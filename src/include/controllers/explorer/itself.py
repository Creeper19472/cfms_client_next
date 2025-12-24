from typing import TYPE_CHECKING
import asyncio
import os

from flet import FilePickerFile
import flet as ft
from websockets import ConnectionClosed

from include.classes.exceptions.request import InvalidResponseError
from include.controllers.base import BaseController
from include.ui.controls.dialogs.explorer import (
    BatchUploadFileAlertDialog,
    UploadDirectoryAlertDialog,
    FileOverwriteConfirmDialog,
)
from include.ui.util.path import get_directory
from include.util.connect import get_connection
from include.util.create import create_directory
from include.util.tree import build_directory_tree
from include.util.requests import do_request
from include.util.transfer import batch_upload_file_to_server, upload_file_to_server

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileManagerView

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class FileExplorerController(BaseController["FileManagerView"]):
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
        async def on_conflict(filename: str, conflict_type: str, conflict_id: str) -> str | None:
            """Handle file conflict by showing a dialog to the user."""
            confirm_dialog = FileOverwriteConfirmDialog(
                filename=filename,
                existing_id=conflict_id,
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

        while True:
            try:
                index, filename, current_size, file_size, exc = await ait.__anext__()

            except StopAsyncIteration:
                break

            if isinstance(exc, InvalidResponseError):
                if (code := exc.response.code) == 403:
                    self.control.send_error(
                        _("Upload failed: No permission to upload files")
                    )
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

            # 正常更新进度条
            progress_bar.value = current_size / file_size
            progress_info.value = f"[{index+1}/{len(files)}] {current_size / 1024 / 1024:.2f} MB/{file_size / 1024 / 1024:.2f} MB"
            progress_column.update()

            if stop_event.is_set():
                await ait.aclose()
                break

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

        # Temporarily use FTP mode to create directory tree.
        async def create_dirs_from_tree(parent_path, tree, parent_id=None):

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
                        # Show overwrite confirmation dialog
                        confirm_dialog = FileOverwriteConfirmDialog(
                            filename=filename,
                            existing_id=conflict_id,
                        )
                        self.control.page.show_dialog(confirm_dialog)
                        user_choice = await confirm_dialog.wait_for_choice()
                        
                        if user_choice == 'overwrite':
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
                                task_data = upload_response.get("data", {}).get("task_data", {})
                                task_id = task_data.get("task_id")
                                if not task_id:
                                    upload_dialog.error_column.controls.append(
                                        ft.Text(
                                            _('Internal error: Missing task_id for file "{filename}"').format(
                                                filename=filename
                                            )
                                        )
                                    )
                                    upload_dialog.error_column.update()
                                    continue
                            else:
                                upload_dialog.error_column.controls.append(
                                    ft.Text(
                                        _('Upload file "{filename}" failed: {errmsg}').format(
                                            filename=filename,
                                            errmsg=upload_response.get(
                                                "message", "Unknown error"
                                            ),
                                        )
                                    )
                                )
                                upload_dialog.error_column.update()
                                continue
                        
                        elif user_choice == 'skip':
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
                    task_data = create_document_response.get("data", {}).get("task_data", {})
                    task_id = task_data.get("task_id")
                
                # Verify we have a valid task_id before proceeding
                if not task_id:
                    # This should not happen in normal operation
                    upload_dialog.error_column.controls.append(
                        ft.Text(
                            _('Internal error: Missing task_id for file "{filename}"').format(
                                filename=filename
                            )
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
