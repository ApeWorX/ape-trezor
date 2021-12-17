from typing import Optional, Tuple

from ape.api.accounts import TransactionAPI
from ape.types import TransactionSignature
from eth_typing.evm import ChecksumAddress
from trezorlib import ethereum
from trezorlib.client import get_default_client  # type: ignore
from trezorlib.exceptions import PinException
from trezorlib.tools import parse_path as parse_hdpath  # type: ignore
from trezorlib.transport import TransportException

from ape_trezor.exceptions import TrezorAccountException, TrezorUsbError
from ape_trezor.hdpath import HDAccountPath, HDBasePath


class TrezorClient:
    """
    This class is a client for the Trezor device.
    """

    def __init__(self, hd_root_path: HDBasePath):
        try:
            self._client = get_default_client()
        except TransportException as exc:
            message = (
                "Unable to open Trezor device path."
                "Make sure you have your device unlocked via the passcode "
                "and have the Ethereum app open."
            )
            raise TrezorUsbError(message) from exc
        self._hd_root_path = hd_root_path

    def get_account_path(self, account_id: int) -> str:
        try:
            return ethereum.get_address(
                self._client, parse_hdpath(f"{self._hd_root_path}/{account_id}")
            )
        except PinException as exc:
            message = "You have entered an invalid PIN."
            raise TrezorAccountException(message) from exc


def _to_vrs(reply: bytes) -> Tuple[int, bytes, bytes]:
    """
    Breaks a byte message into 3 chunks vrs,
    where `v` is 1 byte, `r` is 32 bytes, and `s` is 32 bytes.
    """
    if not reply:
        raise TrezorUsbError("No data in reply")

    v = reply[0]  # 1 byte
    r = reply[1:33]  # 32 bytes
    s = reply[33:65]  # 32 bytes
    return v, r, s


class TrezorAccountClient:
    """
    This class represents an account on the Trezor device when you know the full
    account HD path.
    """

    def __init__(
        self,
        address: ChecksumAddress,
        account_hd_path: HDAccountPath,
    ):
        try:
            self._client = get_default_client()
        except TransportException as exc:
            message = (
                "Unable to open Trezor device path."
                "Make sure you have your device unlocked via the passcode "
                "and have the Ethereum app open."
            )
            raise TrezorUsbError(message) from exc
        self._address = address
        self._account_hd_path = account_hd_path
        self._path_bytes = b""  # cached calculation

    def __str__(self):
        return self._address

    @property
    def address(self) -> str:
        return self._address

    @property
    def path_bytes(self) -> bytes:
        if self._path_bytes == b"":
            self._path_bytes = self._account_hd_path.as_bytes()

        return self._path_bytes

    def sign_personal_message(self, message_bytes: bytes) -> Optional[Tuple[int, bytes, bytes]]:
        signature = ethereum.sign_message(
            self._client, parse_hdpath(self._account_hd_path.path), message_bytes
        )
        return _to_vrs(signature.signature)

    def sign_transaction(self, txn: TransactionAPI) -> TransactionSignature:
        return ethereum.sign_tx(self._client, **txn)


__all__ = [
    "TrezorClient",
    "TrezorAccountClient",
]
