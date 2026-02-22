from typing import Optional
from typing import TYPE_CHECKING

import flet as ft

from websockets.asyncio.client import ClientConnection
from include.classes.shared import AppShared
from include.controllers.explorer.itself import FileExplorerController
from include.ui.controls.explorer.components.bar import (
    ExplorerTopBar,
    FileSortBar,
    SelectionToolbar,
)
from include.ui.controls.explorer.state import ExplorerState
from include.ui.controls.explorer.file_controls import ExplorerBody
from include.ui.util.notifications import send_error

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
    """Thin proxy that exposes the legacy ``FileListView`` interface.

    All data and selection state now lives in the parent ``FileManagerView``'s
    ``ExplorerState`` observable.  Attribute access on this object is delegated
    to the state so that existing controllers and dialogs keep working without
    modification.
    """

    def __init__(
        self,
        parent_manager: "FileManagerView",
        ref: ft.Ref | None = None,
    ):
        super().__init__(ref=ref, expand=True)
        self.parent_manager = parent_manager

    # ── State proxies ──────────────────────────────────────────────────────

    @property
    def current_parent_id(self) -> str | None:
        return self.parent_manager.state.parent_id

    @current_parent_id.setter
    def current_parent_id(self, value: str | None) -> None:
        self.parent_manager.state.parent_id = value

    @property
    def current_files_data(self) -> list[dict]:
        return self.parent_manager.state.files

    @current_files_data.setter
    def current_files_data(self, value: list[dict]) -> None:
        self.parent_manager.state.files = value

    @property
    def current_directories_data(self) -> list[dict]:
        return self.parent_manager.state.directories

    @current_directories_data.setter
    def current_directories_data(self, value: list[dict]) -> None:
        self.parent_manager.state.directories = value

    @property
    def selection_mode(self) -> bool:
        return self.parent_manager.state.selection_mode

    @selection_mode.setter
    def selection_mode(self, value: bool) -> None:
        self.parent_manager.state.selection_mode = value

    @property
    def selected_file_ids(self) -> set[str]:
        return self.parent_manager.state.selected_file_ids

    @selected_file_ids.setter
    def selected_file_ids(self, value: set[str]) -> None:
        self.parent_manager.state.selected_file_ids = value

    @property
    def selected_directory_ids(self) -> set[str]:
        return self.parent_manager.state.selected_directory_ids

    @selected_directory_ids.setter
    def selected_directory_ids(self, value: set[str]) -> None:
        self.parent_manager.state.selected_directory_ids = value

    # ── Forwarded actions (update state; ExplorerBody re-renders) ──────────

    def sort_files(
        self,
        sort_mode: SortMode = SortMode.BY_NAME,
        sort_order: SortOrder = SortOrder.ASCENDING,
    ) -> None:
        """Update sort state; ``ExplorerBody`` re-renders with the new order."""
        self.parent_manager.state.sort_mode = sort_mode
        self.parent_manager.state.sort_order = sort_order

    def toggle_selection_mode(self, enabled: bool) -> None:
        """Toggle selection mode; clears selections when disabling."""
        if not enabled:
            self.parent_manager.state.clear_selection()
        self.parent_manager.state.selection_mode = enabled

    def select_all(self) -> None:
        self.parent_manager.state.select_all()

    def clear_selection(self) -> None:
        self.parent_manager.state.clear_selection()

    def toggle_file_selection(self, file_id: str) -> None:
        self.parent_manager.state.toggle_file_selection(file_id)

    def toggle_directory_selection(self, directory_id: str) -> None:
        self.parent_manager.state.toggle_directory_selection(directory_id)

    def get_selected_count(self) -> int:
        return self.parent_manager.state.get_selected_count()


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

        # Observable model — single source of truth for all explorer state.
        # Assigning to its fields triggers automatic re-rendering of ExplorerBody.
        self.state = ExplorerState()

        self.conn: ClientConnection

        # Persistent UI elements (not driven by ExplorerBody)
        self.indicator = FilePathIndicator("/")
        self.top_bar = ExplorerTopBar(self)

        # Compatibility stubs — still referenced by external controllers but
        # no longer rendered in the column; state mutations are the real mechanism.
        self.file_listview = FileListView(self)
        self.selection_toolbar = SelectionToolbar(self, visible=False)
        self.sort_bar = FileSortBar(self, visible=False)

        self.content = ft.Column(
            controls=[
                ft.Text(_("File Management"), size=24, weight=ft.FontWeight.BOLD),
                self.indicator,
                self.top_bar,
                # Kept in the tree so that page is set and .update() calls in
                # existing controllers don't fail; always stays visible=False
                # because ExplorerBody renders the selection bar from state.
                self.selection_toolbar,
                ft.Divider(),
                # ExplorerBody is a @ft.component: it re-renders automatically
                # whenever self.state changes, producing the correct UI for the
                # current loading / access-denied / content state.
                ExplorerBody(self.state, self),
            ],
            expand=True,
        )

    # ── Navigation state proxies (backward-compat for controllers) ─────────

    @property
    def current_directory_id(self) -> str | None:
        return self.state.current_directory_id

    @current_directory_id.setter
    def current_directory_id(self, value: str | None) -> None:
        self.state.current_directory_id = value

    @property
    def root_directory_id(self) -> str | None:
        return self.state.root_directory_id

    @root_directory_id.setter
    def root_directory_id(self, value: str | None) -> None:
        self.state.root_directory_id = value

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def build(self):
        self.conn = self.app_shared.get_not_none_attribute("conn")

    # ── Helper ────────────────────────────────────────────────────────────

    def send_error(self, msg: str):
        send_error(self.page, msg)

    # ── State-mutation helpers (replace the old imperative visibility toggles)

    def hide_content(self) -> None:
        """Show loading indicator — state change triggers ExplorerBody re-render."""
        self.state.is_loading = True
        self.state.is_access_denied = False

    def show_content(self) -> None:
        """Show file list — state change triggers ExplorerBody re-render."""
        self.state.is_loading = False
        self.state.is_access_denied = False

    def show_access_denied_view(self, reason: str) -> None:
        """Show the access-denied message — state change triggers ExplorerBody re-render."""
        self.state.is_loading = False
        self.state.is_access_denied = True
        self.state.access_denied_reason = reason

    def hide_access_denied_view(self) -> None:
        """Hide the access-denied message — state change triggers ExplorerBody re-render."""
        self.state.is_access_denied = False

