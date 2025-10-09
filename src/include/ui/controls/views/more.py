from math import exp
from typing import TYPE_CHECKING
import gettext
import flet as ft

from include.classes.config import AppConfig
from include.ui.util.notifications import send_error
from include.ui.util.quotes import get_quote
from include.util.communication import build_request

if TYPE_CHECKING:
    from include.ui.models.home import HomeModel

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class ChangePasswdDialog(ft.AlertDialog):
    def __init__(
        self,
        tip: str = "",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = False
        self.scrollable = True
        self.title = ft.Text(_("修改密码"))

        self.app_config = AppConfig()

        self.progress_ring = ft.ProgressRing(visible=False)
        self.new_passwd_field = ft.TextField(
            label=_("新密码"),
            on_submit=self.request_set_passwd,
            password=True,
            can_reveal_password=True,
            expand=True
        )
        self.old_passwd_field = ft.TextField(
            label=_("旧密码"),
            on_submit=lambda _: self.new_passwd_field.focus(),
            password=True,
            can_reveal_password=True,
            expand=True
        )
        self.tip_text = ft.Text(tip, visible=bool(tip), text_align=ft.TextAlign.CENTER)

        self.submit_button = ft.Button(
            "修改",
            on_click=self.request_set_passwd,
        )
        self.cancel_button = ft.TextButton("取消", on_click=self.cancel_button_click)

        self.content = ft.Column(
            controls=[
                self.old_passwd_field,
                self.new_passwd_field,
                self.tip_text,
            ],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        self.actions = [
            self.progress_ring,
            self.submit_button,
            self.cancel_button,
        ]

    def disable_interactions(self):
        self.old_passwd_field.disabled = True
        self.new_passwd_field.disabled = True
        self.cancel_button.disabled = True
        self.submit_button.visible = False
        self.progress_ring.visible = True
        self.modal = True

    def enable_interactions(self):
        self.old_passwd_field.disabled = False
        self.new_passwd_field.disabled = False
        self.cancel_button.disabled = False
        self.submit_button.visible = True
        self.progress_ring.visible = False
        self.modal = False

    def close(self):
        self.open = False
        self.update()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def request_set_passwd(
        self, event: ft.Event[ft.TextField] | ft.Event[ft.Button]
    ):
        yield self.disable_interactions()

        response = await build_request(
            self.app_config.get_not_none_attribute("conn"),
            "set_passwd",
            data={
                "username": self.app_config.username,
                "old_passwd": self.old_passwd_field.value,
                "new_passwd": self.new_passwd_field.value,
            },  # 修改密码，无需 data 外提供 username 和 token
        )

        yield self.close()

        if response["code"] != 200:
            send_error(event.page, f"修改密码失败: {response['message']}")
        else:
            assert type(self.page) == ft.Page
            assert self.page.platform

            if self.page.platform.value not in ["ios", "android"]:
                await self.page.window.close()
            else:
                send_error(event.page, "您已登出，请手动重启应用")


class MoreView(ft.Container):
    def __init__(self, parent_model, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.parent_model: "HomeModel" = parent_model

        self.margin = 10
        self.padding = 10
        self.alignment = ft.Alignment.TOP_CENTER
        self.expand = True
        self.visible = False

        self.app_config = AppConfig()

        self.moreview_avatar = ft.CircleAvatar(
            content=ft.Text(),
        )
        self.moreview_username_display = ft.Text(color=ft.Colors.WHITE)

        self.content = ft.Column(
            controls=[
                # Avatar frame
                ft.Row(
                    controls=[
                        self.moreview_avatar,
                        ft.Column(
                            controls=[
                                self.moreview_username_display,
                                ft.Text(get_quote()),
                            ],
                            spacing=0,
                        ),
                    ]
                ),
                ft.Divider(),
                # Menu entries below the avatar
                ft.ListView(
                    controls=[
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.PASSWORD),
                            title=ft.Text("修改密码"),
                            on_click=self.passwd_listtile_click,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.SETTINGS),
                            title=ft.Text("设置"),
                            on_click=self.settings_listtile_click,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.INFO),
                            title=ft.Text("关于"),
                            on_click=self.about_listtile_click,
                        ),
                    ]
                ),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
        )

    def did_mount(self):
        super().did_mount()
        if self.app_config.nickname:
            self.moreview_username_display.value = self.app_config.nickname
        else:
            self.moreview_username_display.value = (
                self.app_config.get_not_none_attribute("username")
            )
        self.moreview_avatar.content = ft.Text(
            self.moreview_username_display.value[0].upper()
        )

    async def passwd_listtile_click(self, event: ft.Event[ft.ListTile]):
        self.page.show_dialog(ChangePasswdDialog())

    async def settings_listtile_click(self, event: ft.Event[ft.ListTile]):
        assert type(self.page) == ft.Page
        await self.page.push_route("/home/settings")

    async def about_listtile_click(self, event: ft.Event[ft.ListTile]):
        assert type(self.page) == ft.Page
        await self.page.push_route("/home/about")
