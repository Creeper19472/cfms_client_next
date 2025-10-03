import flet as ft
from flet_model import Model, route


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
                leading=ft.Icon(ft.Icons.SECURITY),
                title=ft.Text("安全"),
                subtitle=ft.Text("更改应用的安全设置"),
                # on_click=open_change_passwd_dialog,
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.NETWORK_WIFI_2_BAR_OUTLINED),
                title=ft.Text("连接"),
                subtitle=ft.Text("更改应用使用代理的规则"),
                # on_click=open_change_passwd_dialog,
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.BROWSER_UPDATED),
                title=ft.Text("更新"),
                subtitle=ft.Text("自动检查和安装更新"),
                # on_click=open_change_passwd_dialog,
            ),
        ]

        self.listview = ft.ListView(
            expand=True,
            padding=10,
            auto_scroll=True,
            controls=self.listtiles,
        )

        self.controls = [self.listview]

    async def _go_back(self, event: ft.Event[ft.IconButton]):
        self.page.views.pop()
        if last_route := self.page.views[-1].route:
            await self.page.push_route(last_route)