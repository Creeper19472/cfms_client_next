from typing import TYPE_CHECKING
import flet as ft
import gettext, asyncio

from include.classes.config import AppConfig
from include.ui.util.notifications import send_error
from include.util.communication import build_request

if TYPE_CHECKING:
    from include.ui.controls.views.manage.manage import ManageAccountsView

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class AddUserAccountDialog(ft.AlertDialog):
    def __init__(
        self,
        parent_view: "ManageAccountsView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.parent_view = parent_view
        self.app_config = AppConfig()

        self.modal = False
        self.scrollable = True
        self.title = ft.Text("创建用户")

        self.progress_ring = ft.ProgressRing(visible=False)

        self.password_field = ft.TextField(
            label="密码",
            password=True,
            can_reveal_password=True,
            on_submit=self.request_create_user,
            expand=True,
        )
        self.nickname_field = ft.TextField(
            label="昵称",
            on_submit=lambda _: asyncio.create_task(self.password_field.focus()),
            expand=True,
        )
        self.username_field = ft.TextField(
            label="用户名",
            on_submit=lambda _: asyncio.create_task(self.nickname_field.focus()),
            expand=True,
        )

        self.submit_button = ft.TextButton(
            "创建",
            on_click=self.request_create_user,
        )
        self.cancel_button = ft.TextButton("取消", on_click=self.cancel_button_click)

        self.content = ft.Column(
            controls=[self.username_field, self.nickname_field, self.password_field],
            # spacing=15,
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
        self.username_field.disabled = True
        self.nickname_field.disabled = True
        self.password_field.disabled = True
        self.submit_button.visible = False
        self.cancel_button.disabled = True
        self.modal = True

    def close(self):
        self.open = False
        self.update()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def request_create_user(
        self, event: ft.Event[ft.TextField] | ft.Event[ft.TextButton]
    ):

        yield self.disable_interactions()

        response = await build_request(
            self.app_config.get_not_none_attribute("conn"),
            action="create_user",
            data={
                "username": self.username_field.value,
                "password": self.password_field.value,
                "nickname": self.nickname_field.value,
                "permissions": [],  # TODO
                "groups": [],
            },
            username=self.app_config.username,
            token=self.app_config.token,
        )
        if (code := response["code"]) != 200:
            send_error(event.page, f"创建用户失败: ({code}) {response['message']}")
        else:
            await self.parent_view.refresh_user_list()

        self.close()
