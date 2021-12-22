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


class TrezorClientError(TrezorAccountException):
    def __init__(self, message, status=0):
        self.status = status
        super().__init__(message)
