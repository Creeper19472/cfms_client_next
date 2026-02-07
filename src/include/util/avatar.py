"""Utilities for managing user avatars."""

import os
from typing import Optional

import aiofiles.os

from include.classes.shared import AppShared
from include.classes.response import Response
from include.constants import FLET_APP_STORAGE_DATA
from include.util.connect import get_connection
from include.util.hash import get_server_hash, get_username_hash
from include.util.requests import do_request_2
from include.util.transfer import receive_file_from_server

__all__ = [
    "get_user_avatar",
    "set_user_avatar",
    "download_avatar_file",
]


async def get_user_avatar(username: str) -> Optional[dict]:
    """
    Get the avatar task data for a specific user.

    Sends a request to the server to retrieve the user's avatar file task data.
    Returns None if the user has no avatar set (404) or if an error occurs.
    
    When status code is 200, the response contains task_data with file task
    information in the same format as get_document, which can be used to
    download the avatar file.
    
    Requires authentication - uses current user's credentials from AppShared.

    Args:
        username: Username to get avatar for

    Returns:
        Dictionary containing task_data, or None if no avatar is set (404) or on error

    Example:
        >>> task_data = await get_user_avatar("john_doe")
        >>> if task_data:
        ...     print(f"Task ID: {task_data.get('task_id')}")
    """
    try:
        app_shared = AppShared()
        response: Response = await do_request_2(
            action="get_user_avatar",
            data={"username": username},
            username=app_shared.username,
            token=app_shared.token,
        )

        if response.code == 200:
            # Server returns task_data with file task information
            task_data = response.data.get("task_data")
            return task_data if task_data else None
        elif response.code == 404:
            # No avatar set for this user
            return None
        else:
            # Other error codes - return None
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
    try:
        app_shared = AppShared()
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


async def download_avatar_file(task_data: dict, username: str, force_download: bool = False) -> Optional[str]:
    """
    Download an avatar file from the server and cache it locally.

    Downloads the avatar file using the existing file transfer mechanism and
    caches it in the avatars directory. If the file already exists in the cache,
    returns the cached path immediately without downloading (unless force_download is True).

    Uses task_data from get_user_avatar response, which contains file task information
    in the same format as get_document. The task_id from this data is used with
    download_file action to fetch the avatar.

    The cache structure is:
    {FLET_APP_STORAGE_DATA}/avatars/{server_address_hash}/{username_hash}

    Args:
        task_data: Dictionary containing task_id and other file task information
        username: Username for cache filename
        force_download: If True, re-download even if cached file exists

    Returns:
        Local file path to the downloaded avatar, or None on error

    Example:
        >>> task_data = await get_user_avatar("john_doe")
        >>> if task_data:
        ...     avatar_path = await download_avatar_file(task_data, "john_doe")
        ...     if avatar_path:
        ...         print(f"Avatar saved to: {avatar_path}")
    """
    app_shared = AppShared()

    try:
        # Extract task_id from task_data
        task_id = task_data.get("task_id")
        if not task_id:
            return None

        # Get server address hash for cache directory
        server_address = app_shared.get_not_none_attribute("server_address")
        server_hash = get_server_hash(server_address)

        # Get username hash
        username_hash = get_username_hash(username)
        
        # Build cache directory path
        avatars_cache_dir = os.path.join(
            FLET_APP_STORAGE_DATA, "avatars", server_hash
        )
        avatar_file_path = os.path.join(avatars_cache_dir, username_hash)

        # Check if avatar is already cached (unless force_download)
        if not force_download and await aiofiles.os.path.exists(avatar_file_path):
            return avatar_file_path

        # Create cache directory if it doesn't exist
        await aiofiles.os.makedirs(avatars_cache_dir, exist_ok=True)

        # Delete old cached file if it exists and we're forcing download
        if force_download and await aiofiles.os.path.exists(avatar_file_path):
            await aiofiles.os.remove(avatar_file_path)

        # Create a new connection for file transfer
        # Use task_id from task_data for download_file action
        transfer_conn = await get_connection(
            server_address=server_address,
            disable_ssl_enforcement=app_shared.disable_ssl_enforcement,
            proxy=app_shared.preferences["settings"]["proxy_settings"],
            max_size=1024**2 * 10,  # 10MB max message size for high-resolution avatars
            force_ipv4=app_shared.preferences["settings"].get("force_ipv4", False),
        )

        try:
            # Download the file using the existing transfer mechanism
            # Use task_id from get_user_avatar response
            # receive_file_from_server yields progress updates (stage, *data)
            # For avatars, we silently consume progress for simplicity
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
