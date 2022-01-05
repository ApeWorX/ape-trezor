class HDPath:
    """
    A class representing an HD path. This class is the base class
    for both account specific HD paths (:class:`~ape_trezor.hdpath.HDPath`)
    as well as the derivation HD path class :class:`~ape_trezor.hdpath.HDBasePath`.
    """

    def __init__(self, path: str):
        path = path.rstrip("/")
        if not path.startswith("m/"):
            raise ValueError("HD path must begin with m/")

        self.path = path

    def __str__(self):
        return self.path


class HDBasePath(HDPath):
    """
    A derivation HD path useful for creating objects of type
    :class:`~ape_trezor.hdpath.HDPath`.
    """

    def __init__(self, base_path=None):
        base_path = base_path or "m/44'/60'/0'/0"
        base_path = base_path.rstrip("/")
        super().__init__(base_path)

    def get_account_path(self, account_id) -> HDPath:
        return HDPath(f"{self.path}/{account_id}")
