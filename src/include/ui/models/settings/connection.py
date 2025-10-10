import flet as ft
from flet_model import Model, route

from include.classes.config import AppConfig
from include.ui.util.route import get_parent_route


@route("conn_settings")
class ConnectionSettingsModel(Model):
    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self.appbar = ft.AppBar(
            title=ft.Text("Connection"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self._go_back),
        )
        self.app_config = AppConfig()

        self.save_button = ft.TextButton("Save", on_click=self.save_button_click)
        self.enable_proxy_switch = ft.Switch(label="Follow system proxy")
        self.controls = [
            self.enable_proxy_switch,
            self.save_button,
        ]

    def did_mount(self) -> None:
        super().did_mount()
        self.enable_proxy_switch.value = bool(
            self.app_config.preferences["settings"]["proxy_settings"]
        )
        self.update()

    async def _go_back(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route(get_parent_route(self.page.route))

    async def save_button_click(self, event: ft.Event[ft.TextButton]):
        self.app_config.preferences["settings"]["proxy_settings"] = (
            True if self.enable_proxy_switch.value else None
        )
        self.app_config.dump_preferences()
