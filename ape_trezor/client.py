from typing import Optional, Tuple

from ape.api.accounts import TransactionAPI
from eth_typing.evm import ChecksumAddress
from trezorlib import ethereum
from trezorlib.client import get_default_client  # type: ignore
from trezorlib.exceptions import PinException, TrezorFailure
from trezorlib.tools import parse_path as parse_hdpath  # type: ignore
from trezorlib.transport import TransportException

from ape_trezor.exceptions import TrezorAccountException, TrezorClientError
from ape_trezor.hdpath import HDBasePath, HDPath


class TrezorClient:
    """
    This class is a client for the Trezor device.
    """

    def __init__(self, hd_root_path: HDBasePath):
        try:
            self._client = get_default_client()
        except TransportException as exc:
            message = (
                "Unable to open Trezor device path. "
                "Make sure you have your device unlocked via the passcode."
            )
            raise TrezorClientError(message) from exc

        self._hd_root_path = hd_root_path

    def get_account_path(self, account_id: int) -> str:
        try:
            return ethereum.get_address(
                self._client, parse_hdpath(f"{self._hd_root_path}/{account_id}")
            )
        except (PinException, TrezorFailure) as exc:
            message = "You have entered an invalid PIN."
            raise TrezorAccountException(message) from exc


def _to_vrs(reply: bytes) -> Tuple[int, bytes, bytes]:
    """
    Breaks a byte message into 3 chunks vrs,
    where `v` is 1 byte, `r` is 32 bytes, and `s` is 32 bytes.
    """
    if not reply:
        raise TrezorClientError("No data in reply.")

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
        account_hd_path: HDPath,
    ):
        try:
            self._client = get_default_client()
        except TransportException as exc:
            message = (
                "Unable to open Trezor device path. "
                "Make sure you have your device unlocked via the passcode."
            )
            raise TrezorClientError(message) from exc

        self._address = address
        self._account_hd_path = account_hd_path

    def __str__(self):
        return self._address

    @property
    def address(self) -> str:
        return self._address

    def sign_personal_message(self, message: bytes) -> Optional[Tuple[int, bytes, bytes]]:
        """
        Sign an Ethereum message only following the EIP 191 specification and
        using your Trezor device. You will need to follow the prompts on the device
        to validate the message data.
        """

        return _to_vrs(
            ethereum.sign_message(
                self._client, parse_hdpath(self._account_hd_path.path), message
            ).signature
        )

    def sign_typed_data(
        self, domain_hash: bytes, message_hash: bytes
    ) -> Optional[Tuple[int, bytes, bytes]]:
        """
        Sign an Ethereum message following the EIP 712 specification.
        """

        return _to_vrs(
            ethereum.sign_typed_data(
                self._client, parse_hdpath(self._account_hd_path), message_hash
            ).signature
        )

    def sign_transaction(self, txn: TransactionAPI) -> Optional[Tuple[int, bytes, bytes]]:
        return ethereum.sign_tx(self._client, parse_hdpath(self._account_hd_path), **txn)


__all__ = [
    "TrezorClient",
    "TrezorAccountClient",
]
