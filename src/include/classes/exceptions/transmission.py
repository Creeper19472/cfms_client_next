class FileTransmissionException(Exception): ...


class FileSizeMismatchError(FileTransmissionException):
    def __init__(self, expected: int, got: int, *args) -> None:
        super().__init__(*args)
        self.expected = expected
        self.got = got

    def __str__(self) -> str:
        return f"Expected {self.expected}, got {self.got}"


class FileHashMismatchError(FileTransmissionException):
    def __init__(self, expected: str, got: str, *args) -> None:
        super().__init__(*args)
        self.expected = expected
        self.got = got

    def __str__(self) -> str:
        return f"Expected {self.expected}, got {self.got}"
