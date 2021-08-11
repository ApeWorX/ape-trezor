from ape import plugins

from .accounts import AccountContainer, TrezorAccount


@plugins.register(plugins.AccountPlugin)
def account_types():
    return AccountContainer, TrezorAccount
