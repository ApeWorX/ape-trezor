import pytest  # type: ignore
import glob
import os


@pytest.fixture
def local_trezor_files():
    return glob.glob("./tests/trezor/*")


