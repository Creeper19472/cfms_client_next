import flet as ft
import gettext

t = gettext.translation("client", "ui/locale", fallback=True)
_ = t.gettext


class FloatingUpgradeButton(ft.FloatingActionButton):
    def __init__(self, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.icon = ft.Icons.BROWSER_UPDATED_OUTLINED
        self.on_click = self.button_click
        self.tooltip = _("检查更新")

    async def button_click(self, event: ft.Event[ft.FloatingActionButton]):
        assert type(self.page) == ft.Page
        await self.page.push_route("/connect/about/")