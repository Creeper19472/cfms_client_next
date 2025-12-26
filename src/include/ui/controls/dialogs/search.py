"""Search dialog for finding documents and directories."""

from typing import TYPE_CHECKING
from datetime import datetime

import flet as ft

from include.classes.config import AppShared
from include.controllers.dialogs.search import SearchDialogController
from include.ui.controls.dialogs.base import AlertDialog
from include.ui.controls.components.explorer.tile import DirectoryTile, FileTile
from include.ui.util.notifications import send_error

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileManagerView

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


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
                ft.dropdown.Option(_("Name")),
                ft.dropdown.Option(_("Created time")),
                ft.dropdown.Option(_("Last modified")),
                ft.dropdown.Option(_("Size")),
            ],
            value=_("Name"),
            width=200,
        )

        self.sort_order_dropdown = ft.Dropdown(
            label=_("Sort order"),
            options=[
                ft.dropdown.Option(_("Ascending")),
                ft.dropdown.Option(_("Descending")),
            ],
            value=_("Ascending"),
            width=150,
        )

        # Limit option
        self.limit_textfield = ft.TextField(
            label=_("Results limit"),
            value="100",
            width=120,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # Results area
        self.results_title = ft.Text(
            "",
            size=16,
            weight=ft.FontWeight.BOLD,
            visible=False,
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
                ft.Row([
                    self.search_documents_checkbox,
                    self.search_directories_checkbox,
                ]),
                ft.Row([
                    self.sort_by_dropdown,
                    self.sort_order_dropdown,
                    self.limit_textfield,
                ]),
                ft.Divider(),
                # Progress indicators
                ft.Row([
                    self.progress_ring,
                    self.progress_text,
                ]),
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
            self.results_title.value = _("No results found for \"{query}\"").format(query=query)
        else:
            self.results_title.value = _("Found {count} result(s) for \"{query}\"").format(
                count=total_count,
                query=query,
            )
        self.results_title.visible = True

        # Clear previous results
        self.results_listview.controls.clear()

        # Add directory results
        for directory in directories:
            tile = DirectoryTile(
                directory_id=directory["id"],
                dir_name=directory["name"],
            )
            # Make clickable to navigate
            def make_nav_handler(dir_id):
                async def handler(e):
                    # Close dialog
                    self.close()
                    # Navigate to directory
                    from include.ui.util.file_controls import get_directory
                    await get_directory(
                        id=dir_id,
                        view=self.parent_manager.file_listview,
                    )
                return handler
            tile.on_click = make_nav_handler(directory["id"])
            self.results_listview.controls.append(tile)

        # Add document results
        for document in documents:
            tile = FileTile(
                file_id=document["id"],
                filename=document["name"],
                last_modified=document.get("last_modified", 0),
                size=document.get("size", 0),
                show_id=True,
            )
            self.results_listview.controls.append(tile)

        self.results_listview.visible = True if total_count > 0 else False
        self.update()
