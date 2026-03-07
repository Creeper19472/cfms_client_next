import platform
import flet as ft
import flet.version
from flet_model import Model, Router, route
from include.ui.util.route import get_parent_route
from include.constants import (
    FLET_ASSETS_DIR,
    ROOT_PATH,
    CONSTANT_FILE_ABSPATH,
    LOCALE_PATH,
    RUNTIME_PATH,
    FLET_APP_CONSOLE,
    FLET_APP_STORAGE_TEMP,
    FLET_APP_STORAGE_DATA,
)
from include.util.locale import get_translation
from flet_material_symbols import Symbols

t = get_translation()
_ = t.gettext


@route("debugging")
class DebuggingViewModel(Model):

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)
        self.appbar = ft.AppBar(
            title=ft.Text(_("Debugging")),
            leading=ft.IconButton(
                icon=Symbols.ARROW_BACK,
                on_click=self.back_button_click,
            ),
        )
        self.scroll = ft.ScrollMode.AUTO

        self.controls = [
            ft.Text(_("General Information"), size=16, weight=ft.FontWeight.BOLD),
            ft.Text(
                f"Platform: {platform.system()} {platform.release()} ({platform.version()})"
            ),
            ft.Text(f"Machine: {platform.machine()}"),
            ft.Text(f"Processor: {platform.processor()}"),
            ft.Text(f"Architecture: {platform.architecture()[0]}"),
            ft.Text(f"Python version: {platform.python_version()}"),
            ft.Text(f"Flet version: {flet.version.flet_version}"),
            ft.Text(f"Flutter version: {flet.version.flutter_version}"),
            ft.Text(
                f"Flet build platform: {getattr(self.page.platform, "value", "(Not provided)")}",
            ),
            ft.Divider(),
            ft.Text(_("Environment Variables"), size=16, weight=ft.FontWeight.BOLD),
            ft.Text(f"CONSTANT_FILE_ABSPATH: {CONSTANT_FILE_ABSPATH}"),
            ft.Text(f"ROOT_PATH: {ROOT_PATH}"),
            ft.Text(f"LOCALE_PATH: {LOCALE_PATH}"),
            ft.Text(f"RUNTIME_PATH: {RUNTIME_PATH or '(Not Set)'}"),
            ft.Text(f"FLET_APP_CONSOLE: {FLET_APP_CONSOLE or '(Not Set)'}"),
            ft.Text(f"FLET_APP_STORAGE_TEMP: {FLET_APP_STORAGE_TEMP}"),
            ft.Text(f"FLET_APP_STORAGE_DATA: {FLET_APP_STORAGE_DATA}"),
            ft.Text(f"FLET_ASSETS_DIR: {FLET_ASSETS_DIR or '(Not Set)'}"),
        ]

    async def back_button_click(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route(get_parent_route(self.page.route))
