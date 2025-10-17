from typing import TYPE_CHECKING
import flet as ft
import asyncio, gettext

from include.classes.client import LockableClientConnection
from include.classes.exceptions.request import (
    CreateDirectoryFailureError,
    RequestFailureError,
)
from include.ui.util.notifications import send_error
from include.ui.util.path import get_directory
from include.util.create import create_directory

if TYPE_CHECKING:
    from include.ui.controls.views.filemanager import FileManagerView

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class CreateDirectoryDialog(ft.AlertDialog):
    def __init__(
        self,
        parent_manager: "FileManagerView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = False
        self.title = ft.Text(_("创建目录"))

        self.parent_manager = parent_manager

        self.progress_ring = ft.ProgressRing(visible=False)

        self.directory_textfield = ft.TextField(
            label=_("目录名称"),
            on_submit=self.ok_button_click,
            expand=True,
        )
        self.textfield_empty_message = ft.Text(
            _("Directory name cannot be empty"), color=ft.Colors.RED, visible=False
        )

        self.submit_button = ft.TextButton(
            _("创建"),
            on_click=self.ok_button_click,
        )
        self.cancel_button = ft.TextButton(_("取消"), on_click=self.cancel_button_click)

        self.content = ft.Column(
            controls=[self.directory_textfield, self.textfield_empty_message],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.progress_ring, self.submit_button, self.cancel_button]

    def close(self):
        self.open = False
        self.update()

    def disable_interactions(self):
        self.directory_textfield.disabled = True
        self.cancel_button.disabled = True
        self.submit_button.visible = False
        self.progress_ring.visible = True
        self.textfield_empty_message.visible = False
        self.directory_textfield.border_color = None
        self.modal = True

    def enable_interactions(self):
        self.directory_textfield.disabled = False
        self.cancel_button.disabled = False
        self.submit_button.visible = True
        self.progress_ring.visible = False
        self.modal = False

    async def ok_button_click(
        self, event: ft.Event[ft.TextButton] | ft.Event[ft.TextField]
    ):
        yield self.disable_interactions()

        if not (name := self.directory_textfield.value):
            self.directory_textfield.border_color = ft.Colors.RED
            self.textfield_empty_message.visible = True
            yield self.enable_interactions()
            return

        assert type(self.page) == ft.Page
        conn = self.page.session.store.get("conn")
        assert type(conn) == LockableClientConnection

        try:
            await create_directory(
                conn,
                self.parent_manager.current_directory_id,
                name,
                self.page.session.store.get("username"),
                self.page.session.store.get("token"),
            )
        except CreateDirectoryFailureError as err:
            send_error(self.page, str(err))

        await get_directory(
            self.parent_manager.current_directory_id, self.parent_manager.file_listview
        )
        self.close()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()


class BatchUploadFileAlertDialog(ft.AlertDialog):
    def __init__(
        self,
        progress_column,
        stop_event: asyncio.Event,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = True
        self.title = ft.Text(_("批量上传"))

        self.stop_event = stop_event

        # 预定义按钮
        self.ok_button = ft.TextButton(
            content=_("确定"), on_click=self.ok_button_click, visible=False
        )
        self.cancel_button = ft.TextButton(
            content=_("取消"), on_click=self.cancel_button_click
        )

        self.content = ft.Column(
            controls=[progress_column],
            # spacing=15,
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [
            self.ok_button,
            self.cancel_button,
        ]

    def close(self):
        self.open = False
        self.update()

    async def ok_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        assert self.page
        self.cancel_button.disabled = True
        self.stop_event.set()
        yield


class UploadDirectoryAlertDialog(ft.AlertDialog):
    def __init__(
        self,
        stop_event: asyncio.Event,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = True
        self.scrollable = True
        self.title = ft.Text(_("上传目录"))

        self.stop_event = stop_event

        # 预定义按钮
        self.ok_button = ft.TextButton(
            content=_("确定"), on_click=self.ok_button_click, visible=False
        )
        self.cancel_button = ft.TextButton(
            content=_("取消"), on_click=self.cancel_button_click
        )

        # Component definitions
        self.progress_bar = ft.ProgressBar()
        self.progress_text = ft.Text()
        self.progress_column = ft.Column([self.progress_bar, self.progress_text])

        self.error_column = ft.Column()

        self.content = ft.Column(
            [self.progress_column, self.error_column],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.ok_button, self.cancel_button]

    def close(self):
        self.open = False
        self.update()

    def finish_upload(self):
        self.ok_button.disabled = False
        self.cancel_button.disabled = True

    async def ok_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        assert self.page
        self.cancel_button.disabled = True
        self.stop_event.set()
        yield


class OpenDirectoryDialog(ft.AlertDialog):
    def __init__(
        self,
        parent_manager: "FileManagerView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = False
        self.title = ft.Text(_("跳转至..."))

        self.parent_manager = parent_manager

        self.progress_ring = ft.ProgressRing(visible=False)

        self.directory_textfield = ft.TextField(
            label=_("目录ID"),
            on_submit=self.ok_button_click,
            expand=True,
        )
        self.textfield_empty_message = ft.Text(
            _("Directory id cannot be empty"), color=ft.Colors.RED, visible=False
        )

        self.submit_button = ft.TextButton(
            _("提交"),
            on_click=self.ok_button_click,
        )
        self.cancel_button = ft.TextButton(_("取消"), on_click=self.cancel_button_click)

        self.content = ft.Column(
            controls=[self.directory_textfield, self.textfield_empty_message],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.progress_ring, self.submit_button, self.cancel_button]

    def close(self):
        self.open = False
        self.update()

    def disable_interactions(self):
        self.directory_textfield.disabled = True
        self.cancel_button.disabled = True
        self.submit_button.visible = False
        self.progress_ring.visible = True
        self.textfield_empty_message.visible = False
        self.directory_textfield.border_color = None
        self.directory_textfield.error = None
        self.modal = True

    def enable_interactions(self):
        self.directory_textfield.disabled = False
        self.cancel_button.disabled = False
        self.submit_button.visible = True
        self.progress_ring.visible = False
        self.modal = False

    async def ok_button_click(
        self, event: ft.Event[ft.TextButton] | ft.Event[ft.TextField]
    ):
        yield self.disable_interactions()

        if not (dir_id := self.directory_textfield.value):
            self.directory_textfield.border_color = ft.Colors.RED
            self.textfield_empty_message.visible = True
            yield self.enable_interactions()
            return

        try:
            await get_directory(
                dir_id,
                self.parent_manager.file_listview,
                fallback="",
                _raise_on_error=True,
            )
        except RequestFailureError as exc:
            if exc.response:
                self.directory_textfield.error = (
                    "Get directory failed: "
                    f"({exc.response["code"]}) {exc.response["message"]}"
                )
            yield self.enable_interactions()
            return

        self.parent_manager.indicator.clear()
        self.parent_manager.indicator.go(dir_id)
        self.close()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()
