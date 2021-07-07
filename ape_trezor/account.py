import json
from pathlib import Path
from typing import Iterator, Optional

import click
from eth_account import Account as EthAccount  # type: ignore
from eth_account.datastructures import SignedMessage  # type: ignore
from eth_account.datastructures import SignedTransaction
from eth_account.messages import SignableMessage  # type: ignore

from trezorlib import ethereum

from ape.api.accounts import AccountAPI, AccountContainerAPI, TransactionAPI
from ape.convert import to_address


class AccountContainer(AccountContainerAPI):
    @property
    def _accountfiles(self) -> Iterator[Path]:
        return self.data_folder.glob("*.json")

    @property
    def aliases(self) -> Iterator[str]:
        for p in self._accountfiles:
            yield p.stem

    def __len__(self) -> int:
        return len([*self._accountfiles])

    def __iter__(self) -> Iterator[AccountAPI]:
        for accountfile in self._accountfiles:
            yield TrezorAccount(self, accountfile)  # type: ignore


class TrezorAccount(AccountAPI):
    _accountfile: Path

    @property
    def alias(self) -> str:
        return self._accountfile.stem

    @property
    def accountfile(self) -> dict:
        return json.loads(self._accountfile.read_text())

    @property
    def address(self) -> str:
        return to_address(self.accountfile["address"])

    def sign_message(self, msg: SignableMessage) -> Optional[SignedMessage]:
        return

    def sign_transaction(self, txn: TransactionAPI) -> Optional[TransactionAPI]:
        # NOTE: Some accounts may not offer signing things
        return txn
