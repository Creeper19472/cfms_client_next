__all__ = [
    "FileTransmissionException",
    "FileSizeMismatchError",
    "FileHashMismatchError",
]


class FileTransmissionException(Exception):
    """Base exception for file transmission errors."""
    pass


class FileSizeMismatchError(FileTransmissionException):
    """Exception raised when file size doesn't match expected value."""
    
    def __init__(self, expected: int, got: int, *args) -> None:
        super().__init__(*args)
        self.expected = expected
        self.got = got

    def __str__(self) -> str:
        return f"File size mismatch: expected {self.expected} bytes, got {self.got} bytes"


class FileHashMismatchError(FileTransmissionException):
    """Exception raised when file hash doesn't match expected value."""
    
    def __init__(self, expected: str, got: str, *args) -> None:
        super().__init__(*args)
        self.expected = expected
        self.got = got

    def __str__(self) -> str:
        return f"File hash mismatch: expected {self.expected}, got {self.got}"
