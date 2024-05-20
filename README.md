# Quick Start

Ape Trezor is a plugin for [Ape Framework](https://github.com/ApeWorx/ape) which integrates [Trezorlib ethereum.py](https://github.com/trezor/trezor-firmware/blob/master/python/src/trezorlib/ethereum.py) to load and create accounts, sign messages, and sign transactions.

## Dependencies

- [python3](https://www.python.org/downloads) version 3.9 up tp 3.12.

**Note**: USB does not work in WSL2 environments natively and is [not currently supported](https://github.com/microsoft/WSL/issues/5158).

## Installation

### via `pip`

You can install the latest release via [`pip`](https://pypi.org/project/pip/):

```bash
pip install ape-trezor
```

### via `setuptools`

You can clone the repository and use [`setuptools`](https://github.com/pypa/setuptools) for the most up-to-date version:

```bash
git clone https://github.com/ApeWorX/ape-trezor.git
cd ape-trezor
python3 setup.py install
```

## Quick Usage

Trezor accounts have the following capabilities in `ape`:

1. Can sign transactions (both static-fee and EIP-1559 compliant)
2. Can sign messages using the default EIP-191 specification

To use the Trezor plugin, you must have the Trezor USB device connected and unlocked.

**WARNING**: When the Trezor Suite is open, you may face additional connection issues.
It is recommended to not have the Trezor Suite application open while using the plugin.

## Add Accounts

Add accounts using the `add` command:

```bash
ape trezor add <alias>
```

You can also specify the HD Path:

```bash
ape trezor add <alias> --hd-path "m/44'/1'/0'/0"
```

**WARNING**: When using 3rd party wallets, such as this plugin, `trezorlib` discourages signing transactions from the default Ethereum HD Path `m/44'/60'/0'/0`.
Changing the HD-Path in that circumstance will allow fewer warnings from both Ape and the device, as well as improved security.
See https://github.com/trezor/trezor-firmware/issues/1336#issuecomment-720126545 for more information.

```yaml
trezor:
  hd_path: "m/44'/1'/0'/0"
```

## List Accounts

To list just your Trezor accounts in `ape`, do:

```bash
ape trezor list
```

## Remove accounts

You can also remove accounts:

```bash
ape trezor delete <alias>
ape trezor delete-all
```

## Sign Messages

You can sign messages with your accounts:

```bash
ape trezor sign-message <alias> "hello world"
```

## Verify Messages

You can also verify a message with a signature:

```bash
ape trezor verify-message "hello world" <signature>
```

## Development

Please see the [contributing guide](CONTRIBUTING.md) to learn more how to contribute to this project.
Comments, questions, criticisms and pull requests are welcomed.
