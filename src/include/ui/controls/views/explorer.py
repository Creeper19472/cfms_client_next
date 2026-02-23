from typing import Optional, cast
from typing import TYPE_CHECKING
from copy import deepcopy

import flet as ft

from websockets.asyncio.client import ClientConnection
from include.classes.shared import AppShared
from include.controllers.explorer.itself import FileExplorerController
from include.ui.controls.components.explorer.bar import (
    ExplorerTopBar,
    FileSortBar,
    SelectionToolbar,
)
from include.ui.controls.components.explorer.access_denied import AccessDeniedView
from include.ui.util.notifications import send_error
from include.ui.util.file_controls import update_file_controls

if TYPE_CHECKING:
    from include.ui.models.home import HomeModel

from include.classes.ui.enum import SortMode, SortOrder
from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class FilePathIndicator(ft.Column):
    def __init__(
        self,
        display_root: Optional[str] = None,
        ref: ft.Ref | None = None,
    ):
        super().__init__(
            ref=ref,
        )
        self.text = ft.Text("/")
        self.controls = [self.text]

        self.paths: list[str] = []

        if display_root and display_root != "/":
            self.paths.extend(display_root.split("/"))
            self.update_path()

    def update_path(self):
        self.text.value = "/" + "/".join(self.paths)
        self.update()

    def go(self, path: str):
        self.paths.append(path)
        self.update_path()

    def back(self):
        if self.paths:
            self.paths.pop()
        self.update_path()

    def reset(self, new_root: Optional[str] = None):
        self.paths = new_root.split("/") if new_root else []
        self.update_path()


class FileListView(ft.ListView):
    def __init__(
        self,
        parent_manager: "FileManagerView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible, expand=True)
        self.parent: ft.Column
        self.parent_manager = parent_manager

        # The variables should be updated when loading new directory
        self.current_parent_id: str | None = None
        self.current_files_data: list[dict] = []
        self.current_directories_data: list[dict] = []

        # Selection mode state
        self.selection_mode: bool = False
        self.selected_file_ids: set[str] = set()
        self.selected_directory_ids: set[str] = set()

    def sort_files(
        self,
        sort_mode: SortMode = SortMode.BY_NAME,
        sort_order: SortOrder = SortOrder.ASCENDING,
    ):
        """
        Sort the files and directories in the list view.

        This function actually copies the data and sorts them, then
        calls `update_file_controls()` to show the new order.
        """

        _working_files_data = deepcopy(self.current_files_data)
        _working_directories_data = deepcopy(self.current_directories_data)

        match sort_mode:
            case SortMode.BY_NAME:
                dir_key_func = lambda x: x["name"].lower()
                file_key_func = lambda x: x["title"].lower()
            case SortMode.BY_LAST_MODIFIED:
                dir_key_func = file_key_func = lambda x: x.get("last_modified", 0)
            case SortMode.BY_CREATED_AT:
                dir_key_func = file_key_func = lambda x: x.get("created_time", 0)
            case SortMode.BY_SIZE:
                dir_key_func = file_key_func = lambda x: x.get("size", 0)
            case SortMode.BY_TYPE:
                dir_key_func = lambda x: 0
                file_key_func = lambda x: x["title"].split(".")[-1].lower()
            case _:
                dir_key_func = lambda x: x["name"].lower()
                file_key_func = lambda x: x["title"].lower()

        reverse = sort_order == SortOrder.DESCENDING
        _working_files_data.sort(key=file_key_func, reverse=reverse)
        _working_directories_data.sort(key=dir_key_func, reverse=reverse)

        update_file_controls(
            self,
            _working_directories_data,
            _working_files_data,
            self.current_parent_id,
        )

    def toggle_selection_mode(self, enabled: bool):
        """Enable or disable selection mode."""
        self.selection_mode = enabled
        if not enabled:
            # Clear selections when exiting selection mode
            self.selected_file_ids.clear()
            self.selected_directory_ids.clear()

        # Update all controls to show/hide checkboxes
        update_file_controls(
            self,
            self.current_directories_data,
            self.current_files_data,
            self.current_parent_id,
        )

    def select_all(self):
        """Select all files and directories."""
        self.selected_file_ids = {f["id"] for f in self.current_files_data}
        self.selected_directory_ids = {d["id"] for d in self.current_directories_data}

        # Update UI to reflect selections
        update_file_controls(
            self,
            self.current_directories_data,
            self.current_files_data,
            self.current_parent_id,
        )

    def clear_selection(self):
        """Clear all selections."""
        self.selected_file_ids.clear()
        self.selected_directory_ids.clear()

        # Update UI to reflect cleared selections
        update_file_controls(
            self,
            self.current_directories_data,
            self.current_files_data,
            self.current_parent_id,
        )

    def toggle_file_selection(self, file_id: str):
        """Toggle selection state of a file."""
        if file_id in self.selected_file_ids:
            self.selected_file_ids.remove(file_id)
        else:
            self.selected_file_ids.add(file_id)

    def toggle_directory_selection(self, directory_id: str):
        """Toggle selection state of a directory."""
        if directory_id in self.selected_directory_ids:
            self.selected_directory_ids.remove(directory_id)
        else:
            self.selected_directory_ids.add(directory_id)

    def get_selected_count(self) -> int:
        """Get total count of selected items."""
        return len(self.selected_file_ids) + len(self.selected_directory_ids)


class FileManagerView(ft.Container):
    def __init__(self, parent_model, ref: ft.Ref | None = None, visible=True):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.parent_model: HomeModel = parent_model
        self.controller = FileExplorerController(self)
        self.app_shared = AppShared()

        self.margin = 10
        self.padding = 10
        self.alignment = ft.Alignment.TOP_CENTER
        self.expand = True

        # View variable definitions
        self.root_directory_id: str | None = None
        self.previous_directory_id: str | None = None
        self.current_directory_id: str | None = None
        self.conn: ClientConnection

        # Components
        self.indicator = FilePathIndicator("/")
        self.top_bar = ExplorerTopBar(self)
        self.selection_toolbar = SelectionToolbar(self, visible=False)
        self.sort_bar = FileSortBar(self, visible=False)
        self.file_listview = FileListView(self, visible=False)
        self.progress_ring = ft.ProgressRing(visible=False)
        self.access_denied_view: AccessDeniedView | None = None

        self.content = ft.Column(
            controls=[
                ft.Text(_("File Management"), size=24, weight=ft.FontWeight.BOLD),
                self.indicator,
                self.top_bar,
                self.selection_toolbar,
                ft.Divider(),
                self.progress_ring,
                # File list, initially hidden until loading is complete
                self.sort_bar,
                self.file_listview,
            ],
        )

    def build(self):
        self.conn = self.app_shared.get_not_none_attribute("conn")

    def send_error(self, msg: str):
        send_error(self.page, msg)

    def hide_content(self):
        self.file_listview.visible = False
        self.sort_bar.visible = False
        self.progress_ring.visible = True
        if self.access_denied_view is not None:
            self.access_denied_view.visible = False
        self.update()

    def show_content(self):
        self.file_listview.visible = True
        self.sort_bar.visible = True
        self.progress_ring.visible = False
        if self.access_denied_view is not None:
            self.access_denied_view.visible = False
        self.top_bar.update_root_button_visibility()
        self.update()

    def show_access_denied_view(self, reason: str):
        """
        Display the access denied view instead of the file list.

        Args:
            reason: The reason for access denial (from server message)
        """
        # Hide normal content
        self.file_listview.visible = False
        self.sort_bar.visible = False
        self.progress_ring.visible = False

        # Create or update access denied view
        if self.access_denied_view is None:
            self.access_denied_view = AccessDeniedView(self, reason)
            # Add it to the content column
            cast(ft.Column, self.content).controls.append(self.access_denied_view)
        else:
            # Update the reason text using the proper method
            self.access_denied_view.update_reason(reason)
            self.access_denied_view.visible = True

        self.update()

    def hide_access_denied_view(self):
        """Hide the access denied view and prepare to show normal content."""
        if self.access_denied_view is not None:
            self.access_denied_view.visible = False
        self.update()
