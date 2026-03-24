import asyncio
from datetime import datetime
import sys

import flet as ft
from flet_material_symbols import Symbols
from flet_model import Model, route, Router

from include.classes.shared import AppShared
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


@route("lockdown")
class LockdownModel(Model):
    """
    ViewModel for the Lockdown screen.

    This model manages the state and logic for the lockdown screen, including
    user interactions and data binding for the UI components.
    """

    # Layout configuration
    vertical_alignment = ft.MainAxisAlignment.CENTER
    horizontal_alignment = ft.CrossAxisAlignment.CENTER
    padding = 20
    spacing = 10
    can_pop = False

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)
        # self.scroll = ft.ScrollMode.AUTO

        self.leading = ft.Icon(Symbols.EMERGENCY_HOME, color=ft.Colors.WHITE, size=40)
        self.title = ft.Text(_("Lockdown"), size=24, weight=ft.FontWeight.BOLD)
        self.description = ft.Text(
            _(
                "The server is currently under lockdown for certain reasons. \n"
                "If you have any questions, please contact your system administrator."
            ),
            size=14,
            color=ft.Colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        )
        self.clock = ft.Text(
            "", size=14, color=ft.Colors.WHITE, margin=ft.Margin(top=5, bottom=5)
        )
        self.reject_button = ft.Button(
            _("Quit"),
            on_click=self.quit_button_clicked,
            disabled=AppShared().is_mobile,
        )

        self.controls = [
            ft.SafeArea(self.leading),
            self.title,
            self.description,
            self.clock,
            ft.Divider(),
            ft.Row(
                controls=[
                    ft.Text(_("Wait until the state is lifted or")),
                    self.reject_button,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                wrap=True,
            ),
        ]

    async def quit_button_clicked(self, event: ft.Event[ft.Button]):
        await self.page.window.close()
        sys.exit(0)

    def did_mount(self):
        self._running = True
        self.page.run_task(self._update_time)

    def will_unmount(self):
        self._running = False

    async def _update_time(self):
        ft.context.disable_auto_update()
        try:
            while self._running:
                self.clock.value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.clock.update()
                await asyncio.sleep(0.5)
        finally:
            ft.context.enable_auto_update()
