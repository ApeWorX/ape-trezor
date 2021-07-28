import json
from pathlib import Path
from typing import Iterator, Optional

from ape.api.accounts import AccountAPI, AccountContainerAPI, TransactionAPI
from ape.convert import to_address
from ape.types import AddressType
from eth_account.datastructures import SignedMessage  # type: ignore
from eth_account.messages import SignableMessage, _hash_eip191_message  # type: ignore

from trezorlib import ethereum  # type: ignore
from trezorlib.client import get_default_client  # type: ignore
from trezorlib.tools import parse_path as parse_hdpath  # type: ignore


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
    def hdpath(self) -> str:
        return self.accountfile["hdpath"]

    @property
    def client(self):
        return get_default_client()

    @property
    def address(self) -> AddressType:
        return to_address(self.accountfile["address"])

    def sign_message(self, msg: SignableMessage) -> Optional[SignedMessage]:
        if msg.version != b"E":
            return None
        # TODO: trezor does not support eip712 yet, it only supports eip 191 personal_sign

        signature = ethereum.sign_message(self.client, parse_hdpath(self.hdpath), msg.body)
        messagehash = _hash_eip191_message(msg)
        r = signature["signature"][0:32]
        s = signature["signature"][32:64]
        v = signature["signature"][64]
        return SignedMessage(messagehash, r, s, v, signature["signature"])

    def sign_transaction(self, txn: TransactionAPI) -> Optional[TransactionAPI]:
        # NOTE: Some accounts may not offer signing things
        signature = ethereum.sign_tx(
            self.client,
            parse_hdpath(self.hdpath),
            txn.nonce,
            txn.gas_price,
            txn.gas_limit,
            txn.receiver,
            txn.value,
            txn.data,
            txn.chain_id,
            # tx_type,
        )
        txn.signature = signature
        return txn
