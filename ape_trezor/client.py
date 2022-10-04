from typing import Any, Dict, Tuple

from eth_typing.evm import ChecksumAddress
from hexbytes import HexBytes
from trezorlib.client import TrezorClient as LibTrezorClient  # type: ignore
from trezorlib.client import get_default_client  # type: ignore
from trezorlib.ethereum import get_address, sign_message, sign_tx, sign_tx_eip1559  # type: ignore
from trezorlib.exceptions import PinException, TrezorFailure  # type: ignore
from trezorlib.transport import TransportException  # type: ignore

from ape_trezor.exceptions import (
    InvalidHDPathError,
    InvalidPinError,
    TrezorAccountError,
    TrezorClientConnectionError,
    TrezorClientError,
)
from ape_trezor.hdpath import HDBasePath, HDPath


class TrezorClient:
    """
    This class is a client for the Trezor device.
    """

    def __init__(self, hd_root_path: HDBasePath, client: LibTrezorClient = None):
        if not client:
            try:
                self.client = get_default_client()
            except TransportException:
                raise TrezorClientConnectionError()
            # Handles an unhandled usb exception in Trezor transport
            except Exception as exc:
                raise TrezorClientError(f"Error: {exc}")
        else:
            self.client = client

        self._hd_root_path = hd_root_path

    def get_account_path(self, account_id: int) -> str:
        account_path = self._hd_root_path.get_account_path(account_id)
        address = account_path.address
        try:
            message_type = get_address(self.client, address)
            return str(message_type)
        except PinException as err:
            raise InvalidPinError() from err

        except TrezorFailure as err:
            if "forbidden key path" in str(err).lower():
                raise InvalidHDPathError(str(account_path))

            code = 0 if not err.code else err.code.value
            raise TrezorClientError(str(err), status=code) from err


def extract_signature_vrs_bytes(signature_bytes: bytes) -> Tuple[int, bytes, bytes]:
    """
    Breaks `signature_bytes` into 3 chunks vrs, where `v` is 1 byte, `r` is 32
    bytes, and `s` is 32 bytes.
    """
    if signature_bytes is None:
        raise TrezorClientError("No data in signature bytes.")

    return signature_bytes[-1], signature_bytes[:32], signature_bytes[32:64]


class TrezorAccountClient:
    """
    This class represents an account on the Trezor device when you know the full
    account HD path.
    """

    def __init__(
        self,
        address: ChecksumAddress,
        account_hd_path: HDPath,
    ):
        try:
            self.client = get_default_client()
        except TransportException:
            raise TrezorClientConnectionError()

        self._address = address
        self._account_hd_path = account_hd_path

    def __str__(self):
        return self._address

    @property
    def address(self) -> str:
        return self._address

    def sign_personal_message(self, message: bytes) -> Tuple[int, bytes, bytes]:
        """
        Sign an Ethereum message only following the EIP 191 specification and
        using your Trezor device. You will need to follow the prompts on the device
        to validate the message data.
        """
        ethereum_message_signature = sign_message(
            self.client, self._account_hd_path.address, message
        )

        return extract_signature_vrs_bytes(signature_bytes=ethereum_message_signature.signature)

    # TODO: Uncomment when Trezor has released the EIP 712 update
    # def sign_typed_data(self, domain_hash: bytes, message_hash: bytes)
    # -> Tuple[int, bytes, bytes]:
    #     """
    #     Sign an Ethereum message following the EIP 712 specification.
    #     """
    #     ethereum_typed_data_signature = ethereum.sign_typed_data_hash(
    #         self.client, parse_hdpath(self._account_hd_path.path), domain_hash, message_hash
    #     )

    #     return extract_signature_vrs_bytes(
    #       signature_bytes=ethereum_typed_data_signature.signature)

    def sign_transaction(self, txn: Dict[Any, Any]) -> Tuple[int, bytes, bytes]:
        tx_type = txn["type"]

        if tx_type == "0x00":  # Static transaction type
            tuple_reply = sign_tx(
                self.client,
                self._account_hd_path.address,
                nonce=txn["nonce"],
                gas_price=txn["maxFeePerGas"],
                gas_limit=txn["gas"],
                to=txn.get("receiver", ""),
                value=txn["value"],
                data=txn.get("data"),
                chain_id=txn.get("chainId"),
                tx_type=tx_type,
            )
        elif tx_type == "0x02":  # Dynamic transaction type
            data = txn.get("data", b"")
            if isinstance(data, str):
                data = HexBytes(data)

            tuple_reply = sign_tx_eip1559(
                self.client,
                self._account_hd_path.address,
                nonce=txn["nonce"],
                gas_limit=txn["gas"],
                to=txn.get("receiver", ""),
                value=txn["value"],
                data=data,
                chain_id=txn["chainId"],
                max_gas_fee=txn["maxFeePerGas"],
                max_priority_fee=txn["maxPriorityFeePerGas"],
                access_list=txn.get("accessList"),
            )
        else:
            raise TrezorAccountError(f"Message type {tx_type} is not supported.")

        return (
            tuple_reply[0],
            tuple_reply[1],
            tuple_reply[2],
        )


__all__ = [
    "TrezorClient",
    "TrezorAccountClient",
]
