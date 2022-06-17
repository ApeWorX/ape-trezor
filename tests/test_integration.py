def test_list(runner, cli, existing_key_file):
    result = runner.invoke(cli, ["list"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B (alias: 'harambe_lives')" in result.output


def test_main_accounts_list(runner, ape_cli, existing_key_file):
    result = runner.invoke(ape_cli, ["accounts", "list", "--all"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B (alias: 'harambe_lives')" in result.output


def test_delete(runner, cli, existing_key_file):
    result = runner.invoke(cli, ["delete", "harambe_lives"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert result.output == "SUCCESS: Account 'harambe_lives' has been removed.\n"


def test_sign_message_when_account_does_not_exist(runner, cli):
    alias = "__DOES_NOT_EXIST__"
    result = runner.invoke(cli, ["sign-message", alias, "MESSAGE"])
    assert result.exit_code != 0
    assert f"Account with alias '{alias}' does not exist." in result.output
