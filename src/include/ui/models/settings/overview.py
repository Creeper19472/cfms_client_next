from collections.abc import Awaitable, Callable

from flet_model import Model, Router, route
import flet as ft
from flet_material_symbols import Symbols

from include.ui.frameworks.settings.settings_framework import get_settings_registry
from include.ui.util.route import get_parent_route
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


@route("settings")
class SettingsModel(Model):
    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = 20
    spacing = 10

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)

        self.appbar = ft.AppBar(
            title=ft.Text(_("Settings")),
            # center_title=True,
            leading=ft.IconButton(icon=Symbols.ARROW_BACK, on_click=self._go_back),
        )

        self.listtiles = [
            ft.ListTile(
                leading=ft.Icon(cls.settings_icon),
                title=ft.Text(cls.settings_name),
                subtitle=ft.Text(cls.settings_description),
                on_click=self._make_route_handler(cls.settings_route_suffix),
            )
            for cls in get_settings_registry()
            if cls.settings_route_suffix
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

    def _make_route_handler(
        self, route_suffix: str
    ) -> Callable[[ft.Event[ft.ListTile]], Awaitable[None]]:
        """Return an async click handler that navigates to *route_suffix*."""

        async def handler(event: ft.Event[ft.ListTile]) -> None:
            await self.page.push_route(self.page.route + "/" + route_suffix)

        return handler
