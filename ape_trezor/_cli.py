import json
from typing import List

import click
from eth_account import Account as EthAccount  # type: ignore
from eth_utils import to_bytes

from trezorlib.client import get_default_client
from trezorlib import ethereum

from ape import accounts
from ape.utils import Abort, notify

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
def add(alias):
    if alias in accounts.aliases:
        notify("ERROR", f"Account with alias '{alias}' already exists")
        return

    path = container.data_folder.joinpath(f"{alias}.json")
    client = get_default_client()

    account_n = None
    index_offset = 0
    while type(account_n) != int:
        options = []
        for index in range(index_offset, index_offset + 10):
            options.append(str(index))
            address = ethereum.get_address(client, index)
            click.echo(f"{address}: {index}")
        options.append("n")
        if index_offset > 0:
            options.append("p")
        account_choice = click.prompt(
            "Please choose the address you would like to add, or type 'n' for the next ten entries (or 'p' for the previous 10)",
            type=click.Choice(options),
        )
        if account_choice == "n":
            index_offset += 10
        elif account_choice == "p":
            index_offset -= 10
        else:
            account_n = int(account_choice)

    address = ethereum.get_address(client, account_n)
    output = {}
    output["account_n"] = account_n
    output["address"] = address
    path.write_text(json.dumps(output))

    notify("SUCCESS", f"A new account '{address}' has been added with the id '{alias}'")


@cli.command(
    short_help="Remove an Trezor account from your Ape configuration. \
    (The account will not be deleted from the Trezor hardware device)"
)
@click.argument("alias")
def delete(alias):
    path = container.data_folder.joinpath(f"{alias}.json")
    try:
        path.unlink()
    except Exception as e:
        raise Abort(f"File does not exist: {path}") from e
