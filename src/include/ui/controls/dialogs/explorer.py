from typing import TYPE_CHECKING
import flet as ft
import asyncio, gettext

from include.constants import LOCALE_PATH
from include.controllers.dialogs.directory import (
    CreateDirectoryDialogController,
    OpenDirectoryDialogController,
)
from include.ui.controls.dialogs.base import AlertDialog

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileManagerView

t = gettext.translation("client", LOCALE_PATH, fallback=True)
_ = t.gettext


class CreateDirectoryDialog(AlertDialog):
    def __init__(
        self,
        parent_manager: "FileManagerView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = CreateDirectoryDialogController(self)

        self.modal = False
        self.title = ft.Text(_("Create Directory"))

        self.parent_manager = parent_manager

        self.progress_ring = ft.ProgressRing(visible=False)

        self.directory_textfield = ft.TextField(
            label=_("Directory Name"),
            on_submit=self.ok_button_click,
            expand=True,
        )

        self.submit_button = ft.TextButton(
            _("Create"),
            on_click=self.ok_button_click,
        )
        self.cancel_button = ft.TextButton(_("Cancel"), on_click=self.cancel_button_click)

        self.content = ft.Column(
            controls=[self.directory_textfield],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.progress_ring, self.submit_button, self.cancel_button]

    def disable_interactions(self):
        self.directory_textfield.disabled = True
        self.cancel_button.disabled = True
        self.submit_button.visible = False
        self.progress_ring.visible = True
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

        if not (directory_name := self.directory_textfield.value):
            self.directory_textfield.error = _("Directory name cannot be empty")
            yield self.enable_interactions()
            return

        self.page.run_task(self.controller.action_create_directory, directory_name)

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()


class BatchUploadFileAlertDialog(AlertDialog):
    def __init__(
        self,
        progress_column,
        stop_event: asyncio.Event,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = True
        self.title = ft.Text(_("Batch Upload"))

        self.stop_event = stop_event

        # Predefined buttons
        self.ok_button = ft.TextButton(
            content=_("OK"), on_click=self.ok_button_click, visible=False
        )
        self.cancel_button = ft.TextButton(
            content=_("Cancel"), on_click=self.cancel_button_click
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

    async def ok_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        assert self.page
        self.cancel_button.disabled = True
        self.stop_event.set()
        yield


class UploadDirectoryAlertDialog(AlertDialog):
    def __init__(
        self,
        stop_event: asyncio.Event,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = True
        self.scrollable = True
        self.title = ft.Text(_("Upload Directory"))

        self.stop_event = stop_event

        # Predefined buttons
        self.ok_button = ft.TextButton(
            content=_("OK"), on_click=self.ok_button_click, visible=False
        )
        self.cancel_button = ft.TextButton(
            content=_("Cancel"), on_click=self.cancel_button_click
        )

        # Component definitions
        self.progress_bar = ft.ProgressBar()
        self.progress_text = ft.Text(text_align=ft.TextAlign.CENTER)
        self.progress_column = ft.Column(
            [self.progress_bar, self.progress_text],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.error_column = ft.Column()

        self.content = ft.Column(
            [self.progress_column, self.error_column],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.ok_button, self.cancel_button]

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


class OpenDirectoryDialog(AlertDialog):
    def __init__(
        self,
        parent_manager: "FileManagerView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = OpenDirectoryDialogController(self)

        self.modal = False
        self.title = ft.Text(_("Jump to..."))

        self.parent_manager = parent_manager

        self.progress_ring = ft.ProgressRing(visible=False)

        self.directory_textfield = ft.TextField(
            label=_("Directory ID"),
            on_submit=self.ok_button_click,
            expand=True,
        )

        self.submit_button = ft.TextButton(
            _("Submit"),
            on_click=self.ok_button_click,
        )
        self.cancel_button = ft.TextButton(_("Cancel"), on_click=self.cancel_button_click)

        self.content = ft.Column(
            controls=[self.directory_textfield],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.progress_ring, self.submit_button, self.cancel_button]

    def disable_interactions(self):
        self.directory_textfield.disabled = True
        self.cancel_button.disabled = True
        self.submit_button.visible = False
        self.progress_ring.visible = True
        self.directory_textfield.error = None
        self.modal = True
        self.update()

    def enable_interactions(self):
        self.directory_textfield.disabled = False
        self.cancel_button.disabled = False
        self.submit_button.visible = True
        self.progress_ring.visible = False
        self.modal = False
        self.update()

    async def ok_button_click(
        self, event: ft.Event[ft.TextButton] | ft.Event[ft.TextField]
    ):
        yield self.disable_interactions()

        if not (dir_id := self.directory_textfield.value):
            self.directory_textfield.error = _("Directory id cannot be empty")
            self.enable_interactions()
            return

        self.page.run_task(self.controller.action_open_directory, dir_id)

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()
