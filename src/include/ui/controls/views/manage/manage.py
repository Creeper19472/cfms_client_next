import asyncio
from typing import TYPE_CHECKING
import flet as ft

from include.classes.config import AppConfig
from include.ui.controls.dialogs.manage.accounts import AddUserAccountDialog
from include.ui.util.notifications import send_error
from include.ui.util.user_controls import update_user_controls
from include.util.communication import build_request

if TYPE_CHECKING:
    from include.ui.models.manage import ManageModel


class UserListView(ft.ListView):
    def __init__(
        self,
        parent_manager: "ManageAccountsView",
        ref: ft.Ref | None = None,
        visible=False,
    ):
        super().__init__(ref=ref, visible=visible)
        self.parent: ft.Column
        self.parent_manager = parent_manager
        self.expand = True


class ManageAccountsView(ft.Container):
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
                    visible=True,
                    width=40,
                    height=40,
                    stroke_width=4,
                    value=None,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.user_listview = UserListView(self)

        self.content = ft.Column(
            controls=[
                ft.Text("用户列表", size=24, weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[
                        ft.IconButton(ft.Icons.ADD, on_click=self.add_button_clicked),
                        ft.IconButton(
                            ft.Icons.REFRESH,
                            on_click=lambda e: asyncio.create_task(
                                self.refresh_user_list()
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=10,
                ),
                ft.Divider(),
                self.progress_ring,
                self.user_listview,
            ],
        )

    def disable_interactions(self):
        self.progress_ring.visible = True
        self.user_listview.visible = False
    
    def enable_interactions(self):
        self.progress_ring.visible = False
        self.user_listview.visible = True

    def did_mount(self):
        super().did_mount()
        asyncio.create_task(self.refresh_user_list())

    def add_button_clicked(self, event: ft.Event[ft.IconButton]):
        self.page.show_dialog(AddUserAccountDialog(self))

    async def refresh_user_list(self, _update_page=True):
        self.disable_interactions()
        self.update()

        response = await build_request(
            self.app_config.get_not_none_attribute("conn"),
            action="list_users",
            data={},
            username=self.app_config.username,
            token=self.app_config.token,
        )

        if (code := response["code"]) != 200:
            send_error(self.page, f"加载失败: ({code}) {response['message']}")
        else:
            update_user_controls(
                self.user_listview, response["data"]["users"], _update_page
            )
        
        self.enable_interactions()
        self.update()
