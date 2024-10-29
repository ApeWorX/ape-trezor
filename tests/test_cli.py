import pytest
from ape.logging import LogLevel
from ape.utils import ZERO_ADDRESS

NEW_ACCOUNT_ALIAS = "NEW_ACCOUNT"


@pytest.fixture
def clean(accounts):
    def delete():
        created_account_path = (
            accounts.config_manager.DATA_FOLDER / "trezor" / f"{NEW_ACCOUNT_ALIAS}.json"
        )
        if created_account_path.is_file():
            created_account_path.unlink()

    delete()
    yield
    delete()


@pytest.fixture
def mock_client_factory(mocker):
    return mocker.patch("ape_trezor._cli.create_client")


@pytest.fixture
def mock_client(mocker, mock_client_factory):
    mock_client = mocker.MagicMock()
    mock_client_factory.return_value = mock_client
    return mock_client


def test_add(mock_client, runner, cli, accounts, clean, mock_client_factory, caplog):
    mock_client.get_account_path.return_value = ZERO_ADDRESS

    # The input simulates paging up, paging back down, then selecting the third account.
    with caplog.at_level(LogLevel.WARNING):
        result = runner.invoke(cli, ("add", NEW_ACCOUNT_ALIAS), input="n\np\n2\n")

    assert result.exit_code == 0, result.output
    assert ZERO_ADDRESS in accounts.containers["trezor"]
    assert mock_client_factory.call_args[0][0].path == "m/44'/60'/0'/0"  # Default

    # Ensure warning appears because using default Ethereum HD Path
    log_warning = caplog.records[-1].message
    expected = (
        "Using the default Ethereum HD Path is not recommended for 3rd party wallets. "
        "Please use an alternative HD-Path for a safer integration."
    )
    assert log_warning == expected


def test_add_specify_hd_path(mock_client, runner, cli, clean, mock_client_factory):
    mock_client.get_account_path.return_value = ZERO_ADDRESS
    hd_path = "m/44'/1'/0'/0"
    result = runner.invoke(
        cli, ("add", NEW_ACCOUNT_ALIAS, "--hd-path", hd_path), input="0\n", catch_exceptions=False
    )
    assert result.exit_code == 0, result.output
    assert mock_client_factory.call_args[0][-1].path == hd_path


def test_add_uses_hd_path_from_config(
    mock_client, project, runner, cli, clean, mock_client_factory, accounts
):
    mock_client.get_account_path.return_value = ZERO_ADDRESS
    hd_path = "m/1'/60'/0'/0"
    with project.temp_config(trezor={"hd_path": hd_path}):
        result = runner.invoke(cli, ("add", NEW_ACCOUNT_ALIAS), input="0\n")
        assert result.exit_code == 0, result.output
        assert mock_client_factory.call_args[0][0].path == hd_path

    account = accounts.load(NEW_ACCOUNT_ALIAS)
    assert str(account.hd_path) == "m/1'/60'/0'/0/0"


def test_list(runner, cli, existing_key_file):
    result = runner.invoke(cli, "list", catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B (alias: 'harambe_lives')" in result.output


def test_main_accounts_list(runner, ape_cli, existing_key_file):
    result = runner.invoke(ape_cli, ("accounts", "list", "--all"), catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B (alias: 'harambe_lives')" in result.output


def test_delete(runner, cli, existing_key_file):
    result = runner.invoke(cli, ("delete", "harambe_lives"), catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert "Account 'harambe_lives' has been removed" in result.output


def test_sign_message_when_account_does_not_exist(runner, cli):
    alias = "__DOES_NOT_EXIST__"
    result = runner.invoke(cli, ("sign-message", alias, "MESSAGE"))
    assert result.exit_code != 0
    assert f"Account with alias '{alias}' does not exist." in result.output
