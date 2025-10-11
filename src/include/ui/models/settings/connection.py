from typing import Literal
import flet as ft
from flet_model import Model, route

from include.classes.config import AppConfig
from include.ui.util.notifications import send_success
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
            actions=[
                ft.IconButton(ft.Icons.SAVE_OUTLINED, on_click=self.save_button_click)
            ],
            actions_padding=10,
        )
        self.app_config = AppConfig()

        self.enable_proxy_switch = ft.Switch(
            label="Enable proxy", on_change=self.switch_click
        )
        self.follow_system_proxy_switch = ft.Switch(
            label="Follow system proxy settings", on_change=self.switch_click
        )
        self.custom_proxy_textfield = ft.TextField(
            label="Custom Proxy",
            hint_text="e.g. socks5h://proxy:1080/",
            expand=True,
            expand_loose=True,
        )

        self.controls = [
            self.enable_proxy_switch,
            self.follow_system_proxy_switch,
            self.custom_proxy_textfield,
        ]

    def did_mount(self) -> None:
        super().did_mount()
        self.page.run_task(self.load_switch_status)

    async def _go_back(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route(get_parent_route(self.page.route))

    async def save_button_click(self, event: ft.Event[ft.IconButton]):
        proxy_settings_value = None
        custom_proxy_value = self.custom_proxy_textfield.value

        self.app_config.preferences["settings"]["custom_proxy"] = custom_proxy_value

        if self.enable_proxy_switch.value:
            if self.follow_system_proxy_switch.value:
                proxy_settings_value = True
            else:
                proxy_settings_value = (
                    custom_proxy_value if custom_proxy_value else True
                )
        else:
            proxy_settings_value = None

        self.app_config.preferences["settings"]["proxy_settings"] = proxy_settings_value
        self.app_config.dump_preferences()
        send_success(self.page, "Settings Saved.")

    async def switch_click(self, event: ft.Event[ft.Switch]):
        await self.flush_switch()

    async def load_switch_status(self):
        proxy_settings: str | Literal[True] | None = self.app_config.preferences[
            "settings"
        ].get("proxy_settings")
        self.enable_proxy_switch.value = bool(proxy_settings)
        self.follow_system_proxy_switch.value = proxy_settings == True
        self.custom_proxy_textfield.value = self.app_config.preferences["settings"].get(
            "custom_proxy", ""
        )
        await self.flush_switch()

    async def flush_switch(self):
        depends_enabling_proxy: list[ft.Control] = [
            self.follow_system_proxy_switch,
            self.custom_proxy_textfield,
        ]

        for control in depends_enabling_proxy:
            control.disabled = not self.enable_proxy_switch.value

        self.custom_proxy_textfield.disabled = (
            not self.enable_proxy_switch.value
        ) or self.follow_system_proxy_switch.value
        self.update()
