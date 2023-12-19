import ape
import pytest
from ape.logging import LogLevel
from eth_pydantic_types import HexBytes
from trezorlib.messages import SafetyCheckLevel

from ape_trezor.client import TrezorAccountClient, TrezorClient, extract_signature_vrs_bytes


@pytest.fixture
def mock_device_client(mocker):
    return mocker.MagicMock()


@pytest.fixture
def patch_create_default_client(mocker, mock_device_client):
    patch = mocker.patch("ape_trezor.client.get_default_client")
    patch.return_value = mock_device_client
    return patch


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


@pytest.fixture(autouse=True)
def apply_settings_patch(mocker):
    return mocker.patch("ape_trezor.client.apply_settings")


@pytest.fixture
def base_transaction_values(address, constants):
    return {
        "chain_id": constants.CHAIN_ID,
        "data": b"",
        "to": constants.TO_ADDRESS,
        "gas_limit": constants.GAS_LIMIT,
        "nonce": constants.NONCE,
        "value": constants.VALUE,
    }


@pytest.fixture
def static_fee_transaction(base_transaction_values, constants):
    return {
        **base_transaction_values,
        "gas_price": constants.GAS_PRICE,
    }


@pytest.fixture
def dynamic_fee_transaction(base_transaction_values, constants):
    return {
        **base_transaction_values,
        "max_gas_fee": constants.MAX_FEE_PER_GAS,
        "max_priority_fee": constants.MAX_PRIORITY_FEE_PER_GAS,
        "access_list": [],
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


def test_extract_signature_vrs_bytes(signature, constants):
    v, r, s = extract_signature_vrs_bytes(signature)
    assert v == constants.SIG_V
    assert r == constants.SIG_R
    assert s == constants.SIG_S


class TestTrezorAccountClient:
    @pytest.fixture
    def account_client(self, address, account_hd_path, mock_device_client):
        return TrezorAccountClient(address, account_hd_path, client=mock_device_client)

    def test_sign_personal_message(
        self, mocker, account_client, account_hd_path, signature, constants
    ):
        patch = mocker.patch("ape_trezor.client.sign_message")
        mock_response = mocker.MagicMock()
        mock_response.signature = signature
        patch.return_value = mock_response
        v, r, s = account_client.sign_personal_message(b"Hello Apes")
        assert v == constants.SIG_V
        assert r == constants.SIG_R
        assert s == constants.SIG_S
        patch.assert_called_once_with(
            account_client.client, account_hd_path.address_n, b"Hello Apes"
        )

    def test_sign_static_fee_transaction(
        self,
        mocker,
        account_client,
        static_fee_transaction,
        mock_device_client,
        account_hd_path,
        constants,
    ):
        sign_eip1559_patch = mocker.patch("ape_trezor.client.sign_tx")
        sign_eip1559_patch.return_value = (constants.SIG_V, constants.SIG_R, constants.SIG_S)
        actual = account_client.sign_static_fee_transaction(**static_fee_transaction)
        assert actual == (constants.SIG_V, constants.SIG_R, constants.SIG_S)
        sign_eip1559_patch.assert_called_once_with(
            mock_device_client,
            account_hd_path.address_n,
            nonce=constants.NONCE,
            gas_price=constants.GAS_PRICE,
            gas_limit=constants.GAS_LIMIT,
            to=constants.TO_ADDRESS,
            value=constants.VALUE,
            data=b"",
            chain_id=constants.CHAIN_ID,
        )

    def test_sign_dynamic_fee_transaction(
        self,
        mocker,
        account_client,
        dynamic_fee_transaction,
        mock_device_client,
        account_hd_path,
        constants,
    ):
        sign_eip1559_patch = mocker.patch("ape_trezor.client.sign_tx_eip1559")
        sign_eip1559_patch.return_value = (constants.SIG_V, constants.SIG_R, constants.SIG_S)
        actual = account_client.sign_dynamic_fee_transaction(**dynamic_fee_transaction)
        assert actual == (constants.SIG_V, constants.SIG_R, constants.SIG_S)
        sign_eip1559_patch.assert_called_once_with(
            mock_device_client,
            account_hd_path.address_n,
            nonce=constants.NONCE,
            gas_limit=constants.GAS_LIMIT,
            to=constants.TO_ADDRESS,
            value=constants.VALUE,
            data=b"",
            chain_id=constants.CHAIN_ID,
            max_gas_fee=constants.MAX_FEE_PER_GAS,
            max_priority_fee=constants.MAX_PRIORITY_FEE_PER_GAS,
            access_list=[],
        )

    def test_sign_transaction_when_default_hd_path(
        self,
        mocker,
        account_client,
        account_hd_path,
        dynamic_fee_transaction,
        apply_settings_patch,
        caplog,
    ):
        sign_eip1559_patch = mocker.patch("ape_trezor.client.sign_tx_eip1559")
        apply_settings_patch = mocker.patch("ape_trezor.client.apply_settings")

        with caplog.at_level(LogLevel.WARNING):
            account_client.sign_dynamic_fee_transaction(**dynamic_fee_transaction)

        assert sign_eip1559_patch.call_count == 1
        assert apply_settings_patch.call_count == 2
        call_args = apply_settings_patch.call_args_list
        assert call_args[0][0][0] == account_client.client
        assert call_args[0][1]["safety_checks"] == SafetyCheckLevel.PromptTemporarily

        assert call_args[1][0][0] == account_client.client
        assert call_args[1][1]["safety_checks"] == SafetyCheckLevel.Strict

        expected_warning = (
            "Using account with default Ethereum HD Path - "
            "switching safety level check to 'PromptTemporarily'. "
            "Please ensure you are only using addresses on the Ethereum ecosystem."
        )
        assert caplog.records[-1].message == expected_warning
