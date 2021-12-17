from ape.exceptions import AccountsError


class TrezorAccountException(AccountsError):
    """
    An error that occurs in the ape Trezor plugin.
    """


class TrezorSigningError(TrezorAccountException):
    """
    An error that occurs when signing a message or transaction
    using the Trezor plugin.
    """


class TrezorUsbError(TrezorAccountException):
    def __init__(self, message, status=0):
        self.status = status
        super().__init__(message)


class TrezorTimeoutError(TrezorUsbError):
    """
    Raised when the Trezor client times-out waiting for a response from the device.
    """

    def __init__(self, timeout):
        message = (
            f"Timeout waiting device response (timeout={timeout}).\n"
            f"Make sure the Trezor device is not busy with another task."
        )
        super().__init__(message)
