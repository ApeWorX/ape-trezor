import pytest  # type: ignore
import glob
import os


@pytest.fixture
def local_trezor_files():
    return glob.glob("./tests/trezor/*")


@pytest.fixture
def ape_trezor_vitalik():
    return os.getenv("HOME") + "/.ape/trezor/vitalik.json"
