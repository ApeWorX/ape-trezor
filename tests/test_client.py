import ape
import pytest
from hexbytes import HexBytes

from ape_trezor.client import TrezorClient, extract_signature_vrs_bytes
from ape_trezor.hdpath import HDBasePath


@pytest.fixture
def mock_device_client(mocker):
    return mocker.MagicMock()


@pytest.fixture
def patch_create_default_client(mocker, mock_device_client):
    patch = mocker.patch("ape_trezor.client.get_default_client")
    patch.return_value = mock_device_client
    return patch


@pytest.fixture
def hd_path():
    return HDBasePath("m/44'/60'/0'/0")


@pytest.fixture
def client(hd_path, mock_device_client):
    return TrezorClient(hd_path, client=mock_device_client)


@pytest.fixture
def mock_get_address(mocker):
    return mocker.patch("ape_trezor.client.get_address")


@pytest.fixture
def address():
    return ape.accounts.test_accounts[0].address


@pytest.fixture
def signature():
    return HexBytes(
        "0x8a183a2798a3513133a2f0a5dfdb3f8696034f783e0fb994d69a64a801b07409"
        "6cadc1eb65b05da34d7287c94454efadbcca2952476654f607b9a858847e49bc1b"
    )


class TestTrezorClient:
    def test_init_creates_client(self, patch_create_default_client, hd_path, mock_device_client):
        client = TrezorClient(hd_path)
        assert patch_create_default_client.call_count == 1
        assert client.client == mock_device_client

    def test_get_account_path(self, client, mock_get_address, address):
        mock_get_address.return_value = address
        actual = client.get_account_path(1)
        assert actual == address


def test_extract_signature_vrs_bytes(signature):
    v, r, s = extract_signature_vrs_bytes(signature)
    assert v == 27
    assert r == HexBytes("0x8a183a2798a3513133a2f0a5dfdb3f8696034f783e0fb994d69a64a801b07409")
    assert s == HexBytes("0x6cadc1eb65b05da34d7287c94454efadbcca2952476654f607b9a858847e49bc")
