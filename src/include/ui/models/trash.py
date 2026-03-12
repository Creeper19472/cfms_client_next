"""Route model for the Trash/Recycle Bin screen."""

import flet as ft
from flet_model import Model, Router, route
from flet_material_symbols import Symbols

from include.ui.controls.views.trash import TrashView
from include.ui.util.route import get_parent_route
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


@route("trash")
class TrashModel(Model):
    """Model for the /home/trash route (Recycle Bin)."""

    vertical_alignment = ft.MainAxisAlignment.START
    horizontal_alignment = ft.CrossAxisAlignment.BASELINE
    padding = ft.Padding(20, 0, 20, 20)
    spacing = 10

    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)

        self.appbar = ft.AppBar(
            title=ft.Text(_("Recycle Bin")),
            leading=ft.IconButton(
                icon=Symbols.ARROW_BACK,
                on_click=self._go_back,
                tooltip=_("Back"),
            ),
        )

        self.trash_view = TrashView(parent_model=self)
        self.controls = [self.trash_view]

    def did_mount(self) -> None:
        """Called every time this view comes to the foreground.
        Use route_data to update the folder being viewed."""
        folder_id = self.route_data.get("folder_id", "/") if self.route_data else "/"
        self.trash_view.folder_id_field.value = folder_id
        self.trash_view.current_folder_id = folder_id
        self.page.run_task(
            self.trash_view.controller.load_deleted_items, folder_id
        )

    async def _go_back(self, event: ft.Event[ft.IconButton]):
        await self.page.push_route(get_parent_route(self.page.route))
