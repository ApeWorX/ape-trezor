import json

from ape import config


def test_delete(keyfile, runner, cli):
    trezor_data_folder = config.DATA_FOLDER / "trezor"
    trezor_data_folder.mkdir(exist_ok=True, parents=True)
    (trezor_data_folder / "harambe_lives.json").write_text(json.dumps(keyfile))
    result = runner.invoke(cli, ["delete", "harambe_lives"])
    assert result.exit_code == 0
    assert result.output == "SUCCESS: Account 'harambe_lives' has been removed.\n"
