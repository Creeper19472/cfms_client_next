import flet as ft
from flet_model import Model, route

from include.classes.config import AppConfig
from include.ui.util.notifications import send_success
from include.ui.util.route import get_parent_route


@route("safety_settings")
class SafetySettingsModel(Model):
    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self.appbar = ft.AppBar(
            title=ft.Text("Safety"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self._go_back),
            actions=[
                ft.IconButton(ft.Icons.SAVE_OUTLINED, on_click=self.save_button_click)
            ],
            actions_padding=10,
        )
        self.app_config = AppConfig()

        self.enable_logging_switch = ft.Switch(
            label=ft.Text(
                "Enable connection history logging",
            ),
            on_change=self.switch_click,
            disabled=True,
        )
        self.logging_hint_text = ft.Text(
            "Decide whether the app should log the "
            "server address of the last connection. "
            "While this feature increases convenience, "
            "it may also increase the risk of exposing "
            "the server address."
        )

        self.controls = [self.enable_logging_switch, self.logging_hint_text]

    def did_mount(self) -> None:
        super().did_mount()
        self.page.run_task(self.load_switch_status)

    async def _go_back(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route(get_parent_route(self.page.route))

    async def save_button_click(self, event: ft.Event[ft.IconButton]):
        self.app_config.preferences["settings"][
            "enable_conn_history_logging"
        ] = self.enable_logging_switch.value

        self.app_config.dump_preferences()
        send_success(self.page, "Settings Saved.")

    async def switch_click(self, event: ft.Event[ft.Switch]):
        await self.flush_switch()

    async def load_switch_status(self):
        self.enable_logging_switch.value = bool(
            self.app_config.preferences["settings"].get("enable_conn_history_logging")
        )
        await self.flush_switch()

    async def flush_switch(self):
        self.update()
