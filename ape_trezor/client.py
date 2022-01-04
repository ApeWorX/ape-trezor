from typing import Any, Dict

from eth_typing.evm import ChecksumAddress
from pydantic import BaseModel
from trezorlib import ethereum  # type: ignore
from trezorlib.client import get_default_client  # type: ignore
from trezorlib.exceptions import PinException, TrezorFailure  # type: ignore
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
            self._client = get_default_client()
        except TransportException:
            raise TrezorClientConnectionError()
        # Handles an unhandled usb exception in Trezor transport
        except Exception as exc:
            raise TrezorClientError(f"Error: {exc}")

        self._hd_root_path = hd_root_path

    def get_account_path(self, account_id: int) -> str:
        account_path = str(self._hd_root_path.get_account_path(account_id))
        try:
            return ethereum.get_address(self._client, parse_hdpath(account_path))
        except (PinException, TrezorFailure) as exc:
            message = "You have entered an invalid PIN."
            raise TrezorAccountException(message) from exc


class TrezorSignature(BaseModel):
    """
    Class representing a Trezor Signature
    """

    v: int
    r: bytes
    s: bytes

    def __init__(self, **data: Any) -> None:
        """
        Pass `v`: int, `r`: bytes, and  `s`: bytes fields directly
        or an array of bytes as `signature_bytes` to be broken into 3 chunks
        vrs, where `v` is 1 byte, `r` is 32 bytes, and `s` is 32 bytes.
        """
        if "signature_bytes" in data:
            signature_bytes = data.pop("signature_bytes")

            if signature_bytes is None:
                raise TrezorClientError("No data in signature bytes.")

            data["v"] = signature_bytes[0]  # 1 byte
            data["r"] = signature_bytes[1:33]  # 32 bytes
            data["s"] = signature_bytes[33:65]  # 32 bytes

        super().__init__(**data)


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
            self._client = get_default_client()
        except TransportException:
            raise TrezorClientConnectionError()

        self._address = address
        self._account_hd_path = account_hd_path

    def __str__(self):
        return self._address

    @property
    def address(self) -> str:
        return self._address

    def sign_personal_message(self, message: bytes) -> TrezorSignature:
        """
        Sign an Ethereum message only following the EIP 191 specification and
        using your Trezor device. You will need to follow the prompts on the device
        to validate the message data.
        """
        ethereum_message_signature = ethereum.sign_message(
            self._client, parse_hdpath(self._account_hd_path.path), message
        )

        return TrezorSignature(signature_bytes=ethereum_message_signature.signature)

    def sign_typed_data(self, domain_hash: bytes, message_hash: bytes) -> TrezorSignature:
        """
        Sign an Ethereum message following the EIP 712 specification.
        """
        ethereum_typed_data_signature = ethereum.sign_typed_data_hash(
            self._client, parse_hdpath(self._account_hd_path.path), domain_hash, message_hash
        )

        return TrezorSignature(signature_bytes=ethereum_typed_data_signature.signature)

    def sign_transaction(self, txn: Dict[Any, Any]) -> TrezorSignature:
        # Unexpected keyword type
        txn.pop("type")

        tuple_reply = ethereum.sign_tx(
            self._client, parse_hdpath(self._account_hd_path.path), **txn
        )

        return TrezorSignature(
            v=tuple_reply[0],
            r=tuple_reply[1],
            s=tuple_reply[2],
        )


__all__ = [
    "TrezorClient",
    "TrezorAccountClient",
    "TrezorSignature",
]
