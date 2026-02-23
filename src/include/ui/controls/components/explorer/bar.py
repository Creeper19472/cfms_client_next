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
from include.ui.controls.components.rulemanager import RuleManager

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileManagerView

t = get_translation()
_ = t.gettext


class SelectionToolbar(ft.Row):
    """Toolbar that appears when items are selected in the file explorer."""

    def __init__(
        self,
        parent_view: "FileManagerView",
        visible: bool = False,
        ref: ft.Ref | None = None,
    ):
        super().__init__(
            visible=visible,
            ref=ref,
            spacing=10,
        )
        self.page: ft.Page
        self.parent_view = parent_view

        # Selection info text
        self.selection_info = ft.Text(
            _("0 items selected"),
            size=14,
            weight=ft.FontWeight.W_500,
        )

        # Action buttons
        self.select_all_button = ft.TextButton(
            content=_("Select All"),
            icon=ft.Icons.SELECT_ALL,
            on_click=self.on_select_all_click,
        )

        self.clear_selection_button = ft.TextButton(
            content=_("Clear"),
            icon=ft.Icons.CLEAR,
            on_click=self.on_clear_selection_click,
        )

        self.download_button = ft.TextButton(
            content=_("Download"),
            icon=ft.Icons.DOWNLOAD,
            on_click=self.on_download_click,
        )

        self.move_button = ft.TextButton(
            content=_("Move"),
            icon=ft.Icons.DRIVE_FILE_MOVE,
            on_click=self.on_move_click,
        )

        self.delete_button = ft.TextButton(
            content=_("Delete"),
            icon=ft.Icons.DELETE,
            on_click=self.on_delete_click,
        )

        self.cancel_button = ft.TextButton(
            content=_("Cancel"),
            icon=ft.Icons.CLOSE,
            on_click=self.on_cancel_click,
        )

        self.controls = [
            self.selection_info,
            ft.VerticalDivider(),
            self.select_all_button,
            self.clear_selection_button,
            ft.VerticalDivider(),
            self.download_button,
            self.move_button,
            self.delete_button,
            ft.VerticalDivider(),
            self.cancel_button,
        ]

    def update_selection_count(self, count: int):
        """Update the selection count display."""
        if count == 0:
            self.selection_info.value = _("0 items selected")
        elif count == 1:
            self.selection_info.value = _("1 item selected")
        else:
            self.selection_info.value = _("{count} items selected").format(count=count)
        self.update()

    async def on_select_all_click(self, event: ft.Event[ft.TextButton]):
        """Handle select all button click."""
        self.parent_view.file_listview.select_all()
        count = self.parent_view.file_listview.get_selected_count()
        self.update_selection_count(count)

    async def on_clear_selection_click(self, event: ft.Event[ft.TextButton]):
        """Handle clear selection button click."""
        self.parent_view.file_listview.clear_selection()
        self.update_selection_count(0)

    async def on_download_click(self, event: ft.Event[ft.TextButton]):
        """Handle download selected button click."""
        self.page.run_task(self.parent_view.controller.action_batch_download)

    async def on_move_click(self, event: ft.Event[ft.TextButton]):
        """Handle move selected button click."""
        self.page.run_task(self.parent_view.controller.action_batch_move)

    async def on_delete_click(self, event: ft.Event[ft.TextButton]):
        """Handle delete selected button click."""
        self.page.run_task(self.parent_view.controller.action_batch_delete)

    async def on_cancel_click(self, event: ft.Event[ft.TextButton]):
        """Handle cancel selection mode button click."""
        self.parent_view.file_listview.toggle_selection_mode(False)
        self.visible = False
        # Show the toggle button again
        self.parent_view.top_bar.selection_toggle_button.visible = True
        self.update()
        self.parent_view.top_bar.update()


class ExplorerTopBar(ft.Row):
    def __init__(
        self,
        parent_view: "FileManagerView",
        visible: bool = True,
        ref: ft.Ref | None = None,
    ):
        # Create selection toggle button first
        self.selection_toggle_button = ft.IconButton(
            ft.Icons.CHECKLIST,
            on_click=self.on_selection_toggle_click,
            tooltip=_("Select items"),
        )

        self.root_permissions_button = ft.IconButton(
            ft.Icons.ADMIN_PANEL_SETTINGS_OUTLINED,
            on_click=self.on_set_root_permissions_click,
            tooltip=_("Set root directory permissions"),
            visible=False,
        )

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
                        self.selection_toggle_button,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=10,
                ),
                ft.Row(
                    controls=[
                        self.root_permissions_button,
                        ft.IconButton(
                            ft.Icons.FOLDER_OPEN_OUTLINED,
                            on_click=self.on_open_folder_button_click,
                        ),
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

    def update_root_button_visibility(self):
        """Show the root-permissions button only when viewing the root directory."""
        at_root = (
            self.parent_view.current_directory_id == self.parent_view.root_directory_id
        )
        self.root_permissions_button.visible = at_root
        self.root_permissions_button.update()

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

    async def on_set_root_permissions_click(self, event: ft.Event[ft.IconButton]):
        self.page.show_dialog(
            RuleManager(self.parent_view.root_directory_id or "/", "directory")
        )

    async def on_search_button_click(self, event: ft.Event[ft.IconButton]):
        """Handle search button click."""
        self.page.show_dialog(SearchDialog(self.parent_view))

    async def on_selection_toggle_click(self, event: ft.Event[ft.IconButton]):
        """Handle selection mode toggle button click."""
        # Enable selection mode
        self.parent_view.file_listview.toggle_selection_mode(True)

        # Show selection toolbar
        self.parent_view.selection_toolbar.visible = True
        self.parent_view.selection_toolbar.update_selection_count(0)
        self.parent_view.selection_toolbar.update()

        # Hide this toggle button while in selection mode
        self.selection_toggle_button.visible = False
        self.update()


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
