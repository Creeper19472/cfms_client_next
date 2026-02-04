from typing import TYPE_CHECKING
import asyncio
from datetime import datetime
import logging

import flet as ft

from include.classes.shared import AppShared
from include.controllers.dialogs.directory import (
    CreateDirectoryDialogController,
    OpenDirectoryDialogController,
)
from include.ui.controls.dialogs.base import AlertDialog
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileManagerView

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext

logger = logging.getLogger(__name__)


class CreateDirectoryDialog(AlertDialog):
    def __init__(
        self,
        parent_manager: "FileManagerView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = CreateDirectoryDialogController(self)

        self.modal = False
        self.title = ft.Text(_("Create Directory"))

        self.parent_manager = parent_manager

        self.progress_ring = ft.ProgressRing(visible=False)

        self.directory_textfield = ft.TextField(
            label=_("Directory Name"),
            on_submit=self.ok_button_click,
            expand=True,
        )

        self.submit_button = ft.TextButton(
            _("Create"),
            on_click=self.ok_button_click,
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

        self.content = ft.Column(
            controls=[self.directory_textfield],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.progress_ring, self.submit_button, self.cancel_button]

    def disable_interactions(self):
        self.directory_textfield.disabled = True
        self.cancel_button.disabled = True
        self.submit_button.visible = False
        self.progress_ring.visible = True
        self.directory_textfield.error = None
        self.modal = True

    def enable_interactions(self):
        self.directory_textfield.disabled = False
        self.cancel_button.disabled = False
        self.submit_button.visible = True
        self.progress_ring.visible = False
        self.modal = False

    async def ok_button_click(
        self, event: ft.Event[ft.TextButton] | ft.Event[ft.TextField]
    ):
        yield self.disable_interactions()

        if not (directory_name := self.directory_textfield.value):
            self.directory_textfield.error = _("Directory name cannot be empty")
            yield self.enable_interactions()
            return

        self.page.run_task(self.controller.action_create_directory, directory_name)

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()


class BatchUploadFileAlertDialog(AlertDialog):
    def __init__(
        self,
        progress_column,
        stop_event: asyncio.Event,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = True
        self.title = ft.Text(_("Batch Upload"))

        self.stop_event = stop_event

        # Predefined buttons
        self.ok_button = ft.TextButton(
            content=_("OK"), on_click=self.ok_button_click, visible=False
        )
        self.cancel_button = ft.TextButton(
            content=_("Cancel"), on_click=self.cancel_button_click
        )

        self.content = ft.Column(
            controls=[progress_column],
            # spacing=15,
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [
            self.ok_button,
            self.cancel_button,
        ]

    async def ok_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        assert self.page
        self.cancel_button.disabled = True
        self.stop_event.set()
        yield


class UploadDirectoryAlertDialog(AlertDialog):
    def __init__(
        self,
        stop_event: asyncio.Event,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)

        self.modal = True
        self.scrollable = True
        self.title = ft.Text(_("Upload Directory"))

        self.stop_event = stop_event

        # Predefined buttons
        self.ok_button = ft.TextButton(
            content=_("OK"), on_click=self.ok_button_click, visible=False
        )
        self.cancel_button = ft.TextButton(
            content=_("Cancel"), on_click=self.cancel_button_click
        )

        # Component definitions
        self.progress_bar = ft.ProgressBar()
        self.progress_text = ft.Text(text_align=ft.TextAlign.CENTER)
        self.progress_column = ft.Column(
            [self.progress_bar, self.progress_text],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.error_column = ft.Column()

        self.content = ft.Column(
            [self.progress_column, self.error_column],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.ok_button, self.cancel_button]

    def finish_upload(self):
        self.ok_button.disabled = False
        self.cancel_button.disabled = True

    async def ok_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        assert self.page
        self.cancel_button.disabled = True
        self.stop_event.set()
        yield


class OpenDirectoryDialog(AlertDialog):
    def __init__(
        self,
        parent_manager: "FileManagerView",
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        self.page: ft.Page
        self.controller = OpenDirectoryDialogController(self)

        self.modal = False
        self.title = ft.Text(_("Jump to..."))

        self.parent_manager = parent_manager

        self.progress_ring = ft.ProgressRing(visible=False)

        self.directory_textfield = ft.TextField(
            label=_("Directory ID"),
            helper=_("If you want to go back to the root directory, enter '/'."),
            on_submit=self.ok_button_click,
            expand=True,
        )

        self.submit_button = ft.TextButton(
            _("Submit"),
            on_click=self.ok_button_click,
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"), on_click=self.cancel_button_click
        )

        self.content = ft.Column(
            controls=[self.directory_textfield],
            width=400,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.actions = [self.progress_ring, self.submit_button, self.cancel_button]

    def disable_interactions(self):
        self.directory_textfield.disabled = True
        self.cancel_button.disabled = True
        self.submit_button.visible = False
        self.progress_ring.visible = True
        self.directory_textfield.error = None
        self.modal = True
        self.update()

    def enable_interactions(self):
        self.directory_textfield.disabled = False
        self.cancel_button.disabled = False
        self.submit_button.visible = True
        self.progress_ring.visible = False
        self.modal = False
        self.update()

    async def ok_button_click(
        self, event: ft.Event[ft.TextButton] | ft.Event[ft.TextField]
    ):
        yield self.disable_interactions()

        if not (dir_id := self.directory_textfield.value):
            self.directory_textfield.error = _("Directory id cannot be empty")
            self.enable_interactions()
            return

        self.page.run_task(self.controller.action_open_directory, dir_id)

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.close()


class FileOverwriteConfirmDialog(AlertDialog):
    """Dialog to confirm overwriting an existing file on the server.

    Displays detailed information about the existing file including its size
    and last modified time. Information is loaded asynchronously after the
    dialog is shown.
    """

    def __init__(
        self,
        filename: str,
        existing_id: str,
        is_batch: bool = False,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible, scrollable=True)

        self.modal = True
        self.title = ft.Text(_("File Already Exists"))

        self.filename = filename
        self.existing_id = existing_id
        self.is_batch = is_batch
        self.user_choice = None  # Will be 'overwrite', 'skip', 'always_overwrite', 'always_skip', or None
        self.choice_event = asyncio.Event()
        self.app_shared = AppShared()

        # Create UI elements for document details
        self.progress_ring = ft.ProgressRing(
            visible=True,
            width=24,
            height=24,
        )

        # Container for document details with fade-in animation
        self.details_container_content = ft.Column(
            controls=[],
            spacing=8,
        )
        self.details_container = ft.Container(
            visible=False,
            animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
            opacity=0.0,
            content=self.details_container_content,
        )

        # Main message
        self.message_text = ft.Text(
            _('A file named "{filename}" already exists.').format(filename=filename),
            width=400,
            weight=ft.FontWeight.BOLD,
        )

        # Loading indicator row
        self.loading_row = ft.Row(
            controls=[
                self.progress_ring,
                ft.Text(_("Loading file details..."), italic=True),
            ],
            spacing=10,
        )

        # Dialog content
        self.content = ft.Column(
            controls=[
                self.message_text,
                ft.Container(height=10),
                self.loading_row,
                self.details_container,
                ft.Container(height=10),
                ft.Text(
                    _("Do you want to overwrite it?"),
                    width=400,
                ),
            ],
            width=400,
            spacing=10,
        )

        # Buttons
        self.overwrite_button = ft.TextButton(
            _("Overwrite"),
            on_click=self.overwrite_button_click,
        )
        self.skip_button = ft.TextButton(
            _("Skip"),
            on_click=self.skip_button_click,
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"),
            on_click=self.cancel_button_click,
        )

        # Additional buttons for batch uploads
        self.always_overwrite_button = ft.TextButton(
            _("Always Overwrite"),
            on_click=self.always_overwrite_button_click,
            visible=is_batch,
        )
        self.always_skip_button = ft.TextButton(
            _("Always Skip"),
            on_click=self.always_skip_button_click,
            visible=is_batch,
        )

        # Build actions list based on batch mode
        if is_batch:
            self.actions = [
                self.overwrite_button,
                self.always_overwrite_button,
                self.skip_button,
                self.always_skip_button,
                self.cancel_button,
            ]
        else:
            self.actions = [
                self.overwrite_button,
                self.skip_button,
                self.cancel_button,
            ]

    def did_mount(self):
        """Called when dialog is mounted to the page. Starts lazy loading."""
        super().did_mount()
        assert type(self.page) is ft.Page
        self.page.run_task(self.load_document_details)

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0 Byte"
        elif size_bytes < 1024:
            return f"{size_bytes} Bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes / 1024 / 1024:.2f} MB"

    async def load_document_details(self):
        """Load document details from server and update the UI."""

        def _row(icon, text, color=None, italic=False):
            return ft.Row(
                controls=[
                    ft.Icon(icon, size=16, color=color) if icon else ft.Container(),
                    ft.Text(text, size=14, italic=italic),
                ],
                spacing=8,
            )

        def _show_error(message):
            self.loading_row.visible = False
            self.details_container_content.controls = [
                _row(
                    ft.Icons.ERROR_OUTLINE,
                    message,
                    color=ft.Colors.RED_400,
                    italic=True,
                )
            ]
            self.details_container.visible = True
            self.update()

            self.details_container.opacity = 1.0
            self.update()

        try:
            response = await do_request(
                action="get_document_info",
                data={"document_id": self.existing_id},
                username=self.app_shared.username,
                token=self.app_shared.token,
            )

            if response.get("code") != 200:
                _show_error(_("Could not load file details"))
                return

            data = response.get("data", {})
            doc_size = data.get("size")
            last_modified = data.get("last_modified")
            created_time = data.get("created_time")

            details_controls = []

            if (
                doc_size is not None
                and isinstance(doc_size, (int, float))
                and doc_size >= 0
            ):
                details_controls.append(
                    _row(
                        ft.Icons.DESCRIPTION,
                        _("File size: {size}").format(
                            size=self.format_file_size(int(doc_size))
                        ),
                        color=ft.Colors.BLUE_400,
                    )
                )

            def _format_timestamp(ts):
                if ts is None:
                    return None
                try:
                    ts_float = float(ts)
                except Exception:
                    return None
                return datetime.fromtimestamp(ts_float).strftime("%Y-%m-%d %H:%M:%S")

            if (modified_str := _format_timestamp(last_modified)) is not None:
                details_controls.append(
                    _row(
                        ft.Icons.UPDATE,
                        _("Last modified: {date}").format(date=modified_str),
                        color=ft.Colors.ORANGE_400,
                    )
                )

            if (created_str := _format_timestamp(created_time)) is not None:
                details_controls.append(
                    _row(
                        ft.Icons.ACCESS_TIME,
                        _("Created: {date}").format(date=created_str),
                        color=ft.Colors.GREEN_400,
                    )
                )

            if not details_controls:
                _show_error(_("No details available"))
                return

            # Update UI: hide loader, set details, show container with fade-in
            self.details_container_content.controls = details_controls
            self.loading_row.visible = False
            self.details_container.visible = True
            self.update()

            self.details_container.opacity = 1.0
            self.update()

        except Exception as e:
            logger.exception(
                "Error loading document details for document_id=%s", self.existing_id
            )
            _show_error(_("Error loading file details"))

    async def overwrite_button_click(self, event: ft.Event[ft.TextButton]):
        self.user_choice = "overwrite"
        self.choice_event.set()
        self.close()

    async def skip_button_click(self, event: ft.Event[ft.TextButton]):
        self.user_choice = "skip"
        self.choice_event.set()
        self.close()

    async def always_overwrite_button_click(self, event: ft.Event[ft.TextButton]):
        self.user_choice = "always_overwrite"
        self.choice_event.set()
        self.close()

    async def always_skip_button_click(self, event: ft.Event[ft.TextButton]):
        self.user_choice = "always_skip"
        self.choice_event.set()
        self.close()

    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        self.user_choice = None
        self.choice_event.set()
        self.close()

    async def wait_for_choice(self) -> str | None:
        """Wait for the user to make a choice and return it."""
        await self.choice_event.wait()
        return self.user_choice


class BatchProgressDialog(AlertDialog):
    """Base dialog for showing progress of batch operations.
    
    Provides common UI elements and behavior for batch operations:
    - Progress bar
    - Progress text
    - Error column for displaying failed items
    - Cancel/OK button management
    """
    
    def __init__(
        self,
        title: str,
        with_cancel: bool = False,
        cancel_event: asyncio.Event | None = None,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        """Initialize batch progress dialog.
        
        Args:
            title: Dialog title
            with_cancel: Whether to show a cancel button
            cancel_event: Optional asyncio.Event to signal cancellation
            ref: Flet reference
            visible: Whether dialog is visible initially
        """
        super().__init__(ref=ref, visible=visible)
        
        self.modal = True
        self.scrollable = True
        self.title = ft.Text(title)
        
        self.cancel_event = cancel_event
        
        # Create UI components
        self.progress_bar = ft.ProgressBar(value=0)
        self.progress_text = ft.Text("", text_align=ft.TextAlign.CENTER)
        self.error_column = ft.Column([], scroll=ft.ScrollMode.AUTO)
        
        self.content = ft.Column(
            controls=[self.progress_bar, self.progress_text, self.error_column],
            width=400,
        )
        
        # Create buttons
        self.ok_button = ft.TextButton(_("OK"), on_click=self.ok_button_click, visible=False)
        
        if with_cancel:
            self.cancel_button = ft.TextButton(_("Cancel"), on_click=self.cancel_button_click)
            self.actions = [self.ok_button, self.cancel_button]
        else:
            self.cancel_button = None
            self.actions = [self.ok_button]
    
    def update_progress(self, current: int, total: int, text: str | None = None):
        """Update progress bar and text.
        
        Args:
            current: Number of items completed
            total: Total number of items
            text: Optional custom progress text
        """
        self.progress_bar.value = current / total if total > 0 else 0
        if text:
            self.progress_text.value = text
        self.progress_bar.update()
        self.progress_text.update()
    
    def add_error(self, error_text: str):
        """Add an error message to the error column.
        
        Args:
            error_text: Error message to display
        """
        error_control = ft.Text(error_text)
        self.error_column.controls.append(error_control)
        self.error_column.update()
    
    def show_completion(self, has_errors: bool):
        """Show completion state of the operation.
        
        Args:
            has_errors: Whether any errors occurred
        """
        if has_errors:
            self.ok_button.visible = True
            if self.cancel_button:
                self.cancel_button.disabled = True
            self.update()
        else:
            self.close()
    
    async def ok_button_click(self, event: ft.Event[ft.TextButton]):
        """Handle OK button click."""
        self.close()
    
    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        """Handle cancel button click."""
        if self.cancel_event:
            self.cancel_event.set()
        if self.cancel_button:
            self.cancel_button.disabled = True
        yield


class BatchDeleteConfirmDialog(AlertDialog):
    """Dialog to confirm batch deletion of files and directories."""
    
    def __init__(
        self,
        file_count: int,
        directory_count: int,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible)
        
        self.scrollable = True
        self.title = ft.Text(_("Confirm Delete"))
        
        self.file_count = file_count
        self.directory_count = directory_count
        self.user_confirmed = False
        self.choice_event = asyncio.Event()
        
        # Build confirmation message
        total_count = file_count + directory_count
        if file_count > 0 and directory_count > 0:
            message = _("Delete {count} items ({file_count} files, {dir_count} directories)?").format(
                count=total_count,
                file_count=file_count,
                dir_count=directory_count
            )
        elif file_count > 0:
            message = _("Delete {count} file(s)?").format(count=file_count)
        else:
            message = _("Delete {count} directory(ies)?").format(count=directory_count)
        
        self.content = ft.Column(
            controls=[
                ft.Text(message, size=16),
                ft.Text(
                    _("This action cannot be undone."),
                    weight=ft.FontWeight.BOLD,
                    align=ft.Alignment.CENTER,
                ),
            ],
            width=400,
        )
        
        self.delete_button = ft.TextButton(
            _("Delete"),
            on_click=self.delete_button_click,
        )
        self.cancel_button = ft.TextButton(
            _("Cancel"),
            on_click=self.cancel_button_click,
        )
        
        self.actions = [self.delete_button, self.cancel_button]
    
    async def delete_button_click(self, event: ft.Event[ft.TextButton]):
        """Handle delete button click."""
        self.user_confirmed = True
        self.choice_event.set()
        self.close()
    
    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        """Handle cancel button click."""
        self.user_confirmed = False
        self.choice_event.set()
        self.close()
    
    async def wait_for_confirmation(self) -> bool:
        """Wait for the user to confirm or cancel."""
        await self.choice_event.wait()
        return self.user_confirmed


class DirectorySelectorDialog(AlertDialog):
    """Dialog for selecting a target directory for batch move operations.
    
    Provides a browsable directory tree interface for selecting a target location.
    """
    
    def __init__(
        self,
        file_listview: "FileManagerView",
        excluded_directory_ids: list[str] | None = None,
        ref: ft.Ref | None = None,
        visible=True,
    ):
        """Initialize directory selector dialog.
        
        Args:
            file_listview: The file manager view
            excluded_directory_ids: List of directory IDs to exclude from selection (e.g., items being moved)
            ref: Flet reference
            visible: Whether dialog is visible initially
        """
        super().__init__(ref=ref, visible=visible)
        
        self.file_listview = file_listview
        self.excluded_directory_ids = excluded_directory_ids or []
        self.app_shared = AppShared()
        
        # Current navigation state
        self.current_directory_id: str | None = file_listview.current_directory_id
        self.navigation_stack: list[tuple[str | None, str]] = []  # [(dir_id, dir_name)]
        
        # User selection
        self.selected_directory_id: str | None = None
        self.selection_event = asyncio.Event()
        
        self.modal = True  # Prevent interaction with main UI during selection
        self.title = ft.Text(_("Select Target Directory"))
        
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
        self.select_here_button = ft.Button(
            _("Select Here"),
            icon=ft.Icons.CHECK_CIRCLE,
            on_click=self.select_here_button_click,
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
            self.select_here_button,
            self.go_to_root_button,
            self.cancel_button,
        ]
    
    def did_mount(self):
        """Called when dialog is mounted to the page. Loads initial directory."""
        super().did_mount()
        asyncio.create_task(self.load_directory(self.current_directory_id))
    
    def disable_interactions(self):
        """Disable user interactions during async operations."""
        self.select_here_button.disabled = True
        self.go_to_root_button.disabled = True
        self.cancel_button.disabled = True
        self.folder_listview.visible = False
        self.progress_ring.visible = True
        self.modal = True
        self.update()
    
    def enable_interactions(self):
        """Enable user interactions after async operations complete."""
        self.select_here_button.disabled = False
        self.go_to_root_button.disabled = False
        self.cancel_button.disabled = False
        self.folder_listview.visible = True
        self.progress_ring.visible = False
        self.modal = False
        self.update()
    
    def update_button_visibility(self):
        """Update button visibility based on current state."""
        # Go to Root button: visible if not at root (root is represented as None)
        self.go_to_root_button.visible = self.current_directory_id is not None
        self.update()
    
    def update_location_text(self, path: str = "/"):
        """Update the breadcrumb location indicator."""
        self.location_text.value = _("Current location: {path}").format(path=path)
        self.update()
    
    def build_breadcrumb_path(self) -> str:
        """Build a human-readable path from the navigation stack."""
        if not self.navigation_stack:
            return "/"
        return "/" + "/".join(name for _, name in self.navigation_stack)
    
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
                self.send_error(
                    _("Failed to load directory: ({code}) {message}").format(
                        code=code, message=response["message"]
                    )
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
                    title=ft.Text(_(".. (Parent Directory)"), weight=ft.FontWeight.BOLD),
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
                    
                    # Skip excluded directories
                    if folder_id in self.excluded_directory_ids:
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
            self.send_error(
                _("Error loading directory: {error}").format(error=str(e))
            )
            self.close()
    
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
            parent_id: ID of the parent directory (None for root, "/" is converted to None)
        """
        if self.navigation_stack:
            self.navigation_stack.pop()
        # Normalize "/" to None for consistency
        await self.load_directory(None if parent_id == "/" else parent_id)
    
    async def go_to_root_button_click(self, event: ft.Event[ft.TextButton]):
        """Navigate to the root directory."""
        self.navigation_stack.clear()
        await self.load_directory(None)
    
    async def select_here_button_click(self, event: ft.Event[ft.Button]):
        """Select the current directory as the target."""
        self.selected_directory_id = self.current_directory_id
        self.selection_event.set()
        self.close()
    
    async def cancel_button_click(self, event: ft.Event[ft.TextButton]):
        """Close the dialog without selecting."""
        self.selected_directory_id = None
        self.selection_event.set()
        self.close()
    
    async def wait_for_selection(self) -> str | None:
        """Wait for the user to select a directory or cancel.
        
        Returns:
            The selected directory ID, or None if cancelled
        """
        await self.selection_event.wait()
        return self.selected_directory_id
