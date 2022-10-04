from ape_trezor.client import TrezorClient
from ape_trezor.hdpath import HDPath


def test_init_client_uses_hd_path(mocker):
    factory_patch = mocker.patch("ape_trezor.client.get_default_client")
    hd_path = HDPath("m/44'/60'/0'/0")
    client = TrezorClient(hd_path)
