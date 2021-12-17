from typing import List

import click
from ape import accounts
from ape.cli import (
    ape_cli_context,
    existing_alias_argument,
    non_existing_alias_argument,
    skip_confirmation_option,
)
from eth_account import Account
from eth_account.messages import encode_defunct

from ape_trezor.accounts import TrezorAccount
from ape_trezor.choices import AddressPromptChoice
from ape_trezor.client import TrezorClient
from ape_trezor.hdpath import HDBasePath


@click.group(short_help="Manage Trezor accounts")
def cli():
    """
    Command-line helper for managing Trezor hardware device accounts.
    You can add accounts using the `add` command.
    """


@cli.command("list")
@ape_cli_context()
def list(cli_ctx):
    """List the Trezor accounts in your ape configuration"""

    trezor_accounts = _get_trezor_accounts()

    if len(trezor_accounts) == 0:
        cli_ctx.logger.warning("No accounts found.")
        return

    num_accounts = len(accounts)
    header = f"Found {num_accounts} account"
    header += "s:" if num_accounts > 1 else ":"
    click.echo(header)

    for account in trezor_accounts:
        alias_display = f" (alias: '{account.alias}')" if account.alias else ""
        hd_path_display = f" (hd-path: '{account.hdpath}')" if account.hdpath else ""
        click.echo(f"  {account.address}{alias_display}{hd_path_display}")


def _get_trezor_accounts() -> List[TrezorAccount]:
    return [a for a in accounts if isinstance(a, TrezorAccount)]


@cli.command()
@ape_cli_context()
@non_existing_alias_argument()
@click.option(
    "--hd-path",
    help=(
        f"The Ethereum account derivation path prefix. "
        f"Defaults to {HDBasePath.DEFAULT} where {{x}} is the account ID. "
        "Exclude {x} to append the account ID to the end of the base path."
    ),
    callback=lambda ctx, param, arg: HDBasePath(arg),
)
def add(cli_ctx, alias, hd_path):
    """Add a account from your Trezor hardware wallet"""
    client = TrezorClient(hd_path)
    choices = AddressPromptChoice(client, hd_path)
    address, account_hd_path = choices.get_user_selected_account()
    container = accounts.containers.get("trezor")
    container.save_account(alias, address, str(account_hd_path))
    cli_ctx.logger.success(f"Account '{address}' successfully added with alias '{alias}'.")


@cli.command()
@ape_cli_context()
@existing_alias_argument(account_type=TrezorAccount)
def delete(cli_ctx, alias):
    """Remove a Trezor account from your ape configuration"""

    container = accounts.containers.get("trezor")
    container.delete_account(alias)
    cli_ctx.logger.success(f"Account '{alias}' has been removed")


@cli.command()
@ape_cli_context()
@skip_confirmation_option("Don't ask for confirmation when removing all accounts")
def delete_all(cli_ctx, skip_confirmation):
    """Remove all trezor accounts from your ape configuration"""

    container = accounts.containers.get("trezor")
    trezor_accounts = _get_trezor_accounts()
    if len(trezor_accounts) == 0:
        cli_ctx.logger.warning("No accounts found.")
        return

    user_agrees = skip_confirmation or click.confirm("Remove all Trezor accounts from ape?")
    if not user_agrees:
        cli_ctx.logger.info("No account were removed.")
        return

    for account in trezor_accounts:
        container.delete_account(account.alias)
        cli_ctx.logger.success(f"Account '{account.alias}' has been removed")


@cli.command(short_help="Sign a message with your Trezor device")
@click.argument("alias")
@click.argument("message")
@ape_cli_context()
def sign_message(cli_ctx, alias, message):
    if alias not in accounts.aliases:
        cli_ctx.logger.warning(f"Account with alias '{alias}' does not exist")
        return

    eip191message = encode_defunct(text=message)
    account = accounts.load(alias)
    signature = account.sign_message(eip191message)
    signature_bytes = signature.encode_vrs()

    signer = Account.recover_message(eip191message, signature=signature_bytes)
    if signer != account.address:
        cli_ctx.abort(f"Signer resolves incorrectly, got {signer}, expected {account.address}.")

    click.echo(signature.encode_vrs().hex())


@cli.command(short_help="Verify a message with your Trezor device")
@click.argument("message")
@click.argument("signature")
def verify_message(message, signature):
    eip191message = encode_defunct(text=message)
    click.echo(f"signer: {Account.recover_message(eip191message, signature=signature)}")
