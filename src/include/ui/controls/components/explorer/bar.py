from typing import TYPE_CHECKING
import flet as ft

from include.ui.controls.dialogs.explorer import (
    CreateDirectoryDialog,
    OpenDirectoryDialog,
)
from include.ui.controls.dialogs.search import SearchDialog
from include.ui.util.file_controls import get_directory
from include.controllers.explorer.bar import FileSortBarController
from include.util.locale import get_translation

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileManagerView

t = get_translation()
_ = t.gettext


class ExplorerTopBar(ft.Row):
    def __init__(
        self,
        parent_view: "FileManagerView",
        visible: bool = True,
        ref: ft.Ref | None = None,
    ):
        super().__init__(
            controls=[
                ft.Row(
                    controls=[
                        ft.IconButton(
                            ft.Icons.ADD, on_click=self.on_upload_button_click
                        ),
                        ft.IconButton(
                            ft.Icons.DRIVE_FOLDER_UPLOAD_OUTLINED,
                            on_click=self.on_upload_directory_button_click,
                        ),
                        ft.IconButton(
                            ft.Icons.CREATE_NEW_FOLDER_OUTLINED,
                            on_click=self.on_create_directory_button_click,
                        ),
                        ft.IconButton(
                            ft.Icons.REFRESH,
                            on_click=self.on_refresh_button_click,
                        ),
                        ft.IconButton(
                            ft.Icons.SEARCH,
                            on_click=self.on_search_button_click,
                            tooltip=_("Search"),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=10,
                ),
                ft.Row(
                    controls=[
                        ft.IconButton(
                            ft.Icons.FOLDER_OPEN_OUTLINED,
                            on_click=self.on_open_folder_button_click,
                        )
                    ],
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=10,
            visible=visible,
            ref=ref,
        )
        self.page: ft.Page
        self.parent_view = parent_view
        # self.controller = ExplorerTopBarController(self)

    async def on_upload_button_click(self, event: ft.Event[ft.IconButton]):
        files = await self.parent_view.parent_model.file_picker.pick_files(
            allow_multiple=True
        )
        if not files:
            return

        self.page.run_task(self.parent_view.controller.action_upload, files)

    async def on_upload_directory_button_click(self, event: ft.Event[ft.IconButton]):
        root_path = await self.parent_view.parent_model.file_picker.get_directory_path()
        if not root_path:
            return

        self.page.run_task(
            self.parent_view.controller.action_directory_upload, root_path
        )

    async def on_create_directory_button_click(self, event: ft.Event[ft.IconButton]):
        create_directory_dialog = CreateDirectoryDialog(self.parent_view)
        self.page.show_dialog(create_directory_dialog)

    async def on_refresh_button_click(self, event: ft.Event[ft.IconButton]):
        await get_directory(
            id=self.parent_view.current_directory_id,
            view=self.parent_view.file_listview,
        )

    async def on_open_folder_button_click(self, event: ft.Event[ft.IconButton]):
        self.page.show_dialog(OpenDirectoryDialog(self.parent_view))

    async def on_search_button_click(self, event: ft.Event[ft.IconButton]):
        """Handle search button click."""
        self.page.show_dialog(SearchDialog(self.parent_view))


class FileSortBar(ft.Row):
    def __init__(
        self,
        parent_view: "FileManagerView",
        visible: bool = True,
        ref: ft.Ref | None = None,
    ):
        super().__init__(
            visible=visible,
            ref=ref,
            margin=ft.Margin(10, 0, 10, 0),
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.page: ft.Page
        self.parent_view = parent_view
        self.controller = FileSortBarController(self)

        self.sort_label = ft.Text(_("Sort by:"), size=14)
        self.sort_dropdown = ft.Dropdown(
            options=[
                ft.DropdownOption("name", _("Name")),
                ft.DropdownOption("created_at", _("Created at")),
                ft.DropdownOption("modified", _("Last Modified")),
                ft.DropdownOption("size", _("Size")),
                ft.DropdownOption("type", _("Type")),
            ],
            value="name",
            on_select=self.sort_dropdown_on_select,
            expand=True,
            expand_loose=True,
        )
        self.order_button = ft.IconButton(
            icon=ft.Icons.ARROW_UPWARD,
            tooltip=_("Toggle Sort Order"),
            on_click=self.order_button_on_click,
        )

        self.controls = [
            self.sort_label,
            self.sort_dropdown,
            self.order_button,
        ]

    async def sort_dropdown_on_select(self, event: ft.Event[ft.Dropdown]) -> None:
        self.page.run_task(self.controller.apply_sorting)

    async def order_button_on_click(self, event: ft.Event[ft.IconButton]) -> None:
        if self.order_button.icon == ft.Icons.ARROW_UPWARD:
            self.order_button.icon = ft.Icons.ARROW_DOWNWARD
        else:
            self.order_button.icon = ft.Icons.ARROW_UPWARD

        self.page.run_task(self.controller.apply_sorting)
