from typing import TYPE_CHECKING
import flet as ft
import gettext, asyncio

from include.classes.config import AppConfig
from include.ui.controls.dialogs.base import AlertDialog
from include.ui.util.notifications import send_error
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.views.manage.group import ManageGroupsView

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class AddUserGroupDialog(AlertDialog):
    def __init__(
        self,
        parent_view: "ManageGroupsView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.parent_view = parent_view
        self.app_config = AppConfig()

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(_("Create User"))

        self.progress_ring = ft.ProgressRing(visible=False)

        self.display_name_field = ft.TextField(
            label=_("Display Name"), on_submit=self.request_create_group, expand=True
        )
        self.group_name_field = ft.TextField(
            label=_("User Group Name"),
            on_submit=lambda _: asyncio.create_task(self.display_name_field.focus()),
            expand=True,
        )

        self.submit_button = ft.TextButton(
            "Create",
            on_click=self.request_create_group,
        )
        self.cancel_button = ft.TextButton(_("Cancel"), on_click=self.cancel_button_click)

        self.content = ft.Column(
            controls=[self.display_name_field, self.group_name_field],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        self.actions = [
            self.progress_ring,
            self.submit_button,
            self.cancel_button,
        ]

    def disable_interactions(self):
        self.progress_ring.visible = True
        self.display_name_field.disabled = True
        self.group_name_field.disabled = True
        self.submit_button.visible = False
        self.cancel_button.disabled = True
        self.modal = True

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def request_create_group(
        self, event: ft.Event[ft.TextField] | ft.Event[ft.TextButton]
    ):

        yield self.disable_interactions()

        response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="create_group",
            data={
                "group_name": self.group_name_field.value,
                "display_name": self.display_name_field.value,
                "permissions": [],  # TODO
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            send_error(self.page, _(f"Failed to create user group: ({code}) {response['message']}"))
        else:
            await self.parent_view.refresh_group_list()

        self.close()
