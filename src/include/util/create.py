"""Utility functions for creating resources on the server."""

from typing import Any, Optional

from include.classes.exceptions.request import CreateDirectoryFailureError
from include.util.requests import do_request


async def create_directory(
    parent_id: Optional[str],
    name: str,
    username: str | Any,
    token: str | Any,
    exists_ok: bool = False,
) -> str:
    """
    Create a directory on the server.
    
    Args:
        parent_id: ID of the parent directory, or None for root level
        name: Name of the directory to create
        username: Username for authentication
        token: Authentication token
        exists_ok: If True, don't raise an error if directory already exists
        
    Returns:
        ID of the created (or existing) directory
        
    Raises:
        CreateDirectoryFailureError: If directory creation fails
    """
    mkdir_resp = await do_request(
        "create_directory",
        data={
            "parent_id": parent_id,
            "name": name,
            "exists_ok": exists_ok,
        },
        username=username,
        token=token,
    )

    if mkdir_resp.get("code") != 200:
        raise CreateDirectoryFailureError(
            name, mkdir_resp.get("message", "Unknown error")
        )
    
    return mkdir_resp["data"]["id"]
