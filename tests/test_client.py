import ape
import pytest
from hexbytes import HexBytes

from ape_trezor.client import TrezorAccountClient, TrezorClient, extract_signature_vrs_bytes
from ape_trezor.hdpath import HDBasePath, HDPath


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
def account_hd_path():
    return HDPath("m/44'/60'/0'/1")


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


CHAIN_ID = 4
TO_ADDRESS = "0xE3747e6341E0d3430e6Ea9e2346cdDCc2F8a4b5b"
GAS_LIMIT = 21000
NONCE = 6
VALUE = 100000000000
MAX_FEE_PER_GAS = 1500000008
MAX_PRIORITY_FEE_PER_GAS = 1500000000
GAS_PRICE = 1
SIG_V = 27
SIG_R = HexBytes("0x8a183a2798a3513133a2f0a5dfdb3f8696034f783e0fb994d69a64a801b07409")
SIG_S = HexBytes("0x6cadc1eb65b05da34d7287c94454efadbcca2952476654f607b9a858847e49bc")


@pytest.fixture
def static_fee_transaction(address):
    return {
        "chainId": CHAIN_ID,
        "to": TO_ADDRESS,
        "from": address,
        "gas": GAS_LIMIT,
        "nonce": NONCE,
        "value": VALUE,
        "gasPrice": GAS_PRICE,
    }


@pytest.fixture
def dynamic_fee_transaction(address):
    return {
        "chainId": CHAIN_ID,
        "to": TO_ADDRESS,
        "from": address,
        "gas": GAS_LIMIT,
        "nonce": NONCE,
        "value": VALUE,
        "type": "0x02",
        "maxFeePerGas": MAX_FEE_PER_GAS,
        "maxPriorityFeePerGas": MAX_PRIORITY_FEE_PER_GAS,
        "accessList": [],
    }


class TestTrezorClient:
    @pytest.fixture
    def client(self, hd_path, mock_device_client):
        return TrezorClient(hd_path, client=mock_device_client)

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
    assert v == SIG_V
    assert r == SIG_R
    assert s == SIG_S


class TestTrezorAccountClient:
    @pytest.fixture
    def account_client(self, address, account_hd_path, mock_device_client):
        return TrezorAccountClient(address, account_hd_path, client=mock_device_client)

    def test_sign_static_fee_transaction(
        self,
        mocker,
        account_client,
        static_fee_transaction,
        mock_device_client,
        account_hd_path,
    ):
        sign_eip1559_patch = mocker.patch("ape_trezor.client.sign_tx")
        sign_eip1559_patch.return_value = (SIG_V, SIG_R, SIG_S)
        actual = account_client.sign_transaction(static_fee_transaction)
        assert actual == (SIG_V, SIG_R, SIG_S)
        sign_eip1559_patch.assert_called_once_with(
            mock_device_client,
            account_hd_path.address_n,
            nonce=NONCE,
            gas_price=GAS_PRICE,
            gas_limit=GAS_LIMIT,
            to=TO_ADDRESS,
            value=VALUE,
            data=b"",
            chain_id=CHAIN_ID,
        )

    def test_sign_dynamic_fee_transaction(
        self,
        mocker,
        account_client,
        dynamic_fee_transaction,
        mock_device_client,
        account_hd_path,
    ):
        sign_eip1559_patch = mocker.patch("ape_trezor.client.sign_tx_eip1559")
        sign_eip1559_patch.return_value = (SIG_V, SIG_R, SIG_S)
        actual = account_client.sign_transaction(dynamic_fee_transaction)
        assert actual == (SIG_V, SIG_R, SIG_S)
        sign_eip1559_patch.assert_called_once_with(
            mock_device_client,
            account_hd_path.address_n,
            nonce=NONCE,
            gas_limit=GAS_LIMIT,
            to=TO_ADDRESS,
            value=VALUE,
            data=b"",
            chain_id=CHAIN_ID,
            max_gas_fee=MAX_FEE_PER_GAS,
            max_priority_fee=MAX_PRIORITY_FEE_PER_GAS,
            access_list=[],
        )
