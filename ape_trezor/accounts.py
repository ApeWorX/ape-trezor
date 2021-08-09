import json
from pathlib import Path
from typing import Iterator, Optional

from ape.api.accounts import AccountAPI, AccountContainerAPI, TransactionAPI
from ape.convert import to_address
from ape.types import AddressType, MessageSignature, TransactionSignature, SignableMessage

from trezorlib import ethereum  # type: ignore
from trezorlib.client import get_default_client  # type: ignore
from trezorlib.tools import parse_path as parse_hdpath  # type: ignore
from hexbytes import HexBytes


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

    def sign_message(self, msg: SignableMessage) -> Optional[MessageSignature]:
        if msg.version != b"E":
            return None
        # TODO: trezor does not support eip712 yet, it only supports eip 191 personal_sign
        signature = ethereum.sign_message(self.client, parse_hdpath(self.hdpath), msg.body)
        r = signature.signature[1:33]
        s = signature.signature[33:65]
        v = signature.signature[0]
        return MessageSignature(v, r, s)

    def sign_transaction(self, txn: TransactionAPI) -> TransactionSignature:
        # NOTE: Some accounts may not offer signing things
        vrs = ethereum.sign_tx(
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
        return TransactionSignature(vrs[0], vrs[1], vrs[2])
