"""Unified file browser dialog for selecting files and directories.

This module provides a unified, configurable dialog for browsing and selecting
files and/or directories. It replaces the previous separate implementations of
DocumentSelectorDialog, DirectorySelectorDialog, and MoveDialog with a single
flexible component.
"""

import asyncio
from typing import TYPE_CHECKING, Callable, Optional

import flet as ft

from include.classes.shared import AppShared
from include.ui.controls.dialogs.base import AlertDialog
from include.util.locale import get_translation
from include.util.requests import do_request

if TYPE_CHECKING:
    pass

t = get_translation()
_ = t.gettext


class FileBrowserDialog(AlertDialog):
    """Unified dialog for browsing and selecting files and/or directories.

    This dialog provides a flexible interface for navigating directory hierarchies
    and selecting files or directories based on configuration options.

    Features:
    - Directory navigation with breadcrumb path display
    - Optional file filtering (e.g., images only)
    - Optional directory exclusion (e.g., prevent moving into self)
    - Configurable selection mode (files only, directories only, or both)
    - Async directory loading with progress indicators
    - Navigation stack for back/forward navigation
    """

    def __init__(
        self,
        title: Optional[str] = None,
        on_select_callback: Optional[Callable] = None,
        initial_directory_id: Optional[str] = None,
        mode: str = "both",
        file_filter: Optional[Callable[[str], bool]] = None,
        excluded_directory_ids: Optional[list[str]] = None,
        show_select_button: bool = False,
        select_button_text: Optional[str] = None,
        select_button_icon: Optional[ft.IconData] = None,
        show_breadcrumb: bool = True,
        modal: bool = False,
        ref: ft.Ref | None = None,
        visible: bool = True,
    ):
        """Initialize file browser dialog.

        Args:
            title: Dialog title (default: "Browse Files and Directories")
            on_select_callback: Callback function(item_id, item_name, item_type) when item is selected
                - For files: (file_id, file_name, "file")
                - For directories with select button: (dir_id, dir_name, "directory")
            initial_directory_id: Starting directory (None for root)
            mode: Selection mode - "files", "directories", or "both" (default: "both")
            file_filter: Optional function(filename) -> bool to filter files
            excluded_directory_ids: List of directory IDs to exclude from display
            show_select_button: Whether to show a button to select current directory
            select_button_text: Text for the select button (default: "Select Here")
            select_button_icon: Icon for the select button (default: Icons.CHECK_CIRCLE)
            show_breadcrumb: Whether to show breadcrumb path (default: True)
            modal: Whether dialog should be initially modal (default: False)
            ref: Flet reference
            visible: Whether dialog is visible initially
        """
        super().__init__(ref=ref, visible=visible, modal=modal)

        self.on_select_callback = on_select_callback
        self.app_shared = AppShared()

        # Configuration
        self.initially_modal = modal
        self.mode = mode
        self.file_filter = file_filter
        self.excluded_directory_ids = excluded_directory_ids or []
        self.show_select_button = show_select_button
        self.show_breadcrumb = show_breadcrumb

        # Current navigation state
        self.current_directory_id: Optional[str] = initial_directory_id
        self.navigation_stack: list[tuple[Optional[str], str]] = (
            []
        )  # [(dir_id, dir_name)]
        
        self.reached_root: Optional[bool] = False

        # Selection state (for async wait pattern)
        self.selected_item_id: Optional[str] = None
        self.selection_event = asyncio.Event()

        self.modal = True
        self.scrollable = True
        self.title = ft.Text(title if title else _("Browse Files and Directories"))

        # Progress indicator
        self.progress_ring = ft.ProgressRing(visible=True, width=32, height=32)

        # Current location indicator
        self.location_text = ft.Text(
            _("Current location: {path}").format(path="/"),
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_400,
        )

        # Items list view
        self.items_listview = ft.ListView(
            visible=False,
            expand=True,
            spacing=5,
            padding=10,
        )

        # Action buttons
        self.select_here_button = ft.Button(
            select_button_text if select_button_text else _("Select Here"),
            icon=select_button_icon if select_button_icon else ft.Icons.CHECK_CIRCLE,
            on_click=self.select_here_button_click,
            visible=show_select_button,
        )

        self.go_to_root_button = ft.TextButton(
            _("Go to Root"),
            icon=ft.Icons.HOME,
            on_click=self.go_to_root_button_click,
            visible=False,
        )

        self.cancel_button = ft.TextButton(
            _("Cancel"),
            on_click=self.cancel_button_click,
        )

        # Content layout - conditionally include breadcrumb based on configuration
        content_controls = []
        if self.show_breadcrumb:
            content_controls.extend(
                [
                    self.location_text,
                    ft.Divider(),
                ]
            )
        content_controls.extend(
            [
                self.progress_ring,
                self.items_listview,
            ]
        )

        self.content = ft.Column(
            controls=content_controls,
            width=550,
            height=400,
            spacing=10,
        )

        # Build actions list based on configuration
        actions = []
        if self.show_select_button:
            actions.append(self.select_here_button)
        actions.extend([self.go_to_root_button, self.cancel_button])
        self.actions = actions

    def did_mount(self):
        """Called when dialog is mounted to the page. Loads initial directory."""
        super().did_mount()
        asyncio.create_task(self.load_directory(self.current_directory_id))

    def disable_interactions(self):
        """Disable user interactions during async operations."""
        self.select_here_button.disabled = True
        self.go_to_root_button.disabled = True
        self.cancel_button.disabled = True
        self.items_listview.visible = False
        self.progress_ring.visible = True
        self.modal = True
        self.update()

    def enable_interactions(self):
        """Enable user interactions after async operations complete."""
        self.select_here_button.disabled = False
        self.go_to_root_button.disabled = False
        self.cancel_button.disabled = False
        self.items_listview.visible = True
        self.progress_ring.visible = False
        self.modal = self.initially_modal  # Reset to initial modal state
        self.update()

    async def load_directory(self, directory_id: Optional[str]):
        """Load and display contents of a directory.

        Args:
            directory_id: ID of directory to load (None for root, "/" treated as None)
        """
        # Normalize "/" to None for consistent root handling
        if directory_id == "/":
            directory_id = None
        
        self.disable_interactions()

        try:
            # Request directory contents from server
            response = await do_request(
                action="list_directory",
                data={"folder_id": directory_id},
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if response.get("code") != 200:
                # Show error in dialog
                self.items_listview.controls = [
                    ft.Text(
                        _("Failed to load directory: {message}").format(
                            message=response.get("message", "Unknown error")
                        ),
                        color=ft.Colors.ERROR,
                    )
                ]
                self.enable_interactions()
                return

            data = response.get("data", {})
            directories = data.get("folders", [])
            documents = data.get("documents", [])
            parent_id = data.get("parent_id")  # Get parent_id from API response

            # Update current directory
            self.current_directory_id = directory_id

            # Check if we're at root (directory_id is None)
            is_root = directory_id is None
            
            # Track if we reached root
            self.reached_root = self.reached_root or is_root
            
            # Update go to root button visibility
            self.go_to_root_button.visible = not is_root

            # Update location text (breadcrumb) if enabled
            if self.show_breadcrumb:
                if is_root:
                    # At root - we know the complete path
                    location = "/"
                else:
                    # Build path from navigation stack
                    path_parts = [name for _, name in self.navigation_stack]

                    # Only show constructed path if we reached root
                    # Otherwise we don't have the full path from root
                    if path_parts and self.reached_root:
                        location = "/" + "/".join(path_parts)
                    else:
                        # Navigation stack is empty OR we didn't start from root
                        # We don't have enough info to show the complete path
                        # Show a more honest indicator
                        location = _("(current directory)")

                self.location_text.value = _("Current location: {path}").format(
                    path=location
                )

            # Clear and populate items list
            self.items_listview.controls.clear()

            # Add parent directory navigation if not at root
            # Use parent_id from API response to determine if parent exists
            if parent_id is not None:
                # Normalize "/" to None for consistency
                normalized_parent_id = None if parent_id == "/" else parent_id

                parent_button = ft.ListTile(
                    leading=ft.Icon(ft.Icons.ARROW_UPWARD, color=ft.Colors.ORANGE_400),
                    title=ft.Text(
                        _(".. (Parent Directory)"), weight=ft.FontWeight.BOLD
                    ),
                    on_click=lambda e, pid=normalized_parent_id: asyncio.create_task(
                        self.navigate_to_parent(pid)
                    ),
                    hover_color=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                )
                self.items_listview.controls.append(parent_button)

            # Add subdirectories (if mode allows)
            if self.mode in ("directories", "both"):
                for directory in directories:
                    dir_id = directory.get("id")
                    dir_name = directory.get("name", "Unnamed")

                    # Skip excluded directories
                    if dir_id in self.excluded_directory_ids:
                        continue

                    dir_tile = ft.ListTile(
                        leading=ft.Icon(ft.Icons.FOLDER, color=ft.Colors.BLUE_400),
                        title=ft.Text(dir_name),
                        on_click=lambda e, d_id=dir_id, d_name=dir_name: asyncio.create_task(
                            self.navigate_to_directory(d_id, d_name)
                        ),
                        hover_color=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                    )
                    self.items_listview.controls.append(dir_tile)

            # Add documents (if mode allows and filtered)
            if self.mode in ("files", "both"):
                for document in documents:
                    doc_id = document.get("id")
                    doc_title = document.get("title", "Unnamed")

                    # Apply file filter if provided
                    if self.file_filter and not self.file_filter(doc_title):
                        continue

                    doc_tile = ft.ListTile(
                        leading=ft.Icon(
                            ft.Icons.INSERT_DRIVE_FILE, color=ft.Colors.GREEN_400
                        ),
                        title=ft.Text(doc_title),
                        subtitle=ft.Text(
                            f"ID: {doc_id}", size=11, color=ft.Colors.GREY_500
                        ),
                        on_click=lambda e, d_id=doc_id, d_name=doc_title: self.select_file(
                            d_id, d_name
                        ),
                        hover_color=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                    )
                    self.items_listview.controls.append(doc_tile)

            # Show message if no items
            if len(self.items_listview.controls) == 0 or (
                len(self.items_listview.controls) == 1 and directory_id is not None
            ):
                message = self._get_empty_message()
                self.items_listview.controls.append(
                    ft.Text(
                        message,
                        color=ft.Colors.GREY_500,
                        italic=True,
                    )
                )

            self.enable_interactions()

        except Exception as e:
            # Show error
            self.items_listview.controls = [
                ft.Text(
                    _("Error loading directory: {error}").format(error=str(e)),
                    color=ft.Colors.ERROR,
                )
            ]
            self.enable_interactions()

    def _get_empty_message(self) -> str:
        """Get appropriate empty message based on mode."""
        if self.mode == "files":
            if self.file_filter:
                return _("No matching files found in this directory")
            return _("No files found in this directory")
        elif self.mode == "directories":
            return _("No subdirectories found in this directory")
        else:
            return _("This directory is empty")

    async def navigate_to_directory(self, directory_id: str, directory_name: str):
        """Navigate into a subdirectory.

        Args:
            directory_id: ID of directory to navigate to
            directory_name: Name of directory for breadcrumb
        """
        # Push current directory to stack
        self.navigation_stack.append((self.current_directory_id, directory_name))

        # Load new directory
        await self.load_directory(directory_id)

    async def navigate_to_parent(self, parent_id: Optional[str]):
        """Navigate to parent directory using parent_id from API.

        Args:
            parent_id: ID of the parent directory (None for root)
        """
        # If we have a navigation stack, pop from it to stay in sync
        if self.navigation_stack:
            self.navigation_stack.pop()

        # Load the parent directory
        await self.load_directory(parent_id)

    async def go_to_root_button_click(self, event):
        """Navigate to root directory."""
        self.navigation_stack.clear()
        await self.load_directory(None)

    def select_file(self, file_id: str, file_name: str):
        """Handle file selection.

        Args:
            file_id: ID of selected file
            file_name: Name of selected file
        """
        # Call callback with selected file
        if self.on_select_callback:
            self.on_select_callback(file_id, file_name, "file")

        # Set selection for async wait pattern
        self.selected_item_id = file_id
        self.selection_event.set()

        # Close dialog
        self.close()

    def select_here_button_click(self, event):
        """Handle select current directory button click."""
        # Call callback with current directory
        if self.on_select_callback:
            # Get current directory name from navigation stack
            dir_name = self.navigation_stack[-1][1] if self.navigation_stack else "Root"
            self.on_select_callback(self.current_directory_id, dir_name, "directory")

        # Set selection for async wait pattern
        self.selected_item_id = self.current_directory_id
        self.selection_event.set()

        # Close dialog
        self.close()

    def cancel_button_click(self, event):
        """Handle cancel button click."""
        # Signal cancellation
        self.selected_item_id = None
        self.selection_event.set()

        # Close dialog
        self.close()

    async def wait_for_selection(self) -> Optional[str]:
        """Wait for user to select an item or cancel.

        Returns:
            Selected item ID, or None if cancelled
        """
        await self.selection_event.wait()
        return self.selected_item_id
