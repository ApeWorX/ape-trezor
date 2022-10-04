import ape
import pytest

from ape_trezor.client import TrezorClient
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


class TestTrezorClient:
    def test_init_creates_client(self, patch_create_default_client, hd_path, mock_device_client):
        client = TrezorClient(hd_path)
        assert patch_create_default_client.call_count == 1
        assert client.client == mock_device_client

    def test_get_account_path(self, client, mock_get_address, address):
        mock_get_address.return_value = address
        actual = client.get_account_path(1)
        assert actual == address
