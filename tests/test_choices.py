from ape_trezor.choices import AddressPromptChoice
from ape_trezor.hdpath import HDBasePath


def test_get_user_selected_account(mocker, mock_client, address):
    mock_prompt = mocker.patch("ape_trezor.choices.click.prompt")
    choices = AddressPromptChoice(mock_client, HDBasePath())
    choices._choice_index = 1

    # `None` means the user hasn't selected yeet
    # And is entering other keys, possible the paging keys.
    mock_prompt_return_values = iter((None, None, None, None, address, None))

    def _side_effect(*args, **kwargs):
        return next(mock_prompt_return_values)

    mock_prompt.side_effect = _side_effect
    selected_address, hdpath = choices.get_user_selected_account()
    assert selected_address == address
    assert str(hdpath) == "m/44'/60'/0'/0/1"
