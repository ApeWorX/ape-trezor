import os
import glob


def test_integration(local_trezor_files, ape_trezor_vitalik):
    assert "vitalik.json" in local_trezor_files[0]
    assert ape_trezor_vitalik not in glob.glob(os.getenv("HOME") + "/.ape/trezor/*")
    os.system(f"cp {local_trezor_files[0]} {ape_trezor_vitalik}")
    assert ape_trezor_vitalik in glob.glob(os.getenv("HOME") + "/.ape/trezor/*")
    os.system("ape trezor delete vitalik")
    assert ape_trezor_vitalik not in glob.glob(os.getenv("HOME") + "/.ape/trezor/*")
