"""Exceptions related to local configuration files."""

__all__ = ["CorruptedEncryptedConfigError"]


class CorruptedEncryptedConfigError(Exception):
    """Raised when a local config file is encrypted but cannot be decrypted with the current DEK.

    This typically happens after a server reset clears the user's keyring: the
    client derives a *new* DEK on the next login, but existing local files were
    encrypted with the *old* DEK and are therefore unreadable.

    Attributes:
        file_path: Absolute path to the corrupted file.
    """

    def __init__(self, file_path: str, *args):
        super().__init__(*args or (f"Cannot decrypt configuration file: {file_path}",))
        self.file_path: str = file_path
