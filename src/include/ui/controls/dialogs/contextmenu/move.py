import copy
from typing import TYPE_CHECKING
import asyncio

import flet as ft

from include.classes.config import AppShared
from include.ui.controls.dialogs.base import AlertDialog
from include.ui.util.notifications import send_error, send_success
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileListView

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


class MoveDialog(AlertDialog):
    """Dialog for moving documents and directories to a different location.

    This dialog provides a browsable directory tree interface that allows users
    to navigate through the directory hierarchy and select a target location
    for moving the selected object.
    """

    def __init__(
        self,
        object_type: str,
        object_id: str,
        file_listview: "FileListView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.object_type = object_type
        self.object_id = object_id
        self.file_listview = file_listview
        self.app_shared = AppShared()

        # Current navigation state
        self.current_directory_id: str | None = (
            file_listview.parent_manager.current_directory_id
        )
        self.original_parent_id: str | None = copy.deepcopy(self.current_directory_id)
        self.navigation_stack: list[tuple[str | None, str]] = []  # [(dir_id, dir_name)]

        # Set display name based on object type
        match self.object_type:
            case "document":
                self.object_display_name = _("Document")
            case "directory":
                self.object_display_name = _("Directory")
            case _:
                raise ValueError(f"Invalid object_type: {self.object_type}")

        self.modal = False
        self.title = ft.Text(
            _("Move {display_name}").format(display_name=self.object_display_name)
        )

        # Progress indicator
        self.progress_ring = ft.ProgressRing(visible=True, width=32, height=32)

        # Current location indicator (breadcrumb)
        self.location_text = ft.Text(
            _("Current location: /"),
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_400,
        )

        # Folder list view
        self.folder_listview = ft.ListView(
            visible=False,
            expand=True,
            expand_loose=True,
            spacing=5,
            padding=10,
        )

        # Action buttons
        self.move_here_button = ft.Button(
            _("Move Here"),
            icon=ft.Icons.CHECK_CIRCLE,
            on_click=self.move_here_button_click,
            visible=False,
        )

        self.go_to_root_button = ft.TextButton(
            _("Go to Root"),
            icon=ft.Icons.HOME,
            on_click=self.go_to_root_button_click,
            visible=False,
        )

        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

        # Content layout
        self.content = ft.Column(
            controls=[
                self.location_text,
                ft.Divider(),
                self.progress_ring,
                self.folder_listview,
            ],
            width=550,
            height=400,
            spacing=10,
        )

        self.actions = [
            self.move_here_button,
            self.go_to_root_button,
            self.cancel_button,
        ]

    def did_mount(self):
        """Called when dialog is mounted to the page. Loads initial directory."""
        super().did_mount()
        asyncio.create_task(self.load_directory(self.current_directory_id))

    def disable_interactions(self):
        """Disable user interactions during async operations."""
        self.move_here_button.disabled = True
        self.go_to_root_button.disabled = True
        self.cancel_button.disabled = True
        self.folder_listview.visible = False
        self.progress_ring.visible = True
        self.modal = True
        self.update()

    def enable_interactions(self):
        """Enable user interactions after async operations complete."""
        self.move_here_button.disabled = False
        self.go_to_root_button.disabled = False
        self.cancel_button.disabled = False
        self.folder_listview.visible = True
        self.progress_ring.visible = False
        self.modal = False
        self.update()

    def update_button_visibility(self):
        """Update button visibility based on current state.
        
        - Move Here button: visible when current directory differs from original
        - Go to Root button: visible when not in root directory
        """
        
        # Move Here button: visible if current location differs from original
        self.move_here_button.visible = (self.current_directory_id != self.original_parent_id)
        
        # Go to Root button: visible if not at root
        self.go_to_root_button.visible = self.current_directory_id not in (None, "/")
        
        self.update()

    def update_location_text(self, path: str = "/"):
        """Update the breadcrumb location indicator."""
        self.location_text.value = _("Current location: {path}").format(path=path)
        self.update()

    async def load_directory(self, directory_id: str | None):
        """Load and display folders in the specified directory.

        Args:
            directory_id: The ID of the directory to load, or None for root
        """
        self.disable_interactions()

        try:
            response = await do_request(
                action="list_directory",
                data={"folder_id": directory_id},
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if (code := response["code"]) != 200:
                send_error(
                    self.page,
                    _("Failed to load directory: ({code}) {message}").format(
                        code=code, message=response["message"]
                    ),
                )
                self.close()
                return

            data = response["data"]
            folders = data.get("folders", [])
            parent_id = data.get("parent_id")

            # Update current directory
            self.current_directory_id = directory_id

            # Build breadcrumb path
            path = self.build_breadcrumb_path()
            self.update_location_text(path)

            # Clear and populate folder list
            self.folder_listview.controls.clear()

            # Add parent directory option if not at root
            if parent_id is not None:
                parent_item = ft.ListTile(
                    leading=ft.Icon(ft.Icons.ARROW_UPWARD, color=ft.Colors.ORANGE_400),
                    title=ft.Text(
                        _(".. (Parent Directory)"), weight=ft.FontWeight.BOLD
                    ),
                    on_click=lambda _: asyncio.create_task(
                        self.navigate_to_parent(parent_id)
                    ),
                    hover_color=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                )
                self.folder_listview.controls.append(parent_item)

            # Add folders
            if not folders:
                # Show message if no subfolders
                empty_message = ft.Container(
                    content=ft.Text(
                        _("No subfolders available"),
                        color=ft.Colors.GREY_500,
                        italic=True,
                    ),
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                )
                self.folder_listview.controls.append(empty_message)
            else:
                for folder in folders:
                    folder_id = folder["id"]
                    folder_name = folder["name"]

                    # Skip the folder we're trying to move (can't move into itself)
                    if self.object_type == "directory" and folder_id == self.object_id:
                        continue

                    folder_item = ft.ListTile(
                        leading=ft.Icon(ft.Icons.FOLDER, color=ft.Colors.BLUE_400),
                        title=ft.Text(folder_name),
                        on_click=lambda _, fid=folder_id, fname=folder_name: asyncio.create_task(
                            self.navigate_to_folder(fid, fname)
                        ),
                        hover_color=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                    )
                    self.folder_listview.controls.append(folder_item)

            self.enable_interactions()
            self.update_button_visibility()

        except Exception as e:
            send_error(
                self.page,
                _("Error loading directory: {error}").format(error=str(e)),
            )
            self.close()

    def build_breadcrumb_path(self) -> str:
        """Build a human-readable path from the navigation stack."""
        if not self.navigation_stack:
            return "/"
        return "/" + "/".join(name for _, name in self.navigation_stack)

    async def navigate_to_folder(self, folder_id: str, folder_name: str):
        """Navigate into a subfolder.

        Args:
            folder_id: ID of the folder to navigate to
            folder_name: Name of the folder (for breadcrumb)
        """
        self.navigation_stack.append((folder_id, folder_name))
        await self.load_directory(folder_id)

    async def navigate_to_parent(self, parent_id: str | None):
        """Navigate to the parent directory.

        Args:
            parent_id: ID of the parent directory
        """
        if self.navigation_stack:
            self.navigation_stack.pop()
        await self.load_directory(parent_id if parent_id != "/" else None)

    async def go_to_root_button_click(self, event: ft.Event[ft.TextButton]):
        """Navigate to the root directory."""
        self.navigation_stack.clear()
        await self.load_directory(None)

    async def move_here_button_click(self, event: ft.Event[ft.Button]):
        """Move the object to the current directory."""
        yield self.disable_interactions()
        
        # Perform the move operation
        try:
            if self.object_type == "document":
                action = "move_document"
                data = {
                    "document_id": self.object_id,
                    "target_folder_id": self.current_directory_id,
                }
            elif self.object_type == "directory":
                action = "move_directory"
                data = {
                    "folder_id": self.object_id,
                    "target_folder_id": self.current_directory_id,
                }
            else:
                raise ValueError(f"Invalid object_type: {self.object_type}")

            response = await do_request(
                action=action,
                data=data,
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if (code := response["code"]) != 200:
                send_error(
                    self.page,
                    _("Move failed: ({code}) {message}").format(
                        code=code, message=response["message"]
                    ),
                )
                self.enable_interactions()
            else:
                send_success(
                    self.page,
                    _("{display_name} moved successfully").format(
                        display_name=self.object_display_name
                    ),
                )
                # Refresh the file list view
                from include.ui.util.path import get_directory

                await get_directory(
                    self.file_listview.parent_manager.current_directory_id,
                    self.file_listview,
                )
                self.close()

        except Exception as e:
            send_error(
                self.page,
                _("Error moving {display_name}: {error}").format(
                    display_name=self.object_display_name.lower(), error=str(e)
                ),
            )
            self.enable_interactions()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        """Close the dialog without moving."""
        self.close()
