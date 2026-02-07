import hashlib

__all__ = ["get_username_hash", "get_server_hash"]


def get_server_hash(server_address: str) -> str:
    """Generate a hash for the given server address."""
    return hashlib.sha256(server_address.encode()).hexdigest()[:16]


def get_username_hash(username: str) -> str:
    """Generate a hash for the given username."""
    return hashlib.sha256(username.strip().encode()).hexdigest()[:16]
