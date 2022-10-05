from ape.exceptions import AccountsError


class TrezorAccountError(AccountsError):
    """
    An error that occurs in the ape Trezor plugin.
    """


class InvalidPinError(TrezorAccountError):
    """
    An error raised when you enter the wrong PIN.
    """

    def __init__(self):
        super().__init__("You have entered an invalid PIN.")


class InvalidHDPathError(TrezorAccountError):
    """
    An error raised the given HD-Path is invalid.
    """

    def __init__(self, hd_path: str):
        super().__init__(f"HD-Path '{hd_path}' is invalid.")


class TrezorSigningError(TrezorAccountError):
    """
    An error that occurs when signing a message or transaction
    using the Trezor plugin.
    """


class TrezorClientError(TrezorAccountError):
    def __init__(self, message: str, status: int = 0):
        self.status = status
        super().__init__(message)


class TrezorClientConnectionError(TrezorClientError):
    def __init__(self):
        message = (
            "Unable to open Trezor device path. "
            "Make sure you have your device unlocked via the passcode."
        )
        super().__init__(message)
