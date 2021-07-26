from ape import plugins

from .account import AccountContainer, TrezorAccount


@plugins.register(plugins.AccountPlugin)
def account_types():
    return AccountContainer, TrezorAccount
