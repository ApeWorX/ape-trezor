# ape-trezor

Ape Trezor is a plugin for [Ape Framework](https://github.com/ApeWorx/ape) which integrates [Trezorlib ethereum.py](https://github.com/trezor/trezor-firmware/blob/master/python/src/trezorlib/ethereum.py) to load and create accounts, sign messages, and sign transactions.

## Dependencies

* [python3](https://www.python.org/downloads) version 3.6 or greater, python3-dev

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

```bash
ape trezor add [PICK AN ALIAS]
```
you can now load the account like any other account in Ape console and then use it to sign transactions.

```bash
ape trezor sign-message [YOUR TREZOR ALIAS] "hello world"
ape trezor verify "hello world"
```
the output of `verify` should be the same address as the account `$account_name`

## Development

This project is in development and should be considered a beta.
Things might not be in their final state and breaking changes may occur.
Comments, questions, criticisms and pull requests are welcomed.

## License

This project is licensed under the [Apache 2.0](LICENSE).
