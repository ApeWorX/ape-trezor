import json
from pathlib import Path
from typing import Iterator, Optional

from ape.api.accounts import AccountAPI, AccountContainerAPI, TransactionAPI
from ape.types import AddressType, MessageSignature, TransactionSignature
from eth_account.messages import SignableMessage
from hexbytes import HexBytes

from ape_trezor.client import TrezorAccountClient
from ape_trezor.exceptions import TrezorAccountError, TrezorSigningError
from ape_trezor.hdpath import HDPath


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
            yield TrezorAccount(account_file_path=account_file)  # type: ignore

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

    # Optional because it's lazily loaded
    account_client: Optional[TrezorAccountClient] = None

    @property
    def alias(self) -> str:
        return self.account_file_path.stem

    @property
    def address(self) -> AddressType:
        return self.network_manager.ethereum.decode_address(self.account_file["address"])

    @property
    def hdpath(self) -> HDPath:
        raw_path = self.account_file["hdpath"]
        return HDPath(raw_path)

    @property
    def account_file(self) -> dict:
        return json.loads(self.account_file_path.read_text())

    @property
    def client(self) -> TrezorAccountClient:
        if self.account_client is None:
            self.account_client = TrezorAccountClient(self.address, self.hdpath)

        return self.account_client

    def sign_message(self, msg: SignableMessage) -> Optional[MessageSignature]:
        version = msg.version

        if version == b"E":
            signed_msg = self.client.sign_personal_message(msg.body)

        elif version == b"\x01":
            signed_msg = self.client.sign_typed_message(msg.header, msg.body)

        else:
            raise TrezorSigningError(
                f"Unsupported message-signing specification, (version={version!r})"
            )

        return MessageSignature(*signed_msg)  # type: ignore

    def sign_transaction(self, txn: TransactionAPI) -> Optional[TransactionSignature]:
        txn_data = txn.dict()

        if "type" not in txn_data and "gasPrice" in txn_data:
            tx_type = "0x00"

        else:
            tx_type = txn_data.pop("type", "0x00")
            if isinstance(tx_type, int):
                tx_type = HexBytes(tx_type).hex()
            elif isinstance(tx_type, bytes):
                tx_type = HexBytes(tx_type).hex()

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

        if tx_type == "0x00":
            txn_data["gas_price"] = txn_data.pop("gasPrice", 0)
            v, r, s = self.client.sign_static_fee_transaction(**txn_data)
        elif tx_type == "0x02":
            txn_data["max_gas_fee"] = txn_data.pop("maxFeePerGas", 0)
            txn_data["max_priority_fee"] = txn_data.pop("maxPriorityFeePerGas", 0)
            txn_data["access_list"] = txn_data.pop("accessList", [])
            v, r, s = self.client.sign_dynamic_fee_transaction(**txn_data)
        else:
            raise TrezorAccountError(f"Message type {tx_type} is not supported.")

        return TransactionSignature(v=v, r=r, s=s)  # type: ignore
