import pytest  # type: ignore
from ape import config  # noqa: F401
from click.testing import CliRunner

from ape_trezor import _cli


@pytest.fixture
def keyfile():
    return {"address": "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B", "hdpath": "m/44'/60'/0'/0/0"}


@pytest.fixture
def runner():
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


@pytest.fixture
def cli():
    return _cli.cli
