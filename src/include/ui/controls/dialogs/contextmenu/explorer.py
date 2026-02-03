from datetime import datetime
from typing import TYPE_CHECKING, Optional
import asyncio

import flet as ft

from include.classes.shared import AppShared
from include.controllers.dialogs.menus import (
    GetDirectoryInfoController,
    RenameDialogController,
)
from include.ui.controls.dialogs.base import AlertDialog
from include.ui.util.notifications import send_error
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileListView

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class RenameDialog(AlertDialog):
    def __init__(
        self,
        object_type: str,
        object_id: str,
        file_listview: "FileListView",
        object_name: Optional[str] = None,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = RenameDialogController(self)
        self.object_type = object_type
        self.object_id = object_id
        self.file_listview = file_listview

        match self.object_type:
            case "document":
                self.object_display_name = _("Document")
            case "directory":
                self.object_display_name = _("Directory")
            case _:
                raise

        self.modal = False
        self.title = ft.Text(
            _("Rename {display_name}").format(display_name=self.object_display_name)
        )

        self.progress_ring = ft.ProgressRing(visible=False)
        self.name_textfield = ft.TextField(
            label=_("New {display_name} name").format(
                display_name=self.object_display_name
            ),
            value=object_name or "",
            on_submit=self.ok_button_click,
            expand=True,
            autofocus=True,
        )

        self.submit_button = ft.TextButton(
            _("Submit"),
            on_click=self.ok_button_click,
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

        self.content = ft.Column(
            controls=[self.name_textfield],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.progress_ring, self.submit_button, self.cancel_button]

    def disable_interactions(self):
        self.name_textfield.disabled = True
        self.cancel_button.disabled = True
        self.submit_button.visible = False
        self.progress_ring.visible = True
        self.name_textfield.error = None
        self.modal = False
        self.update()

    def enable_interactions(self):
        self.name_textfield.disabled = False
        self.cancel_button.disabled = False
        self.submit_button.visible = True
        self.progress_ring.visible = False
        self.modal = True
        self.update()

    async def ok_button_click(
        self, event: ft.Event[ft.TextButton] | ft.Event[ft.TextField]
    ):
        yield self.disable_interactions()

        if not (new_title := self.name_textfield.value):
            self.name_textfield.error = _("{display_name} name cannot be empty").format(
                display_name=self.object_display_name
            )
            self.enable_interactions()
            return

        self.page.run_task(self.controller.action_rename_object, new_title)

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.open = False
        self.update()

    def did_mount(self):
        super().did_mount()
        if value_length := len(self.name_textfield.value):
            self.page.run_task(self.name_textfield.focus)
            self.name_textfield.selection = ft.TextSelection(0, value_length)


class GetDocumentInfoDialog(AlertDialog):
    def __init__(
        self,
        document_id: str,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.document_id = document_id
        self.app_shared = AppShared()

        self.modal = False
        self.title = ft.Row(
            controls=[
                ft.Text(_("Document Details")),
                ft.IconButton(
                    ft.Icons.REFRESH,
                    on_click=self.refresh_button_click,
                ),
            ]
        )

        self.progress_ring = ft.ProgressRing(visible=False)
        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

        self.info_listview = ft.ListView(visible=False)

        self.content = ft.Column(
            controls=[self.progress_ring, self.info_listview],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.cancel_button]

    def did_mount(self):
        super().did_mount()

        async def run():
            async for _ in self.request_document_info():
                pass

        asyncio.create_task(run())

    def disable_interactions(self):
        self.progress_ring.visible = True
        self.info_listview.visible = False

    def enable_interactions(self):
        self.progress_ring.visible = False
        self.info_listview.visible = True

    async def request_document_info(self):

        yield self.disable_interactions()

        response = await do_request(
            action="get_document_info",
            data={
                "document_id": self.document_id,
            },
            username=self.app_shared.username,
            token=self.app_shared.token,
        )
        if (code := response["code"]) != 200:
            self.close()
            send_error(
                self.page,
                _("Failed to fetch document info: ({code}) {message}").format(
                    code=code, message=response["message"]
                ),
            )
        else:
            self.info_listview.controls = [
                ft.Text(
                    _("Document ID: {doc_id}").format(
                        doc_id=response["data"]["document_id"]
                    ),
                    selectable=True,
                ),
                ft.Text(
                    _("Document title: {doc_title}").format(
                        doc_title=response["data"]["title"]
                    ),
                    selectable=True,
                ),
                ft.Text(
                    _("Document size: {doc_size}").format(
                        doc_size=response["data"]["size"]
                    )
                ),
                ft.Text(
                    _("Created: {created_time}").format(
                        created_time=datetime.fromtimestamp(
                            response["data"]["created_time"]
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    ),
                ),
                ft.Text(
                    _("Last modified: {last_modified}").format(
                        last_modified=datetime.fromtimestamp(
                            response["data"]["last_modified"]
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    ),
                ),
                ft.Text(
                    _("Parent directory ID: {parent_id}").format(
                        parent_id=response["data"]["parent_id"]
                    ),
                    selectable=True,
                ),
                ft.Text(
                    _("Access rules: {access_rules}").format(
                        access_rules=(
                            response["data"]["access_rules"]
                            if not response["data"]["info_code"]
                            else "Unavailable"
                        )
                    ),
                    selectable=True,
                ),
            ]
            self.enable_interactions()
            self.update()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    refresh_button_click = request_document_info


class GetDirectoryInfoDialog(AlertDialog):
    def __init__(
        self,
        directory_id: str,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = GetDirectoryInfoController(self)

        self.modal = False
        self.title = ft.Row(
            controls=[
                ft.Text(_("Directory Details")),
                ft.IconButton(
                    ft.Icons.REFRESH,
                    on_click=self.refresh_button_click,
                ),
            ]
        )

        self.directory_id = directory_id

        self.progress_ring = ft.ProgressRing(visible=False)
        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

        self.info_listview = ft.ListView(visible=False)

        self.content = ft.Column(
            controls=[self.progress_ring, self.info_listview],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.cancel_button]

    def did_mount(self):
        super().did_mount()
        self.page.run_task(self.controller.fetch_directory_info)

    def disable_interactions(self):
        self.progress_ring.visible = True
        self.info_listview.visible = False
        self.update()

    def enable_interactions(self):
        self.progress_ring.visible = False
        self.info_listview.visible = True
        self.update()

    async def request_directory_info(self):
        yield self.disable_interactions()
        self.page.run_task(self.controller.fetch_directory_info)

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    refresh_button_click = request_directory_info
