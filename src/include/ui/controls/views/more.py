from typing import TYPE_CHECKING
import gettext
import flet as ft

from include.classes.config import AppConfig
from include.ui.controls.dialogs.manage.accounts import PasswdUserDialog
from include.ui.util.quotes import get_quote

if TYPE_CHECKING:
    from include.ui.models.home import HomeModel

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


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
                            title=ft.Text(_("修改密码")),
                            on_click=self.passwd_listtile_click,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.SETTINGS),
                            title=ft.Text(_("设置")),
                            on_click=self.settings_listtile_click,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.INFO),
                            title=ft.Text(_("关于")),
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
        self.page.show_dialog(PasswdUserDialog())

    async def settings_listtile_click(self, event: ft.Event[ft.ListTile]):
        assert type(self.page) == ft.Page
        await self.page.push_route("/home/settings")

    async def about_listtile_click(self, event: ft.Event[ft.ListTile]):
        assert type(self.page) == ft.Page
        await self.page.push_route("/home/about")
