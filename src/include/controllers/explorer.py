import asyncio
import os
from typing import TYPE_CHECKING
import gettext
import flet as ft
from flet import FilePickerFile
from include.classes.config import AppConfig
from include.ui.controls.dialogs.explorer import (
    BatchUploadFileAlertDialog,
    UploadDirectoryAlertDialog,
)
from include.ui.util.path import get_directory
from include.util.connect import get_connection
from include.util.create import create_directory
from include.util.path import build_directory_tree
from include.util.requests import do_request
from include.util.transfer import upload_file_to_server

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileManagerView

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class FileExplorerController:
    def __init__(self, view: "FileManagerView"):
        self.view = view
        self.app_config = AppConfig()

    async def action_upload(self, files: list[FilePickerFile]):
        progress_bar = ft.ProgressBar()
        progress_info = ft.Text(
            _("正在准备上传"), text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE
        )
        progress_column = ft.Column(
            controls=[progress_bar, progress_info],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        stop_event = asyncio.Event()

        batch_dialog = BatchUploadFileAlertDialog(progress_column, stop_event)
        if len(files) > 1:
            self.view.page.show_dialog(batch_dialog)
        else:
            self.view.page.overlay.append(progress_column)
            self.view.page.update()

        for each_file in files:
            if stop_event.is_set():
                break

            if len(files) > 1:
                current_number = files.index(each_file) + 1

                progress_bar.value = current_number / len(files)
                progress_info.value = f"正在上传文件 [{current_number}/{len(files)}]"
                progress_column.update()

            response = await do_request(
                self.app_config.get_not_none_attribute("conn"),
                action="create_document",
                data={
                    "title": each_file.name,
                    "folder_id": self.view.current_directory_id,
                    "access_rules": {},
                },
                username=self.app_config.username,
                token=self.app_config.token,
            )

            if (code := response["code"]) != 200:
                if code == 403:
                    self.view.send_error(
                        _("上传失败: 无权上传文件"),
                    )
                    return
                else:
                    errmsg = _(f"上传失败: ({response['code']}) {response['message']}")
                    if progress_column not in self.view.page.overlay:
                        _new_error_text = ft.Text(
                            errmsg,
                            text_align=ft.TextAlign.CENTER,
                            # color=ft.Colors.RED,
                        )
                        progress_column.controls.append(_new_error_text)
                    else:
                        self.view.send_error(
                            errmsg,
                        )
                    continue

            task_id = response["data"]["task_data"]["task_id"]

            async def handle_file_upload(task_id):  # need abstract
                conn = None

                try:
                    assert each_file.path
                    # get new connection
                    conn = await get_connection(self.app_config.server_address)

                    async for current_size, file_size in upload_file_to_server(
                        conn, task_id, each_file.path
                    ):
                        progress_bar.value = current_size / file_size
                        progress_info.value = f"{current_size / 1024 / 1024:.2f} MB/{file_size / 1024 / 1024:.2f} MB"
                        progress_column.update()
                        if stop_event.is_set():
                            break

                except Exception as exc:
                    _new_error_text = ft.Text(
                        f'在上传 "{each_file.name}" 时遇到问题: {exc}',
                        text_align=ft.TextAlign.CENTER,
                    )
                    progress_column.controls.append(_new_error_text)
                    return

                finally:
                    if conn:
                        await conn._wrapped_connection.close()  # bug: timeout when calling conn.close()
                        # await asyncio.wait_for(conn.close(), timeout=2) # issue: timeout

            await handle_file_upload(task_id)

        if len(files) > 1:
            if len(progress_column.controls) <= 2:
                batch_dialog.open = False
                batch_dialog.update()
            else:
                batch_dialog.ok_button.visible = True
                batch_dialog.cancel_button.disabled = True
                batch_dialog.update()
        else:
            self.view.page.overlay.remove(progress_column)
            self.view.page.update()

        await get_directory(
            id=self.view.current_directory_id,
            view=self.view.file_listview,
        )

    async def action_directory_upload(self, root_path: str):
        tree = await build_directory_tree(root_path)

        stop_event = asyncio.Event()
        upload_dialog = UploadDirectoryAlertDialog(stop_event)
        self.view.page.show_dialog(upload_dialog)

        # 暂时先采用FTP的模式创建目录树。
        async def create_dirs_from_tree(parent_path, tree, parent_id=None):

            # 如果发现终止信号就返回
            if stop_event.is_set():
                return

            upload_dialog.progress_text.value = _(f'正在创建目录 "{parent_path}"')
            upload_dialog.progress_bar.value = None
            upload_dialog.progress_column.update()

            conn = self.app_config.get_not_none_attribute("conn")

            # 在服务器创建目录
            dir_id = await create_directory(
                conn,
                parent_id,
                os.path.basename(parent_path),
                self.app_config.username,
                self.app_config.token,
                exists_ok=True,
            )

            # 创建当前目录下的所有子目录
            for dirname, subtree in tree["dirs"].items():
                dir_path = os.path.join(parent_path, dirname)
                await create_dirs_from_tree(dir_path, subtree, dir_id)

            # 依次上传文件

            for filename in tree["files"]:

                # 同样地，如果发现终止信号就返回
                if stop_event.is_set():
                    return

                abs_path = os.path.join(parent_path, filename)

                _current_number = tree["files"].index(filename) + 1
                _total_number = len(tree["files"])

                upload_dialog.progress_text.value = _(
                    f'[{_current_number}/{_total_number}] 正在上传文件 "{abs_path}"'
                )
                upload_dialog.progress_bar.value = _current_number / _total_number
                upload_dialog.progress_column.update()

                create_document_response = await do_request(
                    conn,
                    action="create_document",
                    data={
                        "title": filename,
                        "folder_id": dir_id,
                        "access_rules": {},
                    },
                    username=self.app_config.username,
                    token=self.app_config.token,
                )

                if create_document_response.get("code") != 200:
                    upload_dialog.error_column.controls.append(
                        ft.Text(
                            _(
                                f'创建文件 "{filename}" 失败: {create_document_response.get("message", "Unknown error")}'
                            )
                        )
                    )
                    upload_dialog.error_column.update()

                max_retries = 2

                for retry in range(1, max_retries + 1):
                    transfer_conn = None
                    try:
                        transfer_conn = await get_connection(
                            self.app_config.server_address,
                            max_size=1024**2 * 4,
                        )
                        async for current_size, file_size in upload_file_to_server(
                            transfer_conn,
                            create_document_response["data"]["task_data"]["task_id"],
                            abs_path,
                        ):
                            upload_dialog.progress_bar.value = current_size / file_size
                            upload_dialog.progress_text.value = f"{current_size / 1024 / 1024:.2f} MB/{file_size / 1024 / 1024:.2f} MB"
                            upload_dialog.progress_column.update()
                            if stop_event.is_set():
                                break
                        await transfer_conn._wrapped_connection.close()
                        break
                    except (
                        Exception
                    ) as e:  # (TimeoutError, websockets.exceptions.ConnectionClosedError)
                        if retry >= max_retries:
                            upload_dialog.error_column.controls.append(
                                ft.Text(
                                    _(f'在上传文件 "{filename}" 时遇到问题：{str(e)}')
                                )
                            )
                            upload_dialog.error_column.update()
                        else:
                            upload_dialog.progress_text.value = _(
                                f"正在重试 [{retry}/{max_retries}]: {str(e)}"
                            )
                            upload_dialog.progress_text.update()
                        continue

        upload_dialog.progress_text.value = _("请稍候")
        upload_dialog.progress_text.update()

        await create_dirs_from_tree(root_path, tree, self.view.current_directory_id)

        upload_dialog.finish_upload()

        await get_directory(
            id=self.view.current_directory_id,
            view=self.view.file_listview,
        )

        if total_errors := len(upload_dialog.error_column.controls):
            upload_dialog.progress_text.value = _(
                _(f"上传完成，共计 {total_errors} 个错误。")
            )
            upload_dialog.ok_button.visible = True
        else:
            upload_dialog.open = False

        upload_dialog.update()
