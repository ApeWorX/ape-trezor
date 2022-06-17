import json
from pathlib import Path
from tempfile import mkdtemp

import ape
import pytest
from ape._cli import cli as root_ape_cli
from click.testing import CliRunner
from eth_typing import HexAddress, HexStr

from ape_trezor import _cli

# NOTE: Ensure that we don't use local paths for these
ape.config.DATA_FOLDER = Path(mkdtemp()).resolve()

TEST_ADDRESS = HexAddress(HexStr("0x0A78AAAAA2122100000b9046f0A085AB2E111113"))


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
