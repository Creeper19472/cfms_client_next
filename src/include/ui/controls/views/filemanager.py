import asyncio
import os
from typing import Optional
from typing import TYPE_CHECKING
import gettext
import flet as ft

from include.classes.client import LockableClientConnection
from include.classes.exceptions.request import RequestFailureError
from include.ui.controls.dialogs.filemanager import (
    BatchUploadFileAlertDialog,
    CreateDirectoryDialog,
    OpenDirectoryDialog,
    UploadDirectoryAlertDialog,
)
from include.ui.util.notifications import send_error
from include.ui.util.file_controls import get_directory
from include.util.communication import build_request
from include.util.connect import get_connection
from include.util.create import create_directory
from include.util.path import build_directory_tree
from include.util.transfer import upload_file_to_server

if TYPE_CHECKING:
    from include.ui.models.home import HomeModel

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class FilePathIndicator(ft.Column):
    def __init__(
        self,
        path: Optional[str] = None,
        ref: ft.Ref | None = None,
    ):
        super().__init__(
            ref=ref,
        )
        self.text = ft.Text()
        self.controls = [self.text]
        self.text.value = path if path else "./"
        self.paths: list[str] = []

    def update_path(self):
        self.text.value = "/" + "/".join(self.paths)
        self.update()

    def go(self, path: str):
        self.paths.append(path)
        self.update_path()

    def back(self):
        if self.paths:
            self.paths.pop()
        self.update_path()

    def clear(self):
        self.paths = []
        self.update_path()


class FileListView(ft.ListView):
    def __init__(
        self,
        parent_manager: "FileManagerView",
        ref: ft.Ref | None = None,
        visible=False,
    ):
        super().__init__(ref=ref, visible=visible)
        self.parent: ft.Column
        self.parent_manager = parent_manager
        self.expand = True


class FileManagerView(ft.Container):
    def __init__(self, parent_model, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.parent_model: HomeModel = parent_model

        self.margin = 10
        self.padding = 10
        self.alignment = ft.Alignment.TOP_CENTER
        self.expand = True

        # View variable definitions
        self.previous_directory_id: str | None = None
        self.current_directory_id: str | None = None
        self.conn: LockableClientConnection

        # Components
        self.indicator = FilePathIndicator("/")
        self.file_listview = FileListView(self)
        self.progress_ring = ft.ProgressRing(visible=False)

        self.content = ft.Column(
            controls=[
                ft.Text(_("文件管理"), size=24, weight=ft.FontWeight.BOLD),
                self.indicator,
                ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    ft.Icons.ADD, on_click=self.on_upload_button_click
                                ),
                                ft.IconButton(
                                    ft.Icons.DRIVE_FOLDER_UPLOAD_OUTLINED,
                                    on_click=self.on_upload_directory_button_click,
                                ),
                                ft.IconButton(
                                    ft.Icons.CREATE_NEW_FOLDER_OUTLINED,
                                    on_click=self.on_create_directory_button_click,
                                ),
                                ft.IconButton(
                                    ft.Icons.REFRESH,
                                    on_click=self.on_refresh_button_click,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=10,
                        ),
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    ft.Icons.FOLDER_OPEN_OUTLINED,
                                    on_click=self.on_open_folder_button_click,
                                )
                            ]
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(),
                self.progress_ring,
                # File list, initially hidden until loading is complete
                self.file_listview,
            ],
        )

    def build(self):
        assert type(self.page) == ft.Page
        conn = self.page.session.store.get("conn")
        assert type(conn) == LockableClientConnection
        self.conn = conn

    async def on_upload_button_click(self, event: ft.Event[ft.IconButton]):
        assert type(self.page) == ft.Page

        files = await self.parent_model.file_picker.pick_files(allow_multiple=True)
        if not files:
            return

        progress_bar = ft.ProgressBar()
        progress_info = ft.Text(
            _("正在准备上传"), text_align=ft.TextAlign.CENTER, color=ft.Colors.WHITE
        )
        progress_column = ft.Column(
            controls=[progress_bar, progress_info],
            # alignment=(
            #     ft.MainAxisAlignment.START
            #     if os.name == "nt"
            #     else ft.MainAxisAlignment.END
            # ),
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        stop_event = asyncio.Event()

        batch_dialog = BatchUploadFileAlertDialog(progress_column, stop_event)
        if len(files) > 1:
            self.page.show_dialog(batch_dialog)
        else:
            self.page.overlay.append(progress_column)
            yield

        for each_file in files:

            if stop_event.is_set():
                break

            if len(files) > 1:
                current_number = files.index(each_file) + 1

                progress_bar.value = current_number / len(files)
                progress_info.value = f"正在上传文件 [{current_number}/{len(files)}]"
                yield

            conn = self.page.session.store.get("conn")
            assert type(conn) == LockableClientConnection

            response = await build_request(
                conn,
                action="create_document",
                data={
                    "title": each_file.name,
                    "folder_id": self.current_directory_id,
                    "access_rules": {},
                },
                username=self.page.session.store.get("username"),
                token=self.page.session.store.get("token"),
            )

            if (code := response["code"]) != 200:
                if code == 403:
                    send_error(
                        self.page,
                        _("上传失败: 无权上传文件"),
                    )
                    return
                else:
                    errmsg = _(f"上传失败: ({response['code']}) {response['message']}")
                    if progress_column not in self.page.overlay:
                        _new_error_text = ft.Text(
                            errmsg,
                            text_align=ft.TextAlign.CENTER,
                            # color=ft.Colors.RED,
                        )
                        progress_column.controls.append(_new_error_text)
                    else:
                        send_error(
                            self.page,
                            _(errmsg),
                        )
                    continue

            task_id = response["data"]["task_data"]["task_id"]

            async def handle_file_upload(page, task_id):  # need abstract
                conn = None

                try:
                    assert each_file.path
                    # get new connection
                    conn = await get_connection(page.session.store.get("server_uri"))

                    async for current_size, file_size in upload_file_to_server(
                        conn, task_id, each_file.path
                    ):
                        progress_bar.value = current_size / file_size
                        progress_info.value = f"{current_size / 1024 / 1024:.2f} MB/{file_size / 1024 / 1024:.2f} MB"
                        yield

                except Exception as exc:
                    _new_error_text = ft.Text(
                        f'在上传 "{each_file.name}" 时遇到问题: {exc}',
                        text_align=ft.TextAlign.CENTER,
                        # color=ft.Colors.RED,
                    )
                    progress_column.controls.append(_new_error_text)
                    return

                finally:
                    if conn:
                        await conn._wrapped_connection.close()  # bug: timeout when calling conn.close()
                        # await asyncio.wait_for(conn.close(), timeout=2) # issue: timeout

            async for i in handle_file_upload(self.page, task_id):
                yield

        if len(files) > 1:
            if len(progress_column.controls) <= 2:
                batch_dialog.open = False
                batch_dialog.update()
            else:
                batch_dialog.ok_button.visible = True
                batch_dialog.cancel_button.disabled = True
                batch_dialog.update()
        else:
            self.page.overlay.remove(progress_column)
            yield

        await get_directory(
            id=self.current_directory_id,
            view=self.file_listview,
        )

    async def on_upload_directory_button_click(self, event: ft.Event[ft.IconButton]):
        assert type(self.page) == ft.Page

        root_path = await self.parent_model.file_picker.get_directory_path()
        if not root_path:
            return

        tree = await build_directory_tree(root_path)

        conn = self.page.session.store.get("conn")
        assert type(conn) == LockableClientConnection

        stop_event = asyncio.Event()
        upload_dialog = UploadDirectoryAlertDialog(stop_event)
        self.page.show_dialog(upload_dialog)

        # 暂时先采用FTP的模式创建目录树。
        async def create_dirs_from_tree(parent_path, tree, parent_id=None):
            assert type(self.page) == ft.Page

            # 如果发现终止信号就返回
            if stop_event.is_set():
                return

            upload_dialog.progress_text.value = _(f'正在创建目录 "{parent_path}"')
            upload_dialog.progress_bar.value = None
            upload_dialog.progress_column.update()

            # 在服务器创建目录
            dir_id = await create_directory(
                conn,
                parent_id,
                os.path.basename(parent_path),
                self.page.session.store.get("username"),
                self.page.session.store.get("token"),
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

                create_document_response = await build_request(
                    conn,
                    action="create_document",
                    data={
                        "title": filename,
                        "folder_id": dir_id,
                        "access_rules": {},
                    },
                    username=self.page.session.store.get("username"),
                    token=self.page.session.store.get("token"),
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
                            self.page.session.store.get("server_uri"),
                            max_size=1024**2 * 4,
                        )
                        async for current_size in upload_file_to_server(
                            transfer_conn,
                            create_document_response["data"]["task_data"]["task_id"],
                            abs_path,
                        ):
                            pass
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

        # event.page.open(_alertdialog_ref.current)

        upload_dialog.progress_text.value = _("请稍候")
        upload_dialog.progress_text.update()

        await create_dirs_from_tree(root_path, tree, self.current_directory_id)

        upload_dialog.finish_upload()

        await get_directory(
            id=self.current_directory_id,
            view=self.file_listview,
        )

        if total_errors := len(upload_dialog.error_column.controls):
            upload_dialog.progress_text.value = _(
                _(f"上传完成，共计 {total_errors} 个错误。")
            )
            upload_dialog.ok_button.visible = True
            # upload_dialog.progress_text.update()
        else:
            upload_dialog.open = False

        upload_dialog.update()

        # return

    async def on_create_directory_button_click(self, event: ft.Event[ft.IconButton]):
        create_directory_dialog = CreateDirectoryDialog(self)
        self.page.show_dialog(create_directory_dialog)

    async def on_refresh_button_click(self, event: ft.Event[ft.IconButton]):
        await get_directory(
            id=self.current_directory_id,
            view=self.file_listview,
        )

    async def on_open_folder_button_click(self, event: ft.Event[ft.IconButton]):
        self.page.show_dialog(OpenDirectoryDialog(self))
