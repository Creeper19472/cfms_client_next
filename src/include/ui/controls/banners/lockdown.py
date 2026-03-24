from typing import Optional
import asyncio
import flet as ft
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class LockdownBanner(ft.Container):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LockdownBanner, cls).__new__(cls)
        return cls._instance

    def __init__(
        self, visible: bool = True, ref: Optional[ft.Ref["LockdownBanner"]] = None
    ):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self.page: ft.Page
        super().__init__(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.WHITE),
                    ft.Text(_("System Lockdown"), color=ft.Colors.WHITE),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.RED,
            padding=10,
            visible=visible,
            ref=ref,
        )

    def did_mount(self):
        self._running = True
        self.page.run_task(self._update_banner)

    def will_unmount(self):
        self._running = False

    async def _update_banner(self):
        while self._running:
            self.bgcolor = (
                ft.Colors.TRANSPARENT
                if self.bgcolor == ft.Colors.RED
                else ft.Colors.RED
            )
            self.update()
            await asyncio.sleep(1.5)

    def close_banner(self):
        self.visible = False
        self.update()
