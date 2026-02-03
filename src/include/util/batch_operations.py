"""Utilities for batch operations on files and directories."""

import asyncio
import os
from typing import AsyncIterator, Optional

from include.classes.shared import AppShared
from include.classes.exceptions.request import InvalidResponseError
from include.util.requests import do_request, do_request_2
from include.util.transfer import download_file_from_server
from include.util.connect import get_connection

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


async def batch_delete_items(
    app_shared: AppShared,
    file_ids: list[str],
    directory_ids: list[str],
) -> AsyncIterator[tuple[str, str, bool, Optional[str]]]:
    """
    Delete multiple files and directories.
    
    Yields progress updates for each item deleted.
    
    Args:
        app_shared: Shared application state
        file_ids: List of file IDs to delete
        directory_ids: List of directory IDs to delete
        
    Yields:
        Tuples of (item_type, item_id, success, error_message)
        - item_type: "file" or "directory"
        - item_id: ID of the item being deleted
        - success: True if deletion succeeded, False otherwise
        - error_message: Error message if deletion failed, None otherwise
    """
    # Delete files first
    for file_id in file_ids:
        try:
            response = await do_request(
                action="delete_document",
                data={"document_id": file_id},
                username=app_shared.username,
                token=app_shared.token,
            )
            
            if response.get("code") == 200:
                yield ("file", file_id, True, None)
            else:
                error_msg = _("({code}) {message}").format(
                    code=response.get("code"),
                    message=response.get("message", "Unknown error")
                )
                yield ("file", file_id, False, error_msg)
                
        except Exception as e:
            yield ("file", file_id, False, str(e))
    
    # Delete directories
    for dir_id in directory_ids:
        try:
            response = await do_request(
                action="delete_directory",
                data={"folder_id": dir_id},
                username=app_shared.username,
                token=app_shared.token,
            )
            
            if response.get("code") == 200:
                yield ("directory", dir_id, True, None)
            else:
                error_msg = _("({code}) {message}").format(
                    code=response.get("code"),
                    message=response.get("message", "Unknown error")
                )
                yield ("directory", dir_id, False, error_msg)
                
        except Exception as e:
            yield ("directory", dir_id, False, str(e))


async def batch_download_items(
    app_shared: AppShared,
    file_items: list[dict],
    directory_items: list[dict],
    save_root_path: str,
) -> AsyncIterator[tuple[str, str, str, bool, Optional[str]]]:
    """
    Download multiple files and directories with structure preservation.
    
    Args:
        app_shared: Shared application state
        file_items: List of file dicts with keys: id, title
        directory_items: List of directory dicts with keys: id, name
        save_root_path: Root directory where files should be saved
        
    Yields:
        Tuples of (item_type, item_name, current_file, success, error_message)
        - item_type: "file" or "directory"
        - item_name: Name of the file/directory being processed
        - current_file: Current file being downloaded (for progress display)
        - success: True if download succeeded, False otherwise
        - error_message: Error message if download failed, None otherwise
    """
    
    async def download_file(file_id: str, filename: str, save_path: str) -> tuple[bool, Optional[str]]:
        """
        Download a single file from the server.
        
        Args:
            file_id: Server ID of the file to download
            filename: Name of the file (used for error messages)
            save_path: Local path where the file should be saved
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            - success: True if download succeeded, False otherwise
            - error_message: Error description if failed, None otherwise
        """
        try:
            # Create download task
            response = await do_request(
                action="download_document",
                data={"document_id": file_id},
                username=app_shared.username,
                token=app_shared.token,
            )
            
            if response.get("code") != 200:
                error_msg = _("({code}) {message}").format(
                    code=response.get("code"),
                    message=response.get("message", "Unknown error")
                )
                return (False, error_msg)
            
            task_id = response.get("data", {}).get("task_data", {}).get("task_id")
            if not task_id:
                return (False, _("Failed to get download task ID"))
            
            # Download the file
            conn = await get_connection(
                server_address=app_shared.get_not_none_attribute("server_address"),
                disable_ssl_enforcement=app_shared.disable_ssl_enforcement,
                proxy=app_shared.preferences["settings"]["proxy_settings"],
                max_size=1024**2 * 4,
                force_ipv4=app_shared.preferences["settings"].get("force_ipv4", False),
            )
            
            try:
                await download_file_from_server(
                    conn,
                    task_id,
                    save_path,
                )
                return (True, None)
            finally:
                await conn.close()
                
        except Exception as e:
            return (False, str(e))
    
    async def download_directory_recursive(dir_id: str, dir_name: str, parent_path: str):
        """
        Recursively download a directory and all its contents.
        
        Downloads all files in the directory and recursively processes subdirectories,
        maintaining the directory structure locally.
        
        Args:
            dir_id: Server ID of the directory to download
            dir_name: Name of the directory
            parent_path: Local parent path where the directory should be created
            
        Yields:
            Tuples of (item_type, item_name, current_file, success, error_message)
            - item_type: "file" or "directory"
            - item_name: Name of the item being processed
            - current_file: Path being downloaded for progress display
            - success: True if operation succeeded, False otherwise
            - error_message: Error description if failed, None otherwise
        """
        # Create directory
        dir_path = os.path.join(parent_path, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        
        # List directory contents
        try:
            response = await do_request(
                action="list_files",
                data={"directory_id": dir_id},
                username=app_shared.username,
                token=app_shared.token,
            )
            
            if response.get("code") != 200:
                error_msg = _("Failed to list directory: ({code}) {message}").format(
                    code=response.get("code"),
                    message=response.get("message", "Unknown error")
                )
                yield ("directory", dir_name, dir_name, False, error_msg)
                return
            
            data = response.get("data", {})
            files = data.get("files", [])
            subdirs = data.get("directories", [])
            
            # Download all files in this directory
            for file_data in files:
                file_id = file_data["id"]
                filename = file_data["title"]
                file_path = os.path.join(dir_path, filename)
                
                success, error = await download_file(file_id, filename, file_path)
                yield ("file", filename, f"{dir_name}/{filename}", success, error)
            
            # Recursively download subdirectories
            for subdir_data in subdirs:
                subdir_id = subdir_data["id"]
                subdir_name = subdir_data["name"]
                
                async for result in download_directory_recursive(subdir_id, subdir_name, dir_path):
                    yield result
                    
        except Exception as e:
            yield ("directory", dir_name, dir_name, False, str(e))
    
    # Download individual files
    for file_data in file_items:
        file_id = file_data["id"]
        filename = file_data["title"]
        file_path = os.path.join(save_root_path, filename)
        
        success, error = await download_file(file_id, filename, file_path)
        yield ("file", filename, filename, success, error)
    
    # Download directories recursively
    for dir_data in directory_items:
        dir_id = dir_data["id"]
        dir_name = dir_data["name"]
        
        async for result in download_directory_recursive(dir_id, dir_name, save_root_path):
            yield result
