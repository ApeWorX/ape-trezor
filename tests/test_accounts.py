import pytest
from ape_ethereum.transactions import DynamicFeeTransaction, StaticFeeTransaction
from eth_account.messages import encode_defunct


@pytest.fixture
def trezor_account(mocker, accounts, address, account_hd_path, mock_client):
    container = accounts.containers["trezor"]
    alias = "trezorplugintests"
    container.save_account(alias, address, account_hd_path.path)
    patch = mocker.patch("ape_trezor.accounts._create_client")
    patch.return_value = mock_client

    try:
        account = accounts.load(alias)
        account.__dict__["client"] = mock_client  # In case cached from another test
        assert account.client == mock_client, "Setup failed: mock client not set"
        yield account
    finally:
        container.delete_account(alias)


@pytest.fixture
def base_transaction_values(address, constants):
    return {
        "chainId": constants.CHAIN_ID,
        "data": b"",
        "to": constants.TO_ADDRESS,
        "gas": constants.GAS_LIMIT,
        "nonce": constants.NONCE,
        "value": constants.VALUE,
    }


@pytest.fixture
def static_fee_transaction(base_transaction_values, constants):
    return StaticFeeTransaction(**base_transaction_values, gasPrice=constants.GAS_PRICE)


@pytest.fixture
def dynamic_fee_transaction(base_transaction_values, constants):
    return DynamicFeeTransaction(
        **base_transaction_values,
        maxFeePerGas=constants.MAX_FEE_PER_GAS,
        maxPriorityFeePerGas=constants.MAX_PRIORITY_FEE_PER_GAS,
        accessList=[],
    )


def test_sign_personal_message(trezor_account, mock_client, constants):
    message = encode_defunct(text="Hello Apes")
    mock_client.sign_personal_message.return_value = (
        constants.SIG_V,
        constants.SIG_R,
        constants.SIG_S,
    )
    actual = trezor_account.sign_message(message)
    assert actual.v == constants.SIG_V
    assert actual.r == constants.SIG_R
    assert actual.s == constants.SIG_S
    mock_client.sign_personal_message.assert_called_once_with(b"Hello Apes")


def test_sign_static_fee_transaction(
    trezor_account, static_fee_transaction, mock_client, constants
):
    mock_client.sign_static_fee_transaction.return_value = (
        constants.SIG_V,
        constants.SIG_R,
        constants.SIG_S,
    )
    actual = trezor_account.sign_transaction(static_fee_transaction)
    assert actual.signature.v == constants.SIG_V
    assert actual.signature.r == constants.SIG_R
    assert actual.signature.s == constants.SIG_S
    mock_client.sign_static_fee_transaction.assert_called_once_with(
        chain_id=constants.CHAIN_ID,
        data=b"",
        gas_price=constants.GAS_PRICE,
        gas_limit=constants.GAS_LIMIT,
        to=constants.TO_ADDRESS,
        nonce=constants.NONCE,
        value=constants.VALUE,
    )


def test_sign_dynamic_fee_transaction(
    trezor_account, dynamic_fee_transaction, mock_client, constants
):
    mock_client.sign_dynamic_fee_transaction.return_value = (
        constants.SIG_V,
        constants.SIG_R,
        constants.SIG_S,
    )
    actual = trezor_account.sign_transaction(dynamic_fee_transaction)
    assert actual.signature.v == constants.SIG_V
    assert actual.signature.r == constants.SIG_R
    assert actual.signature.s == constants.SIG_S
    mock_client.sign_dynamic_fee_transaction.assert_called_once_with(
        chain_id=constants.CHAIN_ID,
        data=b"",
        gas_limit=constants.GAS_LIMIT,
        to=constants.TO_ADDRESS,
        nonce=constants.NONCE,
        value=constants.VALUE,
        max_gas_fee=constants.MAX_FEE_PER_GAS,
        max_priority_fee=constants.MAX_PRIORITY_FEE_PER_GAS,
        access_list=[],
    )
