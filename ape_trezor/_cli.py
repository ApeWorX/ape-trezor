from typing import TYPE_CHECKING, cast

import click
from ape.cli.arguments import existing_alias_argument, non_existing_alias_argument
from ape.cli.options import ape_cli_context, skip_confirmation_option

from ape_trezor.exceptions import TrezorSigningError
from ape_trezor.utils import DEFAULT_ETHEREUM_HD_PATH

if TYPE_CHECKING:
    from ape.api.accounts import AccountAPI

    from ape_trezor.client import TrezorClient
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

    from ape_trezor.accounts import TrezorAccount

    trezor_accounts = cli_ctx.account_manager.get_accounts_by_type(type_=TrezorAccount)
    num_of_accts = len(trezor_accounts)

    if num_of_accts == 0:
        cli_ctx.logger.warning("No Trezor accounts found.")
        return

    header = f"Found {num_of_accts} Trezor account"
    header += "s:" if num_of_accts > 1 else ":"
    click.echo(header)

    for account in trezor_accounts:
        alias_display = f" (alias: '{account.alias}')" if account.alias else ""
        hd_path_display = f" (hd-path: '{account.hd_path}')" if account.hd_path else ""
        click.echo(f"  {account.address}{alias_display}{hd_path_display}")


def handle_hd_path(ctx, param, value):
    from ape.utils.basemodel import ManagerAccessMixin

    from ape_trezor.accounts import TrezorConfig
    from ape_trezor.hdpath import HDBasePath

    if not value:
        try:
            config = cast(TrezorConfig, ManagerAccessMixin.config_manager.get_config("trezor"))
            value = config.hd_path
        except Exception:
            value = DEFAULT_ETHEREUM_HD_PATH

    return HDBasePath(value)


hd_path_option = click.option(
    "--hd-path",
    help="The Ethereum account derivation path prefix (defaults to config value).",
    callback=handle_hd_path,
)


def create_client(hd_path: "HDBasePath") -> "TrezorClient":
    # NOTE: Abstracted for testing (and --help performance!) reasons.
    from ape_trezor.client import create_client as _create_client

    return _create_client(hd_path)


@cli.command()
@ape_cli_context()
@non_existing_alias_argument()
@hd_path_option
def add(cli_ctx, alias, hd_path):
    """Add a account from your Trezor hardware wallet"""

    if hd_path.path == DEFAULT_ETHEREUM_HD_PATH:
        cli_ctx.logger.warning(
            "Using the default Ethereum HD Path is not recommended for 3rd party wallets. "
            "Please use an alternative HD-Path for a safer integration."
        )

    from ape_trezor.choices import AddressPromptChoice

    client = create_client(hd_path)
    choices = AddressPromptChoice(client, hd_path)
    address, account_hd_path = choices.get_user_selected_account()
    container = cli_ctx.account_manager.containers.get("trezor")
    container.save_account(alias, address, str(account_hd_path))
    cli_ctx.logger.success(f"Account '{address}' successfully added with alias '{alias}'.")


def _filter_accounts(acct: "AccountAPI") -> bool:
    from ape_trezor.accounts import TrezorAccount

    return isinstance(acct, TrezorAccount)


@cli.command()
@ape_cli_context()
@existing_alias_argument(account_type=_filter_accounts)
def delete(cli_ctx, alias):
    """Remove a Trezor account from your ape configuration"""

    container = cli_ctx.account_manager.containers.get("trezor")
    container.delete_account(alias)
    cli_ctx.logger.success(f"Account '{alias}' has been removed.")


@cli.command()
@ape_cli_context()
@skip_confirmation_option("Don't ask for confirmation when removing all accounts")
def delete_all(cli_ctx, skip_confirmation):
    """Remove all trezor accounts from your ape configuration"""
    from ape_trezor.accounts import TrezorAccount

    container = cli_ctx.account_manager.containers.get("trezor")
    trezor_accounts = cli_ctx.account_manager.get_accounts_by_type(type_=TrezorAccount)
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
    from eth_account.account import Account
    from eth_account.messages import encode_defunct

    if alias not in cli_ctx.account_manager.aliases:
        cli_ctx.abort(f"Account with alias '{alias}' does not exist.")

    eip191_message = encode_defunct(text=message)
    account = cli_ctx.account_manager.load(alias)
    signature = account.sign_message(eip191_message)
    signature_bytes = signature.encode_rsv()

    # Verify signature
    signer = Account.recover_message(eip191_message, signature=signature_bytes)
    if signer != account.address:
        cli_ctx.abort(f"Signer resolves incorrectly, got {signer}, expected {account.address}.")

    # Message signed successfully, return signature
    click.echo("Signature: " + signature.encode_rsv().hex())


@cli.command(short_help="Verify a message with your Trezor device")
@ape_cli_context()
@click.argument("message")
@click.argument("signature")
def verify_message(cli_ctx, message, signature):
    from eth_account.account import Account
    from eth_account.messages import encode_defunct

    eip191message = encode_defunct(text=message)

    try:
        signer_address = Account.recover_message(eip191message, signature=signature)
    except ValueError as exc:
        message = "Message cannot be verified. Check the signature and try again."
        raise TrezorSigningError(message) from exc

    alias = (
        cli_ctx.account_manager[signer_address].alias
        if signer_address in cli_ctx.account_manager
        else "n/a"
    )

    click.echo(f"Signer: {signer_address}  {alias}")
