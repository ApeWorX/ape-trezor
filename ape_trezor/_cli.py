import json

import click  # type: ignore
from ape import accounts
from ape.utils import Abort, notify
from trezorlib import ethereum  # type: ignore
from trezorlib.client import get_default_client  # type: ignore
from trezorlib.tools import parse_path as parse_hdpath  # type: ignore
from eth_account.messages import SignableMessage  # type: ignore

# NOTE: Must used the instantiated version of `AccountsContainer` in `accounts`
container = accounts.containers["trezor"]


@click.group(short_help="Manage Trezor accounts")
def cli():
    """
    Command-line helper for managing Trezor hardware device accounts.
    You can add accounts using the add method.
    """


@cli.command(short_help="Add an account from your Trezor hardware device")
@click.argument("alias")
@click.option("--hdpath", default="m/44'/60'/0'/0")
def add(hdpath, alias):
    if alias in accounts.aliases:
        notify("ERROR", f"Account with alias '{alias}' already exists")
        return

    path = container.data_folder.joinpath(f"{alias}.json")
    try:
        client = get_default_client()
    except Exception as e:
        raise Abort("Trezor device not found. Please connect via USB and unlock!") from e

    notify("INFO", "Please enter passphrase to allow address discovery.")

    account_hdpath = None
    index_offset = 0
    while not account_hdpath:
        options = []
        for index in range(index_offset, index_offset + 10):
            options.append(str(index))
            address = ethereum.get_address(client, parse_hdpath(f"{hdpath}/{index}"))
            click.echo(f"{address}: {index}")
        options.append("n")
        if index_offset > 0:
            options.append("p")
        account_choice = click.prompt(
            "Please choose the address you would like to add, "
            "or type 'n' for the next ten entries (or 'p' for the previous 10)",
            type=click.Choice(options),
        )
        if account_choice == "n":
            index_offset += 10
        elif account_choice == "p":
            index_offset -= 10
        else:
            account_hdpath = f"{hdpath}/{account_choice}"

    address = ethereum.get_address(client, parse_hdpath(account_hdpath))
    path.write_text(
        json.dumps(
            {
                "address": address,
                "hdpath": account_hdpath,
            }
        )
    )

    notify("SUCCESS", f"A new account '{address}' has been added with the id '{alias}'")


@cli.command(
    short_help="Remove an Trezor account from your Ape configuration. \
    (The account will not be deleted from the Trezor hardware device)"
)
@click.argument("alias")
def delete(alias):
    if alias not in container.aliases:
        raise Abort(f"Account with alias '{alias}' does not exist")

    path = container.data_folder.joinpath(f"{alias}.json")
    try:
        path.unlink()
        notify("SUCCESS", f"Account '{alias}' has been removed")
    except Exception as e:
        raise Abort(f"File does not exist: {path}") from e


@cli.command(short_help="Sign a message with your Trezor device")
@click.argument("alias")
@click.argument("message")
def sign_message(alias, message):
    if alias not in accounts.aliases:
        notify("ERROR", f"Account with alias '{alias}' does not exist")
        return

    eip191message = SignableMessage(
        version=b"E",
        header=f"thereum Signed Message:\n{len(message)}".encode("utf8"),
        body=message.encode("utf8"),
    )
    account = accounts.load(alias)
    signature = account.sign_message(eip191message)
    print(signature["signature"].hex())
