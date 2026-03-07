import platform
import flet as ft
import flet.version
from flet_model import Model, Router, route
from flet_material_symbols import Symbols
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
    LOGFILE_PATH,
)
from include.util.locale import get_translation

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

        self.log_textfield = ft.TextField(
            multiline=True,
            read_only=True,
            expand=True,
            expand_loose=True,
            min_lines=5,
            max_lines=15,
        )

        self.logfile_exists_text = ft.Text(_("LOGFILE exists: "))

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
            ft.Text(f"RUNTIME_PATH: {RUNTIME_PATH or '(Not Set)'}"),
            ft.Text(f"LOCALE_PATH: {LOCALE_PATH}"),
            ft.Text(f"LOGFILE_PATH: {LOGFILE_PATH}"),
            ft.Text(f"FLET_APP_CONSOLE: {FLET_APP_CONSOLE or '(Not Set)'}"),
            ft.Text(f"FLET_APP_STORAGE_TEMP: {FLET_APP_STORAGE_TEMP}"),
            ft.Text(f"FLET_APP_STORAGE_DATA: {FLET_APP_STORAGE_DATA}"),
            ft.Text(f"FLET_ASSETS_DIR: {FLET_ASSETS_DIR or '(Not Set)'}"),
            ft.Divider(),
            ft.Text(_("Logs"), size=16, weight=ft.FontWeight.BOLD),
            self.logfile_exists_text,
            ft.Text(_("The last 10 lines of the logfile:")),
            self.log_textfield,
        ]

    async def back_button_click(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route(get_parent_route(self.page.route))

    async def _load_dynamic_info(self) -> None:
        self.logfile_exists_text.value = (
            _("LOGFILE exists: ") + (_("Yes") if LOGFILE_PATH.exists() else _("No"))
        )
        self.log_textfield.value = (
            "\n".join(
                LOGFILE_PATH.read_text(encoding="utf-8", errors="ignore").split("\n")[
                    -10:
                ]
            )
            if LOGFILE_PATH.exists()
            else _("Logfile not found.")
        )
        self.update()

    def did_mount(self) -> None:
        super().did_mount()
        self.page.run_task(self._load_dynamic_info)
