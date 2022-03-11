from typing import Any, Dict, Tuple

from eth_typing.evm import ChecksumAddress
from trezorlib import ethereum  # type: ignore
from trezorlib.client import get_default_client  # type: ignore
from trezorlib.exceptions import PinException, TrezorFailure  # type: ignore
from trezorlib.messages import TransactionType  # type: ignore
from trezorlib.tools import parse_path as parse_hdpath  # type: ignore
from trezorlib.transport import TransportException  # type: ignore

from ape_trezor.exceptions import (
    TrezorAccountException,
    TrezorClientConnectionError,
    TrezorClientError,
)
from ape_trezor.hdpath import HDBasePath, HDPath


class TrezorClient:
    """
    This class is a client for the Trezor device.
    """

    def __init__(self, hd_root_path: HDBasePath):
        try:
            self.client = get_default_client()
        except TransportException:
            raise TrezorClientConnectionError()
        # Handles an unhandled usb exception in Trezor transport
        except Exception as exc:
            raise TrezorClientError(f"Error: {exc}")

        self._hd_root_path = hd_root_path

    def get_account_path(self, account_id: int) -> str:
        account_path = str(self._hd_root_path.get_account_path(account_id))
        try:
            return ethereum.get_address(self.client, parse_hdpath(account_path))
        except (PinException, TrezorFailure) as exc:
            message = "You have entered an invalid PIN."
            raise TrezorAccountException(message) from exc


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
        ethereum_message_signature = ethereum.sign_message(
            self.client, parse_hdpath(self._account_hd_path.path), message
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

        if isinstance(tx_type, TransactionType.STATIC):
            tuple_reply = ethereum.sign_tx(
                self.client,
                parse_hdpath(self._account_hd_path.path),
                nonce=txn["nonce"],
                gas_price=txn["gas_price"],
                gas_limit=txn["gas_limit"],
                to=txn["receiver"],
                value=txn["value"],
                data=txn.get("data"),
                chain_id=txn.get("chain_id"),
                tx_type=tx_type,
            )
        elif isinstance(tx_type, TransactionType.DYNAMIC):
            tuple_reply = ethereum.sign_tx_eip1559(
                self.client,
                parse_hdpath(self._account_hd_path.path),
                nonce=txn["nonce"],
                gas_limit=txn["gas_limit"],
                to=txn["receiver"],
                value=txn["value"],
                data=txn.get("data"),
                chain_id=txn["chain_id"],
                max_gas_fee=txn["max_fee"],
                max_priority_fee=txn["max_priority_fee"],
                access_list=txn.get("access_list"),
            )
        else:
            raise TrezorAccountException(f"Message type {tx_type} is not supported.")

        return (
            tuple_reply[0],
            tuple_reply[1],
            tuple_reply[2],
        )


__all__ = [
    "TrezorClient",
    "TrezorAccountClient",
]
