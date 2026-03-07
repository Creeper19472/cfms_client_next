import flet as ft
import flet_permission_handler as fph
from flet_material_symbols import Symbols
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class ExternalStorageWarningBanner(ft.Banner):
    def __init__(self):
        super().__init__(
            leading=ft.Icon(Symbols.WARNING, color=ft.Colors.PRIMARY),
            content=ft.Text(
                _(
                    "The application has not yet been granted permission to access "
                    "external storage. Please grant the permission to allow this "
                    "feature to function correctly."
                )
            ),
            actions=[
                ft.TextButton(_("Authorize"), on_click=self._authorize),
                ft.TextButton(_("Dismiss"), on_click=self._dismiss),
            ],
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            open=True,
        )

    async def _dismiss(self, event: ft.Event[ft.TextButton]):
        self.open = False
        self.update()

    async def _authorize(self, event: ft.Event[ft.TextButton]):
        self.open = False
        self.update()
        await fph.PermissionHandler().request(fph.Permission.MANAGE_EXTERNAL_STORAGE)
