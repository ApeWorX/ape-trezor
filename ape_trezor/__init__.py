from ape import plugins

from .accounts import AccountContainer, TrezorAccount, TrezorConfig


@plugins.register(plugins.Config)
def config_class():
    return TrezorConfig


@plugins.register(plugins.AccountPlugin)
def account_types():
    return AccountContainer, TrezorAccount
