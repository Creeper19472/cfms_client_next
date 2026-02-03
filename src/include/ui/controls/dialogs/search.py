"""Search dialog for finding documents and directories."""

from typing import TYPE_CHECKING
from datetime import datetime

import flet as ft

from include.classes.shared import AppShared
from include.controllers.dialogs.search import SearchDialogController
from include.ui.controls.dialogs.base import AlertDialog

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileManagerView

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class SearchResultDirectoryTile(ft.ListTile):
    """Custom directory tile for search results that navigates to the directory."""

    def __init__(
        self,
        directory_id: str,
        directory_name: str,
        created_time: float,
        parent_manager: "FileManagerView",
        dialog,
    ):
        self.directory_id = directory_id
        self.directory_name = directory_name
        self.parent_manager = parent_manager
        self.dialog = dialog

        # Format subtitle with creation time
        subtitle_text = _("Created: {created_time}").format(
            created_time=datetime.fromtimestamp(created_time).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        super().__init__(
            leading=ft.Icon(ft.Icons.FOLDER),
            title=ft.Text(directory_name),
            subtitle=ft.Text(subtitle_text),
            on_click=self.handle_click,
        )

    async def handle_click(self, e):
        """Navigate to this directory."""
        # Close the search dialog
        self.dialog.close()
        # Navigate to the directory
        from include.ui.util.file_controls import get_directory

        await get_directory(
            id=self.directory_id,
            view=self.parent_manager.file_listview,
        )


class SearchResultFileTile(ft.ListTile):
    """Custom file tile for search results that navigates to the parent directory."""

    def __init__(
        self,
        file_id: str,
        filename: str,
        parent_id: str | None,
        size: int,
        last_modified: float,
        parent_manager: "FileManagerView",
        dialog,
    ):
        self.file_id = file_id
        self.filename = filename
        self.parent_id = parent_id
        self.parent_manager = parent_manager
        self.dialog = dialog

        # Format subtitle with size and last modified
        size_text = "0 Byte" if size == 0 else f"{size / 1024 / 1024:.3f} MB"
        modified_text = datetime.fromtimestamp(last_modified).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        subtitle_text = f"{size_text} | {_('Last modified')}: {modified_text}"

        super().__init__(
            leading=ft.Icon(ft.Icons.INSERT_DRIVE_FILE),
            title=ft.Text(filename),
            subtitle=ft.Text(subtitle_text),
            on_click=self.handle_click,
        )

    async def handle_click(self, e):
        """Navigate to the parent directory of this file."""
        # Close the search dialog
        self.dialog.close()
        # Navigate to the parent directory (or root if parent_id is None)
        from include.ui.util.file_controls import get_directory

        await get_directory(
            id=self.parent_id,
            view=self.parent_manager.file_listview,
        )


class SearchDialog(AlertDialog):
    """Dialog for searching documents and directories."""

    def __init__(
        self,
        parent_manager: "FileManagerView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = SearchDialogController(self)
        self.parent_manager = parent_manager
        self.app_shared = AppShared()

        self.modal = False
        self.title = ft.Text(_("Search"))

        # Search input
        self.search_textfield = ft.TextField(
            label=_("Search query"),
            hint_text=_("Enter search term"),
            on_submit=self.on_search_click,
            expand=True,
            autofocus=True,
        )

        # Search options
        self.search_documents_checkbox = ft.Checkbox(
            label=_("Documents"),
            value=True,
        )
        self.search_directories_checkbox = ft.Checkbox(
            label=_("Directories"),
            value=True,
        )

        # Sort options
        self.sort_by_dropdown = ft.Dropdown(
            label=_("Sort by"),
            options=[
                ft.DropdownOption("name", _("Name")),
                ft.DropdownOption("created_time", _("Created time")),
                ft.DropdownOption("last_modified", _("Last modified")),
                ft.DropdownOption("size", _("Size")),
            ],
            value="name",
            expand=True,
            expand_loose=True,
        )

        self.sort_order_dropdown = ft.Dropdown(
            label=_("Sort order"),
            options=[
                ft.DropdownOption("asc", _("Ascending")),
                ft.DropdownOption("desc", _("Descending")),
            ],
            value="asc",
            expand=True,
            expand_loose=True,
        )

        # Limit option
        self.limit_textfield = ft.TextField(
            label=_("Results limit"),
            value="100",
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
            expand_loose=True,
        )

        # Results area
        self.results_title = ft.Text(
            "",
            size=16,
            weight=ft.FontWeight.BOLD,
            visible=False,
            align=ft.Alignment.CENTER,
        )
        self.results_listview = ft.ListView(
            controls=[],
            spacing=5,
            height=400,
            visible=False,
        )

        # Progress indicator
        self.progress_ring = ft.ProgressRing(visible=False)
        self.progress_text = ft.Text(_("Searching..."), visible=False)

        # Buttons
        self.search_button = ft.TextButton(
            _("Search"),
            on_click=self.on_search_click,
            icon=ft.Icons.SEARCH,
        )
        self.close_button = ft.TextButton(
            _("Close"),
            on_click=self.on_close_click,
        )

        # Layout
        self.content = ft.Column(
            controls=[
                # Search input row
                ft.Row([self.search_textfield]),
                ft.Divider(),
                # Options section
                ft.Text(_("Search Options"), weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        self.search_documents_checkbox,
                        self.search_directories_checkbox,
                    ]
                ),
                ft.Row(
                    [
                        self.sort_by_dropdown,
                        self.sort_order_dropdown,
                        self.limit_textfield,
                    ]
                ),
                ft.Divider(),
                # Progress indicators
                ft.Row(
                    [
                        self.progress_ring,
                        self.progress_text,
                    ]
                ),
                # Results section
                self.results_title,
                self.results_listview,
            ],
            width=700,
            scroll=ft.ScrollMode.AUTO,
        )

        self.actions = [self.search_button, self.close_button]

    async def on_search_click(
        self, event: ft.Event[ft.TextButton] | ft.Event[ft.TextField]
    ):
        """Handle search button click."""
        await self.controller.action_search()

    async def on_close_click(self, event: ft.Event[ft.TextButton]):
        """Handle close button click."""
        self.close()

    def show_loading(self):
        """Show loading state."""
        self.search_button.disabled = True
        self.search_textfield.disabled = True
        self.progress_ring.visible = True
        self.progress_text.visible = True
        self.results_title.visible = False
        self.results_listview.visible = False
        self.results_listview.controls.clear()
        self.update()

    def hide_loading(self):
        """Hide loading state."""
        self.search_button.disabled = False
        self.search_textfield.disabled = False
        self.progress_ring.visible = False
        self.progress_text.visible = False
        self.update()

    def display_results(self, data: dict, query: str):
        """Display search results."""
        self.hide_loading()

        documents = data.get("documents", [])
        directories = data.get("directories", [])
        total_count = data.get("total_count", 0)

        # Update title
        if total_count == 0:
            self.results_title.value = _('No results found for "{query}"').format(
                query=query
            )
        else:
            self.results_title.value = _(
                'Found {count} result(s) for "{query}"'
            ).format(
                count=total_count,
                query=query,
            )
        self.results_title.visible = True

        # Clear previous results
        self.results_listview.controls.clear()

        # Add directory results - clicking navigates to the directory itself
        for directory in directories:
            tile = SearchResultDirectoryTile(
                directory_id=directory["id"],
                directory_name=directory["name"],
                created_time=directory.get("created_time", 0),
                parent_manager=self.parent_manager,
                dialog=self,
            )
            self.results_listview.controls.append(tile)

        # Add document results - clicking navigates to the parent directory
        for document in documents:
            tile = SearchResultFileTile(
                file_id=document["id"],
                filename=document["name"],
                parent_id=document.get("parent_id"),
                size=document.get("size", 0),
                last_modified=document.get("last_modified", 0),
                parent_manager=self.parent_manager,
                dialog=self,
            )
            self.results_listview.controls.append(tile)

        self.results_listview.visible = True if total_count > 0 else False
        self.update()
