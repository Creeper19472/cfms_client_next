from typing import Optional

from include.classes.response import Response

__all__ = [
    "RequestFailureError",
    "CreateDirectoryFailureError",
    "InvalidResponseError",
]


class RequestFailureError(Exception):
    """Exception raised when a request to the server fails."""
    
    def __init__(self, msg: str = "", response: Optional[dict] = None, *args) -> None:
        super().__init__(*args)
        self._msg = msg
        self.response: Optional[dict] = response

    def __str__(self) -> str:
        return self._msg or "Request failed"


class CreateDirectoryFailureError(RequestFailureError):
    """Exception raised when directory creation fails."""
    
    def __init__(self, name: str, msg: str, *args) -> None:
        super().__init__(msg, *args)
        self.name = name
        self._err_msg = f"Failed to create directory '{name}': {msg}"
    
    def __str__(self) -> str:
        return self._err_msg


class InvalidResponseError(Exception):
    """Exception raised when an invalid response is received from the server."""
    
    def __init__(
        self, response: Response, msg: str = "", *args
    ) -> None:
        super().__init__(*args)
        self.msg = msg or "Invalid response from server"
        self.response = response

    def __str__(self) -> str:
        return self.msg
