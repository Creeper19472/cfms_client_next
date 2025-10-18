from datetime import datetime
from typing import TYPE_CHECKING
import flet as ft
import gettext
import asyncio
from include.classes.client import LockableClientConnection
from include.controllers.dialogs.rightmenu import (
    GetDirectoryInfoController,
    RenameDialogController,
)
from include.ui.controls.dialogs.base import AlertDialog
from include.ui.util.notifications import send_error
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.rightmenu.explorer import (
        DocumentRightMenuDialog,
        DirectoryRightMenuDialog,
    )

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class RenameDialog(AlertDialog):
    def __init__(
        self,
        parent_dialog: "DocumentRightMenuDialog|DirectoryRightMenuDialog",
        object_type: str,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = RenameDialogController(self)
        self.object_type = object_type
        match self.object_type:
            case "document":
                self.object_display_name = _("Document")
            case "directory":
                self.object_display_name = _("Directory")
            case _:
                raise

        self.modal = False
        self.title = ft.Text(_(f"Rename {self.object_display_name}"))

        self.parent_dialog = parent_dialog

        self.progress_ring = ft.ProgressRing(visible=False)
        self.name_textfield = ft.TextField(
            label=_(f"New {self.object_display_name} name"),
            on_submit=self.ok_button_click,
            expand=True,
        )

        self.submit_button = ft.TextButton(
            _("Submit"),
            on_click=self.ok_button_click,
        )
        self.cancel_button = ft.TextButton(_("Cancel"), on_click=self.cancel_button_click)

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
            self.name_textfield.error = _(
                f"{self.object_display_name} name cannot be empty"
            )
            self.enable_interactions()
            return

        self.page.run_task(self.controller.action_rename_object, new_title)

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.open = False
        self.update()


class GetDocumentInfoDialog(AlertDialog):
    def __init__(
        self,
        parent_dialog: "DocumentRightMenuDialog",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

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

        self.parent_dialog = parent_dialog

        self.progress_ring = ft.ProgressRing(visible=False)
        self.cancel_button = ft.TextButton(_("Cancel"), on_click=self.cancel_button_click)

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

        assert type(self.page) == ft.Page
        conn = self.page.session.store.get("conn")
        assert type(conn) == LockableClientConnection

        response = await do_request(
            conn,
            action="get_document_info",
            data={
                "document_id": self.parent_dialog.document_id,
            },
            username=self.page.session.store.get("username"),
            token=self.page.session.store.get("token"),
        )
        if (code := response["code"]) != 200:
            self.close()
            send_error(
                self.page,
                _(f"Failed to fetch document info: ({code}) {response['message']}"),
            )
        else:
            self.info_listview.controls = [
                ft.Text(
                    _(f"Document ID: {response['data']['document_id']}"), selectable=True
                ),
                ft.Text(_(f"Document title: {response['data']['title']}"), selectable=True),
                ft.Text(_(f"Document size: {response['data']['size']}")),
                ft.Text(
                    _(
                        f"Created: {datetime.fromtimestamp(response['data']['created_time']).strftime('%Y-%m-%d %H:%M:%S')}"
                    ),
                ),
                ft.Text(
                    _(
                        f"Last modified: {datetime.fromtimestamp(response['data']['last_modified']).strftime('%Y-%m-%d %H:%M:%S')}"
                    ),
                ),
                ft.Text(
                    _(f"Parent directory ID: {response['data']['parent_id']}"), selectable=True
                ),
                ft.Text(
                    _(
                        f"Access rules: {response['data']['access_rules'] if not response['data']['info_code'] else 'Unavailable'}"
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
        parent_dialog: "DirectoryRightMenuDialog",
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

        self.parent_dialog = parent_dialog

        self.progress_ring = ft.ProgressRing(visible=False)
        self.cancel_button = ft.TextButton(_("Cancel"), on_click=self.cancel_button_click)

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
