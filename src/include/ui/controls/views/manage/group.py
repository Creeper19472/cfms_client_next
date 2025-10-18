import asyncio
from typing import TYPE_CHECKING
import flet as ft

from include.classes.config import AppConfig
from include.ui.controls.dialogs.manage.groups import AddUserGroupDialog
from include.ui.util.notifications import send_error
from include.ui.util.group_controls import update_group_controls
from include.util.requests import do_request

import gettext

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


if TYPE_CHECKING:
    from include.ui.models.manage import ManageModel


class GroupListView(ft.ListView):
    def __init__(
        self,
        parent_manager: "ManageGroupsView",
        ref: ft.Ref | None = None,
        visible=False,
    ):
        super().__init__(ref=ref, visible=visible)
        self.parent: ft.Column
        self.parent_manager = parent_manager
        self.expand = True


class ManageGroupsView(ft.Container):
    def __init__(
        self, parent_model: "ManageModel", ref: ft.Ref | None = None, visible=True
    ):
        super().__init__(ref=ref, visible=visible)
        self.parent_model: "ManageModel" = parent_model
        self.app_config = AppConfig()

        self.margin = 10
        self.padding = 10
        self.alignment = ft.Alignment.TOP_CENTER
        self.expand = True

        self.progress_ring = ft.Row(
            controls=[
                ft.ProgressRing(
                    width=40,
                    height=40,
                    stroke_width=4,
                    value=None,
                )
            ],
            visible=False,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.group_listview = GroupListView(self)

        self.content = ft.Column(
            controls=[
                ft.Text(_("User Group List"), size=24, weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[
                        ft.IconButton(
                            ft.Icons.GROUP_ADD_OUTLINED, on_click=self.add_button_click
                        ),
                        ft.IconButton(
                            ft.Icons.REFRESH,
                            on_click=lambda e: asyncio.create_task(
                                self.refresh_group_list()
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=10,
                ),
                ft.Divider(),
                self.progress_ring,
                self.group_listview,
            ],
        )

    def disable_interactions(self):
        self.progress_ring.visible = True
        self.group_listview.visible = False

    def enable_interactions(self):
        self.progress_ring.visible = False
        self.group_listview.visible = True

    def did_mount(self):
        super().did_mount()
        asyncio.create_task(self.refresh_group_list())

    def add_button_click(self, event: ft.Event[ft.IconButton]):
        self.page.show_dialog(AddUserGroupDialog(self))

    async def refresh_group_list(self, _update_page=True):
        self.disable_interactions()
        self.update()

        response = await do_request(
            self.app_config.get_not_none_attribute("conn"),
            action="list_groups",
            data={},
            username=self.app_config.username,
            token=self.app_config.token,
        )

        if (code := response["code"]) != 200:
            send_error(self.page, _("Load failed: ({code}) {message}").format(code=code, message=response['message']))
        else:
            update_group_controls(
                self.group_listview, response["data"]["groups"], _update_page
            )

        self.enable_interactions()
        self.update()
