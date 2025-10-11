import flet as ft
from flet_model import Model, route

from include.ui.util.route import get_parent_route


@route("settings")
class SettingsModel(Model):
    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self.appbar = ft.AppBar(
            title=ft.Text("Settings"),
            # center_title=True,
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self._go_back),
        )

        self.listtiles = [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.LINK),
                title=ft.Text("连接"),
                subtitle=ft.Text("更改应用使用代理的规则"),
                on_click=self.configure_conn_listtile_click,
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.SECURITY),
                title=ft.Text("安全"),
                subtitle=ft.Text("调整应用记住连接历史的策略"),
                on_click=self.configure_safety_listtile_click,
            ),
            # ft.ListTile(
            #     leading=ft.Icon(ft.Icons.BROWSER_UPDATED),
            #     title=ft.Text("更新"),
            #     subtitle=ft.Text("自动检查和安装更新"),
            #     # on_click=open_change_passwd_dialog,
            # ),
        ]

        self.listview = ft.ListView(
            expand=True,
            padding=10,
            auto_scroll=True,
            controls=self.listtiles,  # pyright: ignore[reportArgumentType]
        )

        self.controls = [self.listview]

    async def _go_back(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route(get_parent_route(self.page.route))

    async def configure_conn_listtile_click(self, event: ft.Event[ft.ListTile]):
        await self.page.push_route(self.page.route + "/conn_settings")

    async def configure_safety_listtile_click(self, event: ft.Event[ft.ListTile]):
        await self.page.push_route(self.page.route + "/safety_settings")