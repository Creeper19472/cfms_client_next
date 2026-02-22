from dataclasses import dataclass, field
from copy import deepcopy

import flet as ft

from include.classes.ui.enum import SortMode, SortOrder


@ft.observable
@dataclass
class ExplorerState:
    """Observable model for all file-explorer state.

    Assigning to any field automatically triggers a re-render of any
    ``@ft.component`` that reads that field — no explicit ``update()`` calls
    are needed.
    """

    # Loading / error state
    is_loading: bool = True
    is_access_denied: bool = False
    access_denied_reason: str = ""

    # Current directory contents (set after a successful list_directory response)
    directories: list = field(default_factory=list)
    files: list = field(default_factory=list)
    parent_id: str | None = None

    # Navigation
    current_directory_id: str | None = None
    root_directory_id: str | None = None

    # Selection
    selection_mode: bool = False
    selected_file_ids: set = field(default_factory=set)
    selected_directory_ids: set = field(default_factory=set)

    # Sort preferences
    sort_mode: SortMode = SortMode.BY_NAME
    sort_order: SortOrder = SortOrder.ASCENDING

    # --- Derived helpers ---

    def sorted_items(self) -> tuple[list, list]:
        """Return ``(sorted_directories, sorted_files)`` according to the current sort settings."""
        dirs = deepcopy(self.directories)
        files = deepcopy(self.files)

        match self.sort_mode:
            case SortMode.BY_NAME:
                dir_key = lambda x: x["name"].lower()
                file_key = lambda x: x["title"].lower()
            case SortMode.BY_LAST_MODIFIED:
                dir_key = file_key = lambda x: x.get("last_modified", 0)
            case SortMode.BY_CREATED_AT:
                dir_key = file_key = lambda x: x.get("created_time", 0)
            case SortMode.BY_SIZE:
                dir_key = file_key = lambda x: x.get("size", 0)
            case SortMode.BY_TYPE:
                dir_key = lambda x: 0
                file_key = lambda x: x["title"].split(".")[-1].lower()
            case _:
                dir_key = lambda x: x["name"].lower()
                file_key = lambda x: x["title"].lower()

        reverse = self.sort_order == SortOrder.DESCENDING
        dirs.sort(key=dir_key, reverse=reverse)
        files.sort(key=file_key, reverse=reverse)
        return dirs, files

    # --- Selection helpers ---

    def select_all(self) -> None:
        self.selected_file_ids = {f["id"] for f in self.files}
        self.selected_directory_ids = {d["id"] for d in self.directories}

    def clear_selection(self) -> None:
        self.selected_file_ids = set()
        self.selected_directory_ids = set()

    def toggle_file_selection(self, file_id: str) -> None:
        new = set(self.selected_file_ids)
        if file_id in new:
            new.discard(file_id)
        else:
            new.add(file_id)
        self.selected_file_ids = new

    def toggle_directory_selection(self, directory_id: str) -> None:
        new = set(self.selected_directory_ids)
        if directory_id in new:
            new.discard(directory_id)
        else:
            new.add(directory_id)
        self.selected_directory_ids = new

    def get_selected_count(self) -> int:
        return len(self.selected_file_ids) + len(self.selected_directory_ids)
