from typing import Callable, Tuple

from ape.logging import logger
from eth_typing.evm import ChecksumAddress
from trezorlib.client import TrezorClient as LibTrezorClient  # type: ignore
from trezorlib.client import get_default_client  # type: ignore
from trezorlib.device import apply_settings  # type: ignore
from trezorlib.ethereum import (  # type: ignore
    get_address,
    sign_message,
    sign_tx,
    sign_tx_eip1559,
    sign_typed_data_hash,
)
from trezorlib.exceptions import PinException, TrezorFailure  # type: ignore
from trezorlib.messages import SafetyCheckLevel
from trezorlib.transport import TransportException  # type: ignore

from ape_trezor.exceptions import (
    InvalidHDPathError,
    InvalidPinError,
    TrezorAccountError,
    TrezorClientConnectionError,
    TrezorClientError,
)
from ape_trezor.hdpath import HDBasePath, HDPath
from ape_trezor.utils import DEFAULT_ETHEREUM_HD_PATH


def create_client(hd_path: HDBasePath) -> "TrezorClient":
    return TrezorClient(hd_path)


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
        try:
            message_type = get_address(self.client, account_path.address_n)
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
        self, address: ChecksumAddress, account_hd_path: HDPath, client: LibTrezorClient = None
    ):
        if not client:
            try:
                self.client = get_default_client()
            except TransportException:
                raise TrezorClientConnectionError()
        else:
            self.client = client

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
            self.client, self._account_hd_path.address_n, message
        )
        return extract_signature_vrs_bytes(signature_bytes=ethereum_message_signature.signature)

    def sign_typed_data(self, domain_hash: bytes, message_hash: bytes) -> Tuple[int, bytes, bytes]:
        """
        Sign an Ethereum message following the EIP 712 specification.
        """
        ethereum_typed_data_signature = sign_typed_data_hash(
            self.client, self._account_hd_path.address_n, domain_hash, message_hash
        )
        return extract_signature_vrs_bytes(signature_bytes=ethereum_typed_data_signature.signature)

    def sign_static_fee_transaction(self, **kwargs) -> Tuple[int, bytes, bytes]:
        return self._sign_transaction(sign_tx, **kwargs)

    def sign_dynamic_fee_transaction(self, **kwargs) -> Tuple[int, bytes, bytes]:
        return self._sign_transaction(sign_tx_eip1559, **kwargs)

    def _sign_transaction(self, lib_call: Callable, **kwargs) -> Tuple[int, bytes, bytes]:
        did_change = self._allow_default_ethereum_account_signing()
        try:
            return lib_call(self.client, self._account_hd_path.address_n, **kwargs)

        except TrezorFailure as err:
            forbidden_key_path = "forbidden key path" in str(err).lower()
            if forbidden_key_path:
                key_path = self._account_hd_path.path
                raise TrezorAccountError(f"HD account path '{key_path}' is not permitted.") from err

            raise TrezorAccountError(str(err)) from err

        finally:
            if did_change:
                apply_settings(self.client, safety_checks=SafetyCheckLevel.Strict)

    def _allow_default_ethereum_account_signing(self) -> bool:
        key_path = self._account_hd_path.path
        prefix = DEFAULT_ETHEREUM_HD_PATH[:-2]
        is_default_ethereum_path = key_path.startswith(prefix)
        if not is_default_ethereum_path:
            return False

        logger.warning(
            "Using account with default Ethereum HD Path - "
            "switching safety level check to 'PromptTemporarily'. "
            "Please ensure you are only using addresses on the Ethereum ecosystem."
        )
        apply_settings(self.client, safety_checks=SafetyCheckLevel.PromptTemporarily)
        return True


__all__ = [
    "TrezorClient",
    "TrezorAccountClient",
]
