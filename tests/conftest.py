import json
import tempfile
from contextlib import contextmanager
from pathlib import Path
from tempfile import mkdtemp
from typing import Dict, Optional

import ape
import pytest
import yaml
from ape._cli import cli as root_ape_cli
from ape.managers.config import CONFIG_FILE_NAME
from click.testing import CliRunner
from eth_pydantic_types import HexBytes
from eth_typing import HexAddress, HexStr

from ape_trezor import _cli
from ape_trezor.hdpath import HDBasePath, HDPath
from ape_trezor.utils import DEFAULT_ETHEREUM_HD_PATH

ape.config.DATA_FOLDER = Path(mkdtemp()).resolve()

TEST_ADDRESS = HexAddress(HexStr("0x0A78AAAAA2122100000b9046f0A085AB2E111113"))


@pytest.fixture(scope="session")
def accounts():
    return ape.accounts


@pytest.fixture(scope="session")
def config():
    return ape.config


@pytest.fixture(scope="session")
def key_file_data():
    return {"address": "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B", "hdpath": "m/44'/60'/0'/0/0"}


@pytest.fixture(scope="session")
def runner():
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


@pytest.fixture(scope="session")
def cli():
    return _cli.cli


@pytest.fixture(scope="session")
def ape_cli():
    return root_ape_cli


@pytest.fixture(scope="session")
def address():
    return TEST_ADDRESS


@pytest.fixture(scope="session")
def existing_key_file(config, key_file_data):
    trezor_data_folder = config.DATA_FOLDER / "trezor"
    trezor_data_folder.mkdir(exist_ok=True, parents=True)
    (trezor_data_folder / "harambe_lives.json").write_text(json.dumps(key_file_data))


@pytest.fixture
def mock_client(mocker):
    return mocker.MagicMock()


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def hd_path():
    return HDBasePath(DEFAULT_ETHEREUM_HD_PATH)


@pytest.fixture(scope="session")
def account_hd_path():
    return HDPath("m/44'/60'/0'/1")


@pytest.fixture(scope="session")
def temp_config(config):
    @contextmanager
    def func(data: Dict, package_json: Optional[Dict] = None):
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)

            config._cached_configs = {}
            config_file = temp_dir / CONFIG_FILE_NAME
            config_file.touch()
            config_file.write_text(yaml.dump(data))
            config.load(force_reload=True)

            if package_json:
                package_json_file = temp_dir / "package.json"
                package_json_file.write_text(json.dumps(package_json))

            with config.using_project(temp_dir):
                yield temp_dir

            config_file.unlink()
            config._cached_configs = {}

    return func
