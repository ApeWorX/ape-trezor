import pytest
from ape_ethereum.transactions import DynamicFeeTransaction, StaticFeeTransaction
from eip712.messages import EIP712Message, EIP712Type
from eth_account.messages import encode_defunct


class Person(EIP712Type):
    name: "string"  # type: ignore # noqa: F821
    wallet: "address"  # type: ignore # noqa: F821


class Mail(EIP712Message):
    _chainId_: "uint256" = 1  # type: ignore # noqa: F821
    _name_: "string" = "Ether Mail"  # type: ignore # noqa: F821
    _verifyingContract_: "address" = "0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC"  # type: ignore # noqa: F821 E501
    _version_: "string" = "1"  # type: ignore # noqa: F821
    _salt_: "string" = "123"  # type: ignore # noqa: F821

    sender: Person
    receiver: Person


SENDER = Person("Cow", "0xCD2a3d9F938E13CD947Ec05AbC7FE734Df8DD826")  # type: ignore
RECEIVER = Person("Bob", "0xB0B0b0b0b0b0B000000000000000000000000000")  # type: ignore
TYPED_MESSAGE = Mail(sender=SENDER, receiver=RECEIVER)  # type: ignore


@pytest.fixture
def trezor_account(accounts, address, account_hd_path, mock_client):
    container = accounts.containers["trezor"]
    alias = "trezorplugintests"
    container.save_account(alias, address, account_hd_path.path)

    try:
        account = accounts.load(alias)
        account.account_client = mock_client
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


def test_typed_message(trezor_account, mock_client, constants, address):
    mock_client.sign_typed_message.return_value = (
        constants.SIG_V,
        constants.SIG_R,
        constants.SIG_S,
    )
    actual = trezor_account.sign_message(TYPED_MESSAGE.signable_message)
    assert actual.v == constants.SIG_V
    assert actual.r == constants.SIG_R
    assert actual.s == constants.SIG_S
    mock_client.sign_typed_message.assert_called_once_with(
        TYPED_MESSAGE.header, TYPED_MESSAGE.body
    )


def test_sign_static_fee_transaction(
    trezor_account, static_fee_transaction, mock_client, constants
):
    mock_client.sign_static_fee_transaction.return_value = (
        constants.SIG_V,
        constants.SIG_R,
        constants.SIG_S,
    )
    actual = trezor_account.sign_transaction(static_fee_transaction)
    assert actual.v == constants.SIG_V
    assert actual.r == constants.SIG_R
    assert actual.s == constants.SIG_S
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
    assert actual.v == constants.SIG_V
    assert actual.r == constants.SIG_R
    assert actual.s == constants.SIG_S
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
