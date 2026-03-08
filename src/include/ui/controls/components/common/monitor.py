import flet as ft
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class MonitorStack(ft.Stack):
    def __init__(self, ref: ft.Ref[MonitorStack] | None = None, visible=True):
        super().__init__(ref=ref, expand=True, visible=visible)

        self.status_text = ft.Text(_("Ready"), size=14, color=ft.Colors.WHITE)
        self.controls = [
            ft.Container(
                content=self.status_text,
                bgcolor=ft.Colors.TRANSPARENT,
                padding=8,
                border_radius=6,
                bottom=1,
                left=1,
            )
        ]

    def update_status(self, text: str, color: ft.ColorValue = ft.Colors.WHITE):
        """Update the monitor text and color."""
        self.status_text.value = text
        self.status_text.color = color
        self.update()
