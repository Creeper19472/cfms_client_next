import flet as ft
from flet_material_symbols import Symbols

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class FloatingUpgradeButton(ft.FloatingActionButton):
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.icon = Symbols.BROWSER_UPDATED
        self.on_click = self.button_click
        self.tooltip = _("Check for Updates")
        # Initialize badge to None (no badge shown)
        self.badge = None

    def show_update_badge(self):
        """Show a badge indicating an update is available."""
        if self.badge is None:
            self.badge = ft.Badge(
                bgcolor=ft.Colors.RED_400,
                small_size=10,
            )
            if self.page:
                self.update()

    def hide_update_badge(self):
        """Hide the update badge."""
        if self.badge is not None:
            self.badge = None
            if self.page:
                self.update()

    async def button_click(self, event: ft.Event[ft.FloatingActionButton]):
        assert type(self.page) is ft.Page
        # Hide badge when user clicks to check updates
        self.hide_update_badge()
        await self.page.push_route("/connect/about/")
