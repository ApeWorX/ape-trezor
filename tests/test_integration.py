import os
import glob

def test_integration(local_trezor_files):
    assert "vitalik.json" in local_trezor_files[0]
    os.system(f'cp {local_trezor_files[0]} {os.getenv("HOME")}/.ape/trezor/vitalik.json')
    assert os.getenv("HOME") + "/.ape/trezor/vitalik.json" in glob.glob(os.getenv("HOME") + "/.ape/trezor/*")
    os.system('ape trezor delete vitalik')
    assert os.getenv("HOME") + "/.ape/trezor/vitalik.json" not in glob.glob(os.getenv("HOME") + "/.ape/trezor/*")