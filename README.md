# Quick Start

Ape Trezor is a plugin for [Ape Framework](https://github.com/ApeWorx/ape) which integrates [Trezorlib ethereum.py](https://github.com/trezor/trezor-firmware/blob/master/python/src/trezorlib/ethereum.py) to load and create accounts, sign messages, and sign transactions.

## Dependencies

* [python3](https://www.python.org/downloads) version 3.8 or greater, python3-dev

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

You must have the Trezor USB device connected.

Then, add accounts:

```bash
ape trezor add <alias>
```

Trezor accounts have the following capabilities in `ape`:

1. Can sign transactions
2. Can sign messages using the default EIP-191 specification


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
