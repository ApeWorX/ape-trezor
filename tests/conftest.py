import json
from pathlib import Path
from tempfile import mkdtemp

import ape
import pytest
from ape._cli import cli as root_ape_cli
from click.testing import CliRunner
from eth_typing import HexAddress, HexStr
from hexbytes import HexBytes

from ape_trezor import _cli
from ape_trezor.hdpath import HDBasePath, HDPath

# NOTE: Ensure that we don't use local paths for these
ape.config.DATA_FOLDER = Path(mkdtemp()).resolve()

TEST_ADDRESS = HexAddress(HexStr("0x0A78AAAAA2122100000b9046f0A085AB2E111113"))


@pytest.fixture
def accounts():
    return ape.accounts


@pytest.fixture
def config():
    return ape.config


@pytest.fixture
def key_file_data():
    return {"address": "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B", "hdpath": "m/44'/60'/0'/0/0"}


@pytest.fixture
def runner():
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


@pytest.fixture
def cli():
    return _cli.cli


@pytest.fixture
def ape_cli():
    return root_ape_cli


@pytest.fixture
def address():
    return TEST_ADDRESS


@pytest.fixture
def existing_key_file(config, key_file_data):
    trezor_data_folder = config.DATA_FOLDER / "trezor"
    trezor_data_folder.mkdir(exist_ok=True, parents=True)
    (trezor_data_folder / "harambe_lives.json").write_text(json.dumps(key_file_data))


@pytest.fixture
def mock_client(mocker):
    return mocker.MagicMock()


@pytest.fixture
def constants():
    class Constants:
        CHAIN_ID = 4
        TO_ADDRESS = "0xE3747e6341E0d3430e6Ea9e2346cdDCc2F8a4b5b"
        GAS_LIMIT = 21000
        NONCE = 6
        VALUE = 100000000000
        MAX_FEE_PER_GAS = 1500000008
        MAX_PRIORITY_FEE_PER_GAS = 1500000000
        GAS_PRICE = 1
        SIG_V = 27
        SIG_R = HexBytes("0x8a183a2798a3513133a2f0a5dfdb3f8696034f783e0fb994d69a64a801b07409")
        SIG_S = HexBytes("0x6cadc1eb65b05da34d7287c94454efadbcca2952476654f607b9a858847e49bc")

    return Constants


@pytest.fixture
def hd_path():
    return HDBasePath("m/44'/60'/0'/0")


@pytest.fixture
def account_hd_path():
    return HDPath("m/44'/60'/0'/1")
