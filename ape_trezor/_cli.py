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
from ape_trezor.exceptions import TrezorSigningError
from ape_trezor.hdpath import HDBasePath


@click.group(short_help="Manage Trezor accounts")
def cli():
    """
    Command-line helper for managing Trezor hardware device accounts.
    """


@cli.command("list")
@ape_cli_context()
def _list(cli_ctx):
    """List your Trezor accounts in ape"""

    trezor_accounts = accounts.get_accounts_by_type(type_=TrezorAccount)
    num_of_accts = len(trezor_accounts)

    if num_of_accts == 0:
        cli_ctx.logger.warning("No Trezor accounts found.")
        return

    header = f"Found {num_of_accts} Trezor account"
    header += "s:" if num_of_accts > 1 else ":"
    click.echo(header)

    for account in trezor_accounts:
        alias_display = f" (alias: '{account.alias}')" if account.alias else ""
        hd_path_display = f" (hd-path: '{account.hdpath}')" if account.hdpath else ""
        click.echo(f"  {account.address}{alias_display}{hd_path_display}")


@cli.command()
@ape_cli_context()
@non_existing_alias_argument()
@click.option(
    "--hd-path",
    help="The Ethereum account derivation path prefix. Defaults to m/44'/60'/0'/0.",
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
    cli_ctx.logger.success(f"Account '{alias}' has been removed.")


@cli.command()
@ape_cli_context()
@skip_confirmation_option("Don't ask for confirmation when removing all accounts")
def delete_all(cli_ctx, skip_confirmation):
    """Remove all trezor accounts from your ape configuration"""

    container = accounts.containers.get("trezor")
    trezor_accounts = accounts.get_accounts_by_type(type_=TrezorAccount)
    if len(trezor_accounts) == 0:
        cli_ctx.logger.warning("No accounts found.")
        return

    user_agrees = skip_confirmation or click.confirm("Remove all Trezor accounts from ape?")
    if not user_agrees:
        cli_ctx.logger.info("No account were removed.")
        return

    for account in trezor_accounts:
        container.delete_account(account.alias)
        cli_ctx.logger.success(f"Account '{account.alias}' has been removed.")


@cli.command(short_help="Sign a message with your Trezor device")
@click.argument("alias")
@click.argument("message")
@ape_cli_context()
def sign_message(cli_ctx, alias, message):

    if alias not in accounts.aliases:
        cli_ctx.abort(f"Account with alias '{alias}' does not exist.")

    eip191_message = encode_defunct(text=message)
    account = accounts.load(alias)
    signature = account.sign_message(eip191_message)
    signature_bytes = signature.encode_rsv()

    # Verify signature
    signer = Account.recover_message(eip191_message, signature=signature_bytes)
    if signer != account.address:
        cli_ctx.abort(f"Signer resolves incorrectly, got {signer}, expected {account.address}.")

    # Message signed successfully, return signature
    click.echo("Signature: " + signature.encode_rsv().hex())


@cli.command(short_help="Verify a message with your Trezor device")
@click.argument("message")
@click.argument("signature")
def verify_message(message, signature):

    eip191message = encode_defunct(text=message)

    try:
        signer_address = Account.recover_message(eip191message, signature=signature)
    except ValueError as exc:
        message = "Message cannot be verified. Check the signature and try again."
        raise TrezorSigningError(message) from exc

    alias = accounts[signer_address].alias if signer_address in accounts else "n/a"

    click.echo(f"Signer: {signer_address}  {alias}")
