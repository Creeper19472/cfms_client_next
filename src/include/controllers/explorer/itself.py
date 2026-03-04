from typing import TYPE_CHECKING
import asyncio
import os

from flet import FilePickerFile
import flet as ft
from websockets import ConnectionClosed

from include.classes.exceptions.request import InvalidResponseError
from include.controllers.base import Controller
from include.ui.controls.dialogs.explorer import (
    BatchUploadFileAlertDialog,
    UploadDirectoryAlertDialog,
    FileOverwriteConfirmDialog,
    BatchDeleteConfirmDialog,
    BatchProgressDialog,
    DirectorySelectorDialog,
)
from include.ui.util.choice import normalize_always_choice
from include.ui.util.path import get_directory
from include.util.connect import get_connection
from include.util.create import create_directory
from include.util.tree import build_directory_tree
from include.util.requests import do_request
from include.util.transfer import batch_upload_file_to_server, upload_file_to_server
from include.util.batch_operations import batch_delete_items, batch_download_items, batch_move_items

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileManagerView

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class FileExplorerController(Controller["FileManagerView"]):
    def __init__(self, control: "FileManagerView"):
        super().__init__(control)

    async def action_upload(self, files: list[FilePickerFile]):
        progress_bar = ft.ProgressBar()
        progress_info = ft.Text(
            _("Preparing upload"), text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE
        )
        progress_column = ft.Column(
            controls=[progress_bar, progress_info],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        stop_event = asyncio.Event()

        batch_dialog = BatchUploadFileAlertDialog(progress_column, stop_event)
        if len(files) > 1:
            self.control.page.show_dialog(batch_dialog)
        else:
            self.control.page.overlay.append(progress_column)
            self.control.page.update()

        # Callback for handling file conflicts
        async def on_conflict(
            filename: str, conflict_type: str, conflict_id: str
        ) -> str | None:
            """Handle file conflict by showing a dialog to the user."""
            confirm_dialog = FileOverwriteConfirmDialog(
                filename=filename,
                existing_id=conflict_id,
                is_batch=len(files) > 1,
            )
            self.control.page.show_dialog(confirm_dialog)
            choice = await confirm_dialog.wait_for_choice()
            return choice

        # 使用手动迭代器，这样可以在取下一个元素时捕获异常并 continue
        ait = batch_upload_file_to_server(
            self.app_shared,
            self.control.current_directory_id,
            files,
            on_conflict_callback=on_conflict,
        )

        # set default vars
        index = 0
        filename = ""
        current_size = 0
        file_size = 0
        files_processed = False  # Track if any files were actually processed

        while True:
            try:
                index, filename, current_size, file_size, exc = await ait.__anext__()

            except StopAsyncIteration:
                break

            if isinstance(exc, InvalidResponseError):
                if (code := exc.response.code) == 403:
                    # Show access denied dialog for 403 errors
                    from include.ui.controls.dialogs.explorer import AccessDeniedDialog
                    
                    dialog = AccessDeniedDialog(
                        reason=exc.response.message,
                        operation=_("upload"),
                    )
                    self.control.page.show_dialog(dialog)
                else:
                    errmsg = _("Upload failed: ({code}) {message}").format(
                        code=code, message=exc.response.message
                    )
                    if progress_column not in self.control.page.overlay:
                        _new_error_text = ft.Text(
                            errmsg,
                            text_align=ft.TextAlign.CENTER,
                            # color=ft.Colors.RED,
                        )
                        progress_column.controls.append(_new_error_text)
                    else:
                        self.control.send_error(
                            errmsg,
                        )
                continue

            elif isinstance(exc, Exception):
                _new_error_text = ft.Text(
                    _(
                        'Problem occurred when uploading "{each_file_name}": {exc}'
                    ).format(each_file_name=filename, exc=exc),
                    text_align=ft.TextAlign.CENTER,
                )
                progress_column.controls.append(_new_error_text)
                return

            # Check if file was skipped (indicated by -1, -1)
            if current_size == -1 and file_size == -1:
                # File was skipped, mark as processed but don't update progress bar
                files_processed = True
                continue

            # Mark file as processed
            files_processed = True

            # Update progress bar
            # For empty files (size 0), show as complete
            if file_size == 0:
                # Empty file uploaded successfully
                progress_bar.value = 1.0
                progress_info.value = f"[{index+1}/{len(files)}] 0.00 MB/0.00 MB"
            else:
                # Normal file with size
                progress_bar.value = current_size / file_size
                progress_info.value = f"[{index+1}/{len(files)}] {current_size / 1024 / 1024:.2f} MB/{file_size / 1024 / 1024:.2f} MB"

            progress_column.update()

            if stop_event.is_set():
                await ait.aclose()
                break

        # Cleanup: always remove progress UI for single file uploads if any files were processed
        if len(files) > 1:
            if len(progress_column.controls) <= 2:
                batch_dialog.open = False
                batch_dialog.update()
            else:
                batch_dialog.ok_button.visible = True
                batch_dialog.cancel_button.disabled = True
                batch_dialog.update()
        else:
            self.control.page.overlay.remove(progress_column)
            self.control.page.update()

        await get_directory(
            id=self.control.current_directory_id,
            view=self.control.file_listview,
        )

    async def action_directory_upload(self, root_path: str):
        tree = await build_directory_tree(root_path)

        stop_event = asyncio.Event()
        upload_dialog = UploadDirectoryAlertDialog(stop_event)
        self.control.page.show_dialog(upload_dialog)

        # Track "always" choice across all files in directory tree
        always_choice = None

        # Temporarily use FTP mode to create directory tree.
        async def create_dirs_from_tree(parent_path, tree, parent_id=None):
            nonlocal always_choice  # Access the outer variable

            # helper to ensure persistent transfer connection is closed and removed
            async def _close_transfer_conn():
                transfer_conn = getattr(create_dirs_from_tree, "_transfer_conn", None)
                if transfer_conn:
                    try:
                        await transfer_conn.close()
                    except (
                        ConnectionClosed,
                        ConnectionResetError,
                        ConnectionAbortedError,
                    ):
                        pass
                    except Exception:
                        pass
                    try:
                        delattr(create_dirs_from_tree, "_transfer_conn")
                    except Exception:
                        pass

            # Return if termination signal is detected
            if stop_event.is_set():
                await _close_transfer_conn()
                return

            upload_dialog.progress_text.value = _(
                'Creating directory "{parent_path}"'
            ).format(parent_path=parent_path)
            upload_dialog.progress_bar.value = None
            upload_dialog.progress_column.update()

            # conn = self.app_shared.get_not_none_attribute("conn")

            # Create directory on server
            dir_id = await create_directory(
                parent_id,
                os.path.basename(parent_path),
                self.app_shared.username,
                self.app_shared.token,
                exists_ok=True,
            )

            # Create all subdirectories under current directory
            for dirname, subtree in tree["dirs"].items():
                dir_path = os.path.join(parent_path, dirname)
                await create_dirs_from_tree(dir_path, subtree, dir_id)

            # Upload files sequentially

            for filename in tree["files"]:

                # Similarly, return if termination signal is detected
                if stop_event.is_set():
                    await _close_transfer_conn()
                    return

                abs_path = os.path.join(parent_path, filename)

                _current_number = tree["files"].index(filename) + 1
                _total_number = len(tree["files"])

                upload_dialog.progress_text.value = _(
                    '[{_current_number}/{_total_number}] Uploading file "{abs_path}"'
                ).format(
                    _current_number=_current_number,
                    _total_number=_total_number,
                    abs_path=abs_path,
                )

                upload_dialog.progress_bar.value = _current_number / _total_number
                upload_dialog.progress_column.update()

                create_document_response = await do_request(
                    action="create_document",
                    data={
                        "title": filename,
                        "folder_id": dir_id,
                        "access_rules": {},
                    },
                    username=self.app_shared.username,
                    token=self.app_shared.token,
                )

                task_id = None

                if create_document_response.get("code") == 409:
                    # Handle conflict (file already exists)
                    conflict_type = create_document_response.get("data", {}).get("type")
                    conflict_id = create_document_response.get("data", {}).get("id")

                    # conflict_id must be a non-empty string for overwrite to work
                    if conflict_type == "document" and conflict_id:
                        # Use always choice if set, otherwise ask user
                        if always_choice in ("always_overwrite", "always_skip"):
                            user_choice = normalize_always_choice(always_choice)
                        else:
                            # Show overwrite confirmation dialog
                            # Check if there are multiple files in the tree (including nested directories)
                            def _count_files(node: dict) -> int:
                                """Recursively count all files in a directory tree."""
                                files = node.get("files", [])
                                total = len(files)
                                for subtree in node.get("dirs", {}).values():
                                    if isinstance(subtree, dict):
                                        total += _count_files(subtree)
                                return total

                            total_files = _count_files(tree)
                            confirm_dialog = FileOverwriteConfirmDialog(
                                filename=filename,
                                existing_id=conflict_id,
                                is_batch=total_files > 1,
                            )
                            self.control.page.show_dialog(confirm_dialog)
                            user_choice = await confirm_dialog.wait_for_choice()

                            # Store "always" choices for subsequent files
                            if user_choice in ("always_overwrite", "always_skip"):
                                always_choice = user_choice
                                user_choice = normalize_always_choice(user_choice)

                        if user_choice == "overwrite":
                            # Upload as a new version of existing document
                            upload_response = await do_request(
                                action="upload_document",
                                data={
                                    "document_id": conflict_id,
                                },
                                username=self.app_shared.username,
                                token=self.app_shared.token,
                            )

                            if upload_response.get("code") == 200:
                                # Get task_id with defensive checks
                                task_data = upload_response.get("data", {}).get(
                                    "task_data", {}
                                )
                                task_id = task_data.get("task_id")
                                if not task_id:
                                    upload_dialog.error_column.controls.append(
                                        ft.Text(
                                            _(
                                                'Internal error: Missing task_id for file "{filename}"'
                                            ).format(filename=filename)
                                        )
                                    )
                                    upload_dialog.error_column.update()
                                    continue
                            else:
                                upload_dialog.error_column.controls.append(
                                    ft.Text(
                                        _(
                                            'Upload file "{filename}" failed: {errmsg}'
                                        ).format(
                                            filename=filename,
                                            errmsg=upload_response.get(
                                                "message", "Unknown error"
                                            ),
                                        )
                                    )
                                )
                                upload_dialog.error_column.update()
                                continue

                        elif user_choice == "skip":
                            # Skip this file
                            continue

                        else:
                            # User cancelled, stop upload
                            await _close_transfer_conn()
                            return
                    else:
                        # Can't handle this conflict
                        upload_dialog.error_column.controls.append(
                            ft.Text(
                                _('Create file "{filename}" failed: {errmsg}').format(
                                    filename=filename,
                                    errmsg=create_document_response.get(
                                        "message", "Unknown error"
                                    ),
                                )
                            )
                        )
                        upload_dialog.error_column.update()
                        continue

                elif create_document_response.get("code") != 200:
                    upload_dialog.error_column.controls.append(
                        ft.Text(
                            _('Create file "{filename}" failed: {errmsg}').format(
                                filename=filename,
                                errmsg=create_document_response.get(
                                    "message", "Unknown error"
                                ),
                            )
                        )
                    )
                    upload_dialog.error_column.update()
                    continue

                else:
                    # Success - get task_id with defensive checks
                    task_data = create_document_response.get("data", {}).get(
                        "task_data", {}
                    )
                    task_id = task_data.get("task_id")

                # Verify we have a valid task_id before proceeding
                if not task_id:
                    # This should not happen in normal operation
                    upload_dialog.error_column.controls.append(
                        ft.Text(
                            _(
                                'Internal error: Missing task_id for file "{filename}"'
                            ).format(filename=filename)
                        )
                    )
                    upload_dialog.error_column.update()
                    continue

                max_retries = 2

                for retry in range(1, max_retries + 1):
                    try:
                        # reuse a persistent connection stored on the function object
                        transfer_conn = getattr(
                            create_dirs_from_tree, "_transfer_conn", None
                        )

                        if transfer_conn is None:
                            transfer_conn = await get_connection(
                                server_address=self.app_shared.get_not_none_attribute(
                                    "server_address"
                                ),
                                disable_ssl_enforcement=self.app_shared.disable_ssl_enforcement,
                                proxy=self.app_shared.preferences["settings"][
                                    "proxy_settings"
                                ],
                                max_size=1024**2 * 4,
                                force_ipv4=self.app_shared.preferences["settings"].get(
                                    "force_ipv4", False
                                ),
                            )
                            setattr(
                                create_dirs_from_tree, "_transfer_conn", transfer_conn
                            )

                        gen = upload_file_to_server(
                            transfer_conn,
                            task_id,
                            abs_path,
                        )
                        async for current_size, file_size in gen:
                            upload_dialog.progress_bar.value = current_size / file_size
                            upload_dialog.progress_text.value = f"{current_size / 1024 / 1024:.2f} MB/{file_size / 1024 / 1024:.2f} MB"
                            upload_dialog.progress_column.update()
                            if stop_event.is_set():
                                break

                        # if stop was set during upload, ensure connection closed and stop processing
                        if stop_event.is_set():
                            await _close_transfer_conn()
                            return

                        # success -> stop retrying
                        break

                    except Exception as e:
                        # On exception, close and remove the persistent connection so next attempt will recreate it
                        transfer_conn = getattr(
                            create_dirs_from_tree, "_transfer_conn", None
                        )
                        if transfer_conn:
                            try:
                                await transfer_conn.close()
                            except (
                                ConnectionClosed,
                                ConnectionResetError,
                                ConnectionAbortedError,
                            ):
                                pass
                            try:
                                delattr(create_dirs_from_tree, "_transfer_conn")
                            except Exception:
                                pass

                        if retry >= max_retries:
                            upload_dialog.error_column.controls.append(
                                ft.Text(
                                    _(
                                        'Problem occurred when uploading file "{filename}": {err}'
                                    ).format(filename=filename, err=str(e))
                                )
                            )
                            upload_dialog.error_column.update()
                        else:
                            upload_dialog.progress_text.value = _(
                                "Retrying [{retry}/{max_retries}]: {strerr}"
                            ).format(
                                retry=retry,
                                max_retries=max_retries,
                                strerr=str(e),
                            )
                            upload_dialog.progress_text.update()
                        continue

                # If this is the last file in the root directory, close any persistent connection
                if _current_number == _total_number and parent_path == root_path:
                    transfer_conn = getattr(
                        create_dirs_from_tree, "_transfer_conn", None
                    )
                    if transfer_conn:
                        try:
                            await transfer_conn.close()
                        except Exception:
                            pass
                        try:
                            delattr(create_dirs_from_tree, "_transfer_conn")
                        except Exception:
                            pass

        upload_dialog.progress_text.value = _("Please wait")
        upload_dialog.progress_text.update()

        await create_dirs_from_tree(root_path, tree, self.control.current_directory_id)

        upload_dialog.finish_upload()

        await get_directory(
            id=self.control.current_directory_id,
            view=self.control.file_listview,
        )

        if total_errors := len(upload_dialog.error_column.controls):
            upload_dialog.progress_text.value = _(
                "Upload completed with {total_errors} error(s)."
            ).format(total_errors=total_errors)

            upload_dialog.ok_button.visible = True
        else:
            upload_dialog.open = False

        upload_dialog.update()

    def _close_dialog(self, dialog: ft.AlertDialog):
        """Helper method to close a dialog."""
        dialog.open = False
        dialog.update()

    async def action_batch_delete(self):
        """Handle batch delete of selected files and directories."""
        file_ids = list(self.control.file_listview.selected_file_ids)
        directory_ids = list(self.control.file_listview.selected_directory_ids)

        if not file_ids and not directory_ids:
            self.control.send_error(_("No items selected"))
            return

        # Show confirmation dialog
        confirm_dialog = BatchDeleteConfirmDialog(
            file_count=len(file_ids),
            directory_count=len(directory_ids),
        )

        self.control.page.show_dialog(confirm_dialog)

        # Wait for user confirmation
        confirmed = await confirm_dialog.wait_for_confirmation()
        if not confirmed:
            return

        # Execute the batch delete
        await self._execute_batch_delete(file_ids, directory_ids)

    async def _execute_batch_delete(
        self, file_ids: list[str], directory_ids: list[str]
    ):
        """Execute the batch delete operation."""
        # Create cancel event for stopping the operation
        cancel_event = asyncio.Event()
        
        # Create progress dialog with cancel button
        progress_dialog = BatchProgressDialog(
            title=_("Deleting Items"),
            with_cancel=True,
            cancel_event=cancel_event,
        )
        
        self.control.page.show_dialog(progress_dialog)
        
        # Track progress
        total_items = len(file_ids) + len(directory_ids)
        completed = 0
        failed = 0
        cancelled = False
        
        # Get file and directory names for error reporting
        file_names = {
            f["id"]: f["title"] for f in self.control.file_listview.current_files_data
        }
        dir_names = {
            d["id"]: d["name"]
            for d in self.control.file_listview.current_directories_data
        }
        
        # Delete items
        async for item_type, item_id, success, error_msg in batch_delete_items(
            file_ids, directory_ids, cancel_event
        ):
            completed += 1
            
            if not success:
                failed += 1
                item_name = (
                    file_names.get(item_id)
                    if item_type == "file"
                    else dir_names.get(item_id)
                )
                error_text = _('Failed to delete {type} "{name}": {error}').format(
                    type=_("file") if item_type == "file" else _("directory"),
                    name=item_name or item_id,
                    error=error_msg,
                )
                progress_dialog.add_error(error_text)
            
            # Update progress
            progress_text = _(
                "Deleted {completed}/{total} items ({failed} failed)"
            ).format(completed=completed, total=total_items, failed=failed)
            progress_dialog.update_progress(completed, total_items, progress_text)
        
        # Check if operation was cancelled
        if cancel_event.is_set():
            cancelled = True
        
        # Show completion
        if failed > 0:
            progress_dialog.progress_text.value = _("Deletion completed with {failed} error(s)").format(
                failed=failed
            )
            progress_dialog.progress_text.update()
        
        progress_dialog.show_completion(failed > 0)
        
        # Exit selection mode and refresh directory
        self.control.file_listview.toggle_selection_mode(False)
        self.control.selection_toolbar.visible = False
        self.control.top_bar.selection_toggle_button.visible = True
        self.control.selection_toolbar.update()
        self.control.top_bar.update()
        
        await get_directory(
            id=self.control.current_directory_id,
            view=self.control.file_listview,
        )

    async def action_batch_download(self):
        """Handle batch download of selected files and directories."""
        file_ids = list(self.control.file_listview.selected_file_ids)
        directory_ids = list(self.control.file_listview.selected_directory_ids)

        if not file_ids and not directory_ids:
            self.control.send_error(_("No items selected"))
            return

        from include.util.download_path import get_download_root_path

        save_path = get_download_root_path()

        # Get file and directory data
        file_items = [
            f
            for f in self.control.file_listview.current_files_data
            if f["id"] in file_ids
        ]
        directory_items = [
            d
            for d in self.control.file_listview.current_directories_data
            if d["id"] in directory_ids
        ]

        # Create cancel event for stopping the operation
        cancel_event = asyncio.Event()
        
        # Create progress dialog for adding items to download queue
        progress_dialog = BatchProgressDialog(
            title=_("Adding Downloads"),
            with_cancel=True,
            cancel_event=cancel_event,
        )
        
        # Set progress bar to indeterminate initially
        progress_dialog.progress_bar.value = None
        progress_dialog.progress_text.value = _("Adding items to download queue...")
        
        self.control.page.show_dialog(progress_dialog)
        
        # Track progress
        added = 0
        failed = 0
        
        # Add items to download queue
        try:
            async for (
                item_type,
                item_name,
                current_file,
                success,
                error_msg,
            ) in batch_download_items(
                file_items, directory_items, save_path, cancel_event
            ):
                if not success:
                    failed += 1
                    error_text = _('Failed to add {type} "{name}": {error}').format(
                        type=_("file") if item_type == "file" else _("directory"),
                        name=item_name,
                        error=error_msg,
                    )
                    progress_dialog.add_error(error_text)
                else:
                    added += 1
                
                progress_dialog.progress_text.value = _("Adding: {current_file}").format(
                    current_file=current_file
                )
                progress_dialog.progress_text.update()
        except StopAsyncIteration:
            pass
        
        # Show completion message
        if failed > 0:
            progress_dialog.progress_text.value = _(
                "Added {added} items to download queue, {failed} failed"
            ).format(added=added, failed=failed)
            progress_dialog.progress_text.update()
        
        progress_dialog.show_completion(failed > 0)
        
        # Exit selection mode
        self.control.file_listview.toggle_selection_mode(False)
        self.control.selection_toolbar.visible = False
        self.control.top_bar.selection_toggle_button.visible = True
        self.control.selection_toolbar.update()
        self.control.top_bar.update()

    async def action_batch_move(self):
        """Handle batch move of selected files and directories."""
        file_ids = list(self.control.file_listview.selected_file_ids)
        directory_ids = list(self.control.file_listview.selected_directory_ids)
        
        if not file_ids and not directory_ids:
            self.control.send_error(_("No items selected"))
            return
        
        # Show directory selector dialog
        selector_dialog = DirectorySelectorDialog(
            file_listview=self.control,
            excluded_directory_ids=directory_ids,  # Exclude directories being moved
        )
        
        self.control.page.show_dialog(selector_dialog)
        
        # Wait for user to select a directory
        target_directory_id = await selector_dialog.wait_for_selection()
        
        if target_directory_id is None:
            # User cancelled the selection
            return
        
        # Check if target is the same as current directory
        if target_directory_id == self.control.current_directory_id:
            self.control.send_error(_("Target directory is the same as current directory"))
            return
        
        # Execute the batch move
        await self._execute_batch_move(file_ids, directory_ids, target_directory_id)
    
    async def _execute_batch_move(
        self, file_ids: list[str], directory_ids: list[str], target_directory_id: str | None
    ):
        """Execute the batch move operation.
        
        Args:
            file_ids: List of file IDs to move
            directory_ids: List of directory IDs to move
            target_directory_id: Target directory ID (None for root)
        """
        # Create cancel event for stopping the operation
        cancel_event = asyncio.Event()
        
        # Create progress dialog with cancel button
        progress_dialog = BatchProgressDialog(
            title=_("Moving Items"),
            with_cancel=True,
            cancel_event=cancel_event,
        )
        
        self.control.page.show_dialog(progress_dialog)
        
        # Track progress
        total_items = len(file_ids) + len(directory_ids)
        completed = 0
        failed = 0
        
        # Get file and directory names for error reporting
        file_names = {
            f["id"]: f["title"] for f in self.control.file_listview.current_files_data
        }
        dir_names = {
            d["id"]: d["name"]
            for d in self.control.file_listview.current_directories_data
        }
        
        # Move items
        async for item_type, item_id, success, error_msg in batch_move_items(
            file_ids, directory_ids, target_directory_id, cancel_event
        ):
            completed += 1
            
            if not success:
                failed += 1
                item_name = (
                    file_names.get(item_id)
                    if item_type == "file"
                    else dir_names.get(item_id)
                )
                error_text = _('Failed to move {type} "{name}": {error}').format(
                    type=_("file") if item_type == "file" else _("directory"),
                    name=item_name or item_id,
                    error=error_msg,
                )
                progress_dialog.add_error(error_text)
            
            # Update progress
            progress_text = _(
                "Moved {completed}/{total} items ({failed} failed)"
            ).format(completed=completed, total=total_items, failed=failed)
            progress_dialog.update_progress(completed, total_items, progress_text)
        
        # Check if operation was cancelled
        if cancel_event.is_set():
            cancelled = True
        
        # Show completion
        if failed > 0:
            progress_dialog.progress_text.value = _("Move completed with {failed} error(s)").format(
                failed=failed
            )
            progress_dialog.progress_text.update()
        
        progress_dialog.show_completion(failed > 0)
        
        # Exit selection mode and refresh directory
        self.control.file_listview.toggle_selection_mode(False)
        self.control.selection_toolbar.visible = False
        self.control.top_bar.selection_toggle_button.visible = True
        self.control.selection_toolbar.update()
        self.control.top_bar.update()
        
        await get_directory(
            id=self.control.current_directory_id,
            view=self.control.file_listview,
        )    
