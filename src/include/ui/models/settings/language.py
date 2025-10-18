import flet as ft
from flet_model import Model, route

from include.classes.config import AppConfig
from include.ui.util.notifications import send_success
from include.ui.util.route import get_parent_route


@route("language_settings")
class LanguageSettingsModel(Model):
    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self.appbar = ft.AppBar(
            title=ft.Text("Language"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self._go_back),
            actions=[
                ft.IconButton(ft.Icons.SAVE_OUTLINED, on_click=self.save_button_click)
            ],
            actions_padding=10,
        )
        self.app_config = AppConfig()

        # Language selection dropdown
        self.language_dropdown = ft.Dropdown(
            label="Language",
            hint_text="Select your preferred language",
            options=[
                ft.dropdown.Option(key="zh_CN", text="中文 (Chinese Simplified)"),
                ft.dropdown.Option(key="en", text="English"),
            ],
            expand=True,
            expand_loose=True,
            disabled=True,  # This feature is currently disabled since it doesnt work
        )

        self.language_hint_text = ft.Text(
            "Select your preferred language for the application interface. "
            "You may need to restart the application for changes to take full effect.",
            size=12,
        )

        self.controls = [self.language_dropdown, self.language_hint_text]

    def did_mount(self) -> None:
        super().did_mount()
        self.page.run_task(self.load_language_setting)

    async def _go_back(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route(get_parent_route(self.page.route))

    async def save_button_click(self, event: ft.Event[ft.IconButton]):
        selected_language = self.language_dropdown.value
        
        if selected_language:
            self.app_config.preferences["settings"]["language"] = selected_language
            self.app_config.dump_preferences()
            send_success(self.page, "Language setting saved. Please restart the application for changes to take effect.")
        else:
            # If no language selected, use default
            self.app_config.preferences["settings"]["language"] = "zh_CN"
            self.app_config.dump_preferences()
            send_success(self.page, "Settings Saved.")

    async def load_language_setting(self):
        current_language = self.app_config.preferences["settings"].get("language", "zh_CN")
        self.language_dropdown.value = current_language
        self.update()
