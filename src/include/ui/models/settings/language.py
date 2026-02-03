from flet_model import Model, route, Router
import flet as ft

from include.classes.shared import AppShared
from include.ui.util.notifications import send_success
from include.ui.util.route import get_parent_route
from include.util.locale import set_translation, get_translation

t = get_translation()
_ = t.gettext


@route("language_settings")
class LanguageSettingsModel(Model):
    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)

        self.appbar = ft.AppBar(
            title=ft.Text(_("Language")),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self._go_back),
            actions=[
                ft.IconButton(ft.Icons.SAVE_OUTLINED, on_click=self.save_button_click)
            ],
            actions_padding=10,
        )
        self.app_shared = AppShared()

        # Language selection dropdown
        self.language_dropdown = ft.Dropdown(
            label=_("Language"),
            hint_text=_("Select your preferred language"),
            options=[
                ft.DropdownOption(key="zh_CN", text="中文 (Chinese Simplified)"),
                ft.DropdownOption(key="en", text="English"),
            ],
            expand=True,
            expand_loose=True,
            # disabled=True,  # This feature is currently disabled since it doesnt work
        )

        self.language_hint_text = ft.Text(
            _(
                "Select your preferred language for the application interface. "
                "You may need to restart the application for changes to take full effect."
            ),
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
            self.app_shared.preferences["settings"]["language"] = selected_language
            self.app_shared.dump_preferences()
            set_translation(selected_language)
            self._router.clear_cache()
            send_success(
                self.page,
                _(
                    "Language setting saved. Please restart the application for changes to take effect."
                ),
            )

    async def load_language_setting(self):
        current_language = self.app_shared.preferences["settings"].get(
            "language", "zh_CN"
        )
        self.language_dropdown.value = current_language
        self.update()
