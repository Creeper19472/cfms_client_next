class RequestFailureError(Exception):
    def __init__(self, msg: str = "", *args) -> None:
        super().__init__(*args)
        self._msg = msg

    def __str__(self) -> str:
        return self._msg


class CreateDirectoryFailureError(RequestFailureError):
    def __init__(self, name, msg, *args) -> None:
        super().__init__(*args)
        self._err_msg = f"Failed to create directory '{name}': {msg}"
