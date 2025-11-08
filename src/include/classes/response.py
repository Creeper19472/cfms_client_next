"""Response data class for server communications."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Response:
    """
    Represents a response from the server.
    
    Attributes:
        code: HTTP-like status code
        message: Human-readable message
        data: Response payload data
        timestamp: Unix timestamp of the response
    """
    code: int
    message: str
    data: dict[str, Any]
    timestamp: float