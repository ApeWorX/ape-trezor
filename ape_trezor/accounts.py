import json
from collections.abc import Iterator
from functools import cached_property
from pathlib import Path
from typing import Any, Optional

from ape.api import AccountAPI, AccountContainerAPI, PluginConfig, TransactionAPI
from ape.types import AddressType, MessageSignature, TransactionSignature
from dataclassy import asdict
from eip712 import EIP712Message, EIP712Type
from eth_account.messages import SignableMessage, encode_defunct
from eth_pydantic_types import HexBytes

from ape_trezor.client import TrezorAccountClient
from ape_trezor.exceptions import TrezorAccountError, TrezorSigningError
from ape_trezor.hdpath import HDPath
from ape_trezor.utils import DEFAULT_ETHEREUM_HD_PATH


class TrezorConfig(PluginConfig):
    hd_path: str = DEFAULT_ETHEREUM_HD_PATH


class AccountContainer(AccountContainerAPI):
    @property
    def _account_files(self) -> Iterator[Path]:
        return self.data_folder.glob("*.json")

    @property
    def aliases(self) -> Iterator[str]:
        for p in self._account_files:
            yield p.stem

    def __len__(self) -> int:
        return len([*self._account_files])

    @property
    def accounts(self) -> Iterator[AccountAPI]:
        for account_file in self._account_files:
            yield TrezorAccount(account_file_path=account_file)

    def save_account(self, alias: str, address: str, hd_path: str):
        """
        Save a new Trezor account to your ape configuration.
        """
        account_data = {"address": address, "hdpath": hd_path}
        path = self.data_folder.joinpath(f"{alias}.json")
        path.write_text(json.dumps(account_data))

    def delete_account(self, alias: str):
        path = self.data_folder.joinpath(f"{alias}.json")

        if path.exists():
            path.unlink()


class TrezorAccount(AccountAPI):
    account_file_path: Path

    @property
    def alias(self) -> str:
        return self.account_file_path.stem

    @property
    def address(self) -> AddressType:
        return self.network_manager.ethereum.decode_address(self.account_file["address"])

    @property
    def hd_path(self) -> HDPath:
        raw_path = self.account_file["hdpath"]
        return HDPath(raw_path)

    @property
    def account_file(self) -> dict:
        return json.loads(self.account_file_path.read_text())

    @cached_property
    def client(self) -> TrezorAccountClient:
        return _create_client(self.address, self.hd_path)

    def sign_message(self, msg: Any, **signer_options) -> Optional[MessageSignature]:
        if isinstance(msg, EIP712Message):
            data = _prepare_data_for_hashing(msg._body_)
            signed_msg = self.client.sign_typed_data(data)
        elif isinstance(msg, dict):
            # Raw typed data.
            signed_msg = self.client.sign_typed_data(msg)
        elif isinstance(msg, SignableMessage) and msg.version == b"E":
            signed_msg = self.client.sign_personal_message(msg.body)
        elif isinstance(msg, SignableMessage) and msg.version == b"\x01":
            # Using EIP-712 without eip712 package.
            # TODO: Investigate why doesn't work.
            try:
                signed_msg = self.client.sign_typed_data_hash(msg.header, msg.body)
            except Exception as err:
                raise TrezorAccountError(
                    "Signing typed data hash is not generally not recommended. "
                    f"Try using eip712 package or a raw dict instead.\n{err}"
                ) from err
        elif isinstance(msg, SignableMessage):
            try:
                version_str = msg.version.decode("utf8")
            except Exception:
                try:
                    version_str = HexBytes(msg.version).hex()
                except Exception:
                    version_str = None

            message = "Unable to sign version"
            suffix = f" '{version_str}'" if version_str else ""
            raise TrezorSigningError(f"{message}{suffix}.")

        elif isinstance(msg, str):
            msg = encode_defunct(text=msg)
            signed_msg = self.client.sign_personal_message(msg.body)
        elif isinstance(msg, int):
            msg = encode_defunct(hexstr=HexBytes(msg).hex())
            signed_msg = self.client.sign_personal_message(msg.body)
        elif isinstance(msg, bytes):
            msg = encode_defunct(primitive=msg)
            signed_msg = self.client.sign_personal_message(msg.body)
        else:
            type_str = getattr(type(msg), "__name__", None)
            if not type_str:
                try:
                    type_str = f"{type(msg)}"
                except Exception:
                    type_str = None

            message = "Unknown message type"
            if type_str:
                message = f"{message} {type_str}"

            raise TypeError(message)

        return MessageSignature(*signed_msg)

    def sign_transaction(self, txn: TransactionAPI, **kwargs) -> Optional[TransactionAPI]:
        txn_data = txn.model_dump(mode="json", by_alias=True)

        if "type" not in txn_data and "gasPrice" in txn_data:
            tx_type = HexBytes("0x00")

        else:
            tx_type = txn_data.pop("type", HexBytes("0x00"))
            if isinstance(tx_type, int):
                tx_type = HexBytes(tx_type)
            elif isinstance(tx_type, bytes):
                tx_type = HexBytes(tx_type)

        # NOTE: `trezorlib` expects empty bytes when no data.
        data = txn_data.get("data") or b""
        if isinstance(data, str):
            txn_data["data"] = HexBytes(data)

        # NOTE: When creating contracts, use `""` as `to=` field.
        txn_data["to"] = txn_data.get("to") or ""

        # NOTE: Chain ID is required
        chain_id = txn_data.pop("chainId")
        if not chain_id:
            chain_id = self.provider.chain_id

        txn_data["chain_id"] = chain_id

        # 'from' field not needed
        if "from" in txn_data:
            del txn_data["from"]

        txn_data["gas_limit"] = txn_data.pop("gas", 0)

        if tx_type == HexBytes("0x00"):
            txn_data["gas_price"] = txn_data.pop("gasPrice", 0)
            v, r, s = self.client.sign_static_fee_transaction(**txn_data)
        elif tx_type == HexBytes("0x02"):
            txn_data["max_gas_fee"] = txn_data.pop("maxFeePerGas", 0)
            txn_data["max_priority_fee"] = txn_data.pop("maxPriorityFeePerGas", 0)
            txn_data["access_list"] = txn_data.pop("accessList", [])
            v, r, s = self.client.sign_dynamic_fee_transaction(**txn_data)
        else:
            raise TrezorAccountError(f"Message type {tx_type} is not supported.")

        txn.signature = TransactionSignature(v=v, r=r, s=s)
        return txn


def _prepare_data_for_hashing(data: dict) -> dict:
    # NOTE: Private method copied from eip712 package.
    result: dict = {}

    for key, value in data.items():
        item: Any = value
        if isinstance(value, EIP712Type):
            item = asdict(value)
        elif isinstance(value, dict):
            item = _prepare_data_for_hashing(item)
        elif isinstance(value, bytes):
            item = value.hex()

        result[key] = item

    return result


def _create_client(address: AddressType, hd_path: HDPath):
    # Separated so can be mocked easily in tests.
    return TrezorAccountClient(address, hd_path)
