"""Utilities for batch operations on files and directories."""

import asyncio
import os
from typing import AsyncIterator, Optional, cast

from include.classes.shared import AppShared
from include.classes.services.download import DownloadManagerService
from include.util.requests import do_request

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
                    message=response.get("message", "Unknown error"),
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
                    message=response.get("message", "Unknown error"),
                )
                yield ("directory", dir_id, False, error_msg)

        except Exception as e:
            yield ("directory", dir_id, False, str(e))


async def batch_download_items(
    app_shared: AppShared,
    file_items: list[dict],
    directory_items: list[dict],
    save_root_path: str,
    cancel_event: Optional[asyncio.Event] = None,
) -> AsyncIterator[tuple[str, str, str, bool, Optional[str]]]:
    """
    Add multiple files and directories to the download queue with structure preservation.

    Uses the DownloadManagerService to queue downloads. The actual downloads happen
    asynchronously in the background via the download service. This function only
    adds tasks to the queue and reports success/failure of the queueing operation.

    Args:
        app_shared: Shared application state
        file_items: List of file dicts with keys: id, title
        directory_items: List of directory dicts with keys: id, name
        save_root_path: Root directory where files should be saved
        cancel_event: Optional asyncio.Event to signal cancellation

    Yields:
        Tuples of (item_type, item_name, current_file, success, error_message)
        - item_type: "file" or "directory"
        - item_name: Name of the file/directory being processed
        - current_file: Current file being added to queue (for progress display)
        - success: True if task was added to queue, False otherwise
        - error_message: Error message if adding to queue failed, None otherwise
    """

    # Get the download manager service
    download_service = None
    if app_shared.service_manager:
        download_service = cast(
            DownloadManagerService,
            app_shared.service_manager.get_service("download_manager"),
        )

    if not download_service:
        # If download service is not available, fail immediately
        for file_data in file_items:
            yield ("file", file_data["title"], file_data["title"], False, _("Download manager service not available"))
        for dir_data in directory_items:
            yield ("directory", dir_data["name"], dir_data["name"], False, _("Download manager service not available"))
        return

    async def download_file(
        file_id: str, filename: str, save_path: str, download_service: DownloadManagerService
    ) -> tuple[bool, Optional[str]]:
        """
        Add a file to the download queue using the DownloadManagerService.

        This function requests a download task from the server and adds it to the
        download manager queue. The actual download happens asynchronously in the
        background via the download service.

        Args:
            file_id: Server ID of the file to download
            filename: Name of the file (used for error messages)
            save_path: Local path where the file should be saved
            download_service: DownloadManagerService instance to use for downloading

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            - success: True if task was successfully added to queue, False otherwise
            - error_message: Error description if failed, None otherwise
        """
        try:
            # Request download task from server
            response = await do_request(
                action="get_document",
                data={"document_id": file_id},
                username=app_shared.username,
                token=app_shared.token,
            )

            if response.get("code") != 200:
                error_msg = _("({code}) {message}").format(
                    code=response.get("code"),
                    message=response.get("message", "Unknown error"),
                )
                return (False, error_msg)

            task_data = response.get("data", {}).get("task_data", {})
            task_id = task_data.get("task_id")
            if not task_id:
                return (False, _("Failed to get download task ID"))

            # Check if server supports resume
            supports_resume = task_data.get("supports_resume", False)

            # Add task to download manager - it will be downloaded in the background
            download_service.add_task(
                task_id=task_id,
                file_id=file_id,
                filename=filename,
                file_path=save_path,
                priority=10,  # High priority for batch downloads
                supports_resume=supports_resume,
            )

            # Return success immediately - download happens in background
            return (True, None)

        except Exception as e:
            return (False, str(e))

    async def download_directory_recursive(
        dir_id: str, dir_name: str, parent_path: str, download_service: DownloadManagerService
    ):
        """
        Recursively add all files in a directory to the download queue.

        Traverses the directory structure and adds all files to the download queue,
        maintaining the directory structure locally. The actual downloads happen
        asynchronously in the background via the download service.

        Args:
            dir_id: Server ID of the directory to download
            dir_name: Name of the directory
            parent_path: Local parent path where the directory should be created
            download_service: DownloadManagerService instance to use for downloading

        Yields:
            Tuples of (item_type, item_name, current_file, success, error_message)
            - item_type: "file" or "directory"
            - item_name: Name of the item being processed
            - current_file: Path being added to queue for progress display
            - success: True if task was added to queue, False otherwise
            - error_message: Error description if failed, None otherwise
        """
        # Check for cancellation
        if cancel_event and cancel_event.is_set():
            return
            
        # Create directory
        dir_path = os.path.join(parent_path, dir_name)
        os.makedirs(dir_path, exist_ok=True)

        # List directory contents
        try:
            response = await do_request(
                action="list_directory",
                data={"folder_id": dir_id},
                username=app_shared.username,
                token=app_shared.token,
            )

            if response.get("code") != 200:
                error_msg = _("Failed to list directory: ({code}) {message}").format(
                    code=response.get("code"),
                    message=response.get("message", "Unknown error"),
                )
                yield ("directory", dir_name, dir_name, False, error_msg)
                return

            data = response.get("data", {})
            files = data.get("documents", [])  # API returns "documents", not "files"
            subdirs = data.get("folders", [])  # API returns "folders", not "directories"

            # Download all files in this directory
            for file_data in files:
                # Check for cancellation before each file
                if cancel_event and cancel_event.is_set():
                    return
                    
                file_id = file_data["id"]
                filename = file_data["title"]
                file_path = os.path.join(dir_path, filename)

                success, error = await download_file(file_id, filename, file_path, download_service)
                yield ("file", filename, f"{dir_name}/{filename}", success, error)

            # Recursively download subdirectories
            for subdir_data in subdirs:
                # Check for cancellation before each subdirectory
                if cancel_event and cancel_event.is_set():
                    return
                    
                subdir_id = subdir_data["id"]
                subdir_name = subdir_data["name"]

                async for result in download_directory_recursive(
                    subdir_id, subdir_name, dir_path, download_service
                ):
                    yield result

        except Exception as e:
            yield ("directory", dir_name, dir_name, False, str(e))

    # Download individual files
    for file_data in file_items:
        # Check for cancellation before each file
        if cancel_event and cancel_event.is_set():
            return
            
        file_id = file_data["id"]
        filename = file_data["title"]
        file_path = os.path.join(save_root_path, filename)

        success, error = await download_file(file_id, filename, file_path, download_service)
        yield ("file", filename, filename, success, error)

    # Download directories recursively
    for dir_data in directory_items:
        # Check for cancellation before each directory
        if cancel_event and cancel_event.is_set():
            return
            
        dir_id = dir_data["id"]
        dir_name = dir_data["name"]

        async for result in download_directory_recursive(
            dir_id, dir_name, save_root_path, download_service
        ):
            yield result
