from typing import TYPE_CHECKING
import flet as ft
from flet_material_symbols import Symbols

from include.classes.shared import AppShared
from include.ui.controls.components.account import AccountBadge
from include.ui.controls.dialogs.admin.accounts import PasswdUserDialog
from include.ui.util.quotes import refresh_quote

if TYPE_CHECKING:
    from include.ui.models.home import HomeModel

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class MoreView(ft.Container):
    def __init__(self, parent_model, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.parent_model: "HomeModel" = parent_model

        self.margin = 10
        self.padding = 10
        self.alignment = ft.Alignment.TOP_CENTER
        self.expand = True

        self.app_shared = AppShared()

        refresh_quote()
        self.content = ft.Column(
            controls=[
                # Avatar frame
                AccountBadge(),
                ft.Divider(),
                # Menu entries below the avatar
                ft.ListView(
                    controls=[
                        ft.ListTile(
                            leading=ft.Icon(Symbols.PASSWORD),
                            title=ft.Text(_("Change Password")),
                            on_click=self.passwd_listtile_click,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(Symbols.SETTINGS),
                            title=ft.Text(_("Settings")),
                            on_click=self.settings_listtile_click,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(Symbols.INFO),
                            title=ft.Text(_("About")),
                            on_click=self.about_listtile_click,
                        ),
                    ]
                ),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
        )

    async def passwd_listtile_click(self, event: ft.Event[ft.ListTile]):
        self.page.show_dialog(
            PasswdUserDialog(self.app_shared.get_not_none_attribute("username"))
        )

    async def settings_listtile_click(self, event: ft.Event[ft.ListTile]):
        assert type(self.page) == ft.Page
        await self.page.push_route("/home/settings")

    async def about_listtile_click(self, event: ft.Event[ft.ListTile]):
        assert type(self.page) == ft.Page
        await self.page.push_route("/home/about")
