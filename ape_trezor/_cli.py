from _typeshed import NoneType
import json
from typing import List

import click
from eth_account import Account as EthAccount  # type: ignore
from eth_utils import to_bytes

from trezorlib.client import get_default_client
from trezorlib import ethereum

from ape import accounts
from ape.utils import notify

# NOTE: Must used the instantiated version of `AccountsContainer` in `accounts`
container = accounts.containers["trezor"]

@click.group(short_help="Manage local accounts")
def cli():
    """
    Command-line helper for managing local accounts. You can unlock local accounts from
    scripts or the console using the accounts.load() method.
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
            # address = ethereum.get_address(client, index)
            #click.echo(f"{address}: {index}")
        options.append("next")
        if index_offset > 0:
            options.append("previous")
        account_choice = click.prompt("Please choose the address you would like to add.",type=click.Choice(options))
        if account_choice == "next":
            index_offset += 10
        elif account_choice == "previous":
            index_offset -= 10
        elif type(account_choice) != int:
            account_n = int(account_choice)
        else:
            raise Exception("An invalid option has been selected.")


    address = ethereum.get_address(client, account_n)
    output = {alias:address}
    path.write_text(json.dumps(output))

    notify("SUCCESS", f"A new account '{a.address}' has been added with the id '{alias}'")
