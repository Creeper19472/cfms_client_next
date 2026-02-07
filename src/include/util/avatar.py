"""Utilities for managing user avatars."""

import hashlib
import os
from typing import Optional

import aiofiles.os

from include.classes.shared import AppShared
from include.classes.response import Response
from include.constants import FLET_APP_STORAGE_DATA
from include.util.connect import get_connection
from include.util.requests import do_request_2
from include.util.transfer import receive_file_from_server

__all__ = [
    "get_user_avatar",
    "set_user_avatar",
    "download_avatar_file",
]


async def get_user_avatar(username: str) -> Optional[str]:
    """
    Get the avatar_id for a specific user.

    Sends a request to the server to retrieve the avatar ID for the given username.
    Returns None if the user has no avatar set (empty string response).
    
    Requires authentication - uses current user's credentials from AppShared.

    Args:
        username: Username to get avatar for

    Returns:
        Avatar file ID string, or None if no avatar is set or on error

    Example:
        >>> avatar_id = await get_user_avatar("john_doe")
        >>> if avatar_id:
        ...     print(f"Avatar ID: {avatar_id}")
    """
    app_shared = AppShared()
    
    try:
        response: Response = await do_request_2(
            action="get_user_avatar",
            data={"username": username},
            username=app_shared.username,
            token=app_shared.token,
        )

        if response.code == 200:
            avatar_id = response.data.get("avatar_id", "")
            # Server returns empty string if no avatar is set
            return avatar_id if avatar_id else None
        else:
            # Log error but don't raise - return None to indicate no avatar
            return None

    except Exception:
        # Silently handle exceptions and return None
        return None


async def set_user_avatar(username: str, document_id: str) -> bool:
    """
    Set the avatar for a specific user.

    Sends a request to the server to update the user's avatar to the specified
    document ID. The document must exist and be an image file.
    
    Requires authentication - uses current user's credentials from AppShared.

    Args:
        username: Username to set avatar for
        document_id: Document ID of the image file to use as avatar

    Returns:
        True if avatar was set successfully, False otherwise

    Example:
        >>> success = await set_user_avatar("john_doe", "img_123456")
        >>> if success:
        ...     print("Avatar updated successfully")
    """
    app_shared = AppShared()
    
    try:
        response: Response = await do_request_2(
            action="set_user_avatar",
            data={
                "username": username,
                "document_id": document_id,
            },
            username=app_shared.username,
            token=app_shared.token,
        )

        return response.code == 200

    except Exception:
        # Silently handle exceptions and return False
        return False


async def download_avatar_file(file_id: str, username: str) -> Optional[str]:
    """
    Download an avatar file from the server and cache it locally.

    Downloads the avatar file using the existing file transfer mechanism and
    caches it in the avatars directory. If the file already exists in the cache,
    returns the cached path immediately without downloading.

    The cache structure is:
    {FLET_APP_STORAGE_DATA}/avatars/{server_address_hash}/{username}.png

    Args:
        file_id: Document ID of the avatar file on the server
        username: Username for cache filename (used as {username}.png)

    Returns:
        Local file path to the downloaded avatar, or None on error

    Example:
        >>> avatar_path = await download_avatar_file("img_123456", "john_doe")
        >>> if avatar_path:
        ...     # Display avatar from avatar_path
        ...     print(f"Avatar saved to: {avatar_path}")
    """
    app_shared = AppShared()

    try:
        # Get server address hash for cache directory
        server_address = app_shared.get_not_none_attribute("server_address")
        server_hash = hashlib.sha256(server_address.encode()).hexdigest()[:16]

        # Build cache directory path
        avatars_cache_dir = os.path.join(
            FLET_APP_STORAGE_DATA, "avatars", server_hash
        )
        avatar_file_path = os.path.join(avatars_cache_dir, f"{username}.png")

        # Check if avatar is already cached
        if await aiofiles.os.path.exists(avatar_file_path):
            return avatar_file_path

        # Create cache directory if it doesn't exist
        await aiofiles.os.makedirs(avatars_cache_dir, exist_ok=True)

        # Request download task from server
        response: Response = await do_request_2(
            action="get_document",
            data={"document_id": file_id},
            username=app_shared.username,
            token=app_shared.token,
        )

        if response.code != 200:
            return None

        task_data = response.data.get("task_data", {})
        task_id = task_data.get("task_id")
        if not task_id:
            return None

        # Create a new connection for file transfer
        transfer_conn = await get_connection(
            server_address=server_address,
            disable_ssl_enforcement=app_shared.disable_ssl_enforcement,
            proxy=app_shared.preferences["settings"]["proxy_settings"],
            max_size=1024**2 * 10,  # 10MB max message size for high-resolution avatars
            force_ipv4=app_shared.preferences["settings"].get("force_ipv4", False),
        )

        try:
            # Download the file using the existing transfer mechanism
            # receive_file_from_server yields progress updates (stage, *data)
            # For avatars, we silently consume progress for simplicity
            # Future enhancement: expose progress via optional callback parameter
            async for _ in receive_file_from_server(
                transfer_conn, task_id, avatar_file_path
            ):
                pass  # Progress updates are consumed but not exposed

            # Verify the file was downloaded successfully
            if await aiofiles.os.path.exists(avatar_file_path):
                return avatar_file_path
            else:
                return None

        finally:
            # Always close the transfer connection
            await transfer_conn.close()

    except Exception:
        # Silently handle any exceptions and return None
        # This includes connection errors, file system errors, etc.
        return None
