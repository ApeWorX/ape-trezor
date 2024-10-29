from importlib import import_module
from typing import Any

from ape import plugins


@plugins.register(plugins.Config)
def config_class():
    from .accounts import TrezorConfig

    return TrezorConfig


@plugins.register(plugins.AccountPlugin)
def account_types():
    from .accounts import AccountContainer, TrezorAccount

    return AccountContainer, TrezorAccount


def __getattr__(name: str) -> Any:
    if name in ("AccountContainer", "TrezorAccount", "TrezorConfig"):
        return getattr(import_module("ape_trezor.accounts"), name)

    else:
        raise AttributeError(name)


__all__ = [
    "AccountContainer",
    "TrezorAccount",
    "TrezorConfig",
]
