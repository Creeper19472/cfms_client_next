from typing import TYPE_CHECKING
import asyncio
from datetime import datetime

import flet as ft

from include.classes.config import AppShared
from include.controllers.dialogs.directory import (
    CreateDirectoryDialogController,
    OpenDirectoryDialogController,
)
from include.ui.controls.dialogs.base import AlertDialog
from include.ui.util.notifications import send_error
from include.util.requests import do_request

if TYPE_CHECKING:
    from include.ui.controls.views.explorer import FileManagerView

from include.util.locale import get_translation

t = get_translation()
_ = t.gettext


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
        ref: ft.Ref | None = None,
        visible=True,
    ):
        super().__init__(ref=ref, visible=visible, scrollable=True)
        
        self.modal = True
        self.title = ft.Text(_("File Already Exists"))
        
        self.filename = filename
        self.existing_id = existing_id
        self.user_choice = None  # Will be 'overwrite', 'skip', or None
        self.choice_event = asyncio.Event()
        self.app_shared = AppShared()
        
        # Create UI elements for document details
        self.progress_ring = ft.ProgressRing(
            visible=True,
            width=24,
            height=24,
        )
        
        # Container for document details with fade-in animation
        self.details_container = ft.Container(
            visible=False,
            opacity=0,
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            content=ft.Column(
                controls=[],
                spacing=8,
            ),
        )
        
        # Main message
        self.message_text = ft.Text(
            _('A file named "{filename}" already exists.').format(
                filename=filename
            ),
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
        
        self.actions = [
            self.overwrite_button,
            self.skip_button,
            self.cancel_button,
        ]
    
    def did_mount(self):
        """Called when dialog is mounted to the page. Starts lazy loading."""
        super().did_mount()
        asyncio.create_task(self._load_document_details_task())
    
    async def _load_document_details_task(self):
        """Task wrapper for loading document details."""
        async for _ in self.load_document_details():
            pass
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0 Bytes"
        elif size_bytes < 1024:
            return f"{size_bytes} Bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes / 1024 / 1024:.2f} MB"
    
    async def load_document_details(self):
        """Load document details from server and update the UI."""
        try:
            # Request document info from server
            response = await do_request(
                action="get_document_info",
                data={
                    "document_id": self.existing_id,
                },
                username=self.app_shared.username,
                token=self.app_shared.token,
            )
            
            if response.get("code") == 200:
                data = response.get("data", {})
                
                # Extract document details
                doc_size = data.get("size", 0)
                last_modified = data.get("last_modified")
                created_time = data.get("created_time")
                
                # Build details controls
                details_controls = []
                
                # File size
                if doc_size is not None and doc_size >= 0:
                    details_controls.append(
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.DESCRIPTION, size=16, color=ft.Colors.BLUE_400),
                                ft.Text(
                                    _("File size: {size}").format(size=self.format_file_size(doc_size)),
                                    size=14,
                                ),
                            ],
                            spacing=8,
                        )
                    )
                
                # Last modified date
                if last_modified is not None:
                    modified_str = datetime.fromtimestamp(last_modified).strftime("%Y-%m-%d %H:%M:%S")
                    details_controls.append(
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.UPDATE, size=16, color=ft.Colors.ORANGE_400),
                                ft.Text(
                                    _("Last modified: {date}").format(date=modified_str),
                                    size=14,
                                ),
                            ],
                            spacing=8,
                        )
                    )
                
                # Created date
                if created_time is not None:
                    created_str = datetime.fromtimestamp(created_time).strftime("%Y-%m-%d %H:%M:%S")
                    details_controls.append(
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.ACCESS_TIME, size=16, color=ft.Colors.GREEN_400),
                                ft.Text(
                                    _("Created: {date}").format(date=created_str),
                                    size=14,
                                ),
                            ],
                            spacing=8,
                        )
                    )
                
                # Update the details container
                self.details_container.content.controls = details_controls
                
                # Hide loading indicator
                self.loading_row.visible = False
                
                # Show details with fade-in animation
                self.details_container.visible = True
                yield
                
                # Trigger animation by changing opacity
                self.details_container.opacity = 1
                yield
                
            else:
                # Failed to fetch details, show error message
                self.loading_row.visible = False
                self.details_container.content.controls = [
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ERROR_OUTLINE, size=16, color=ft.Colors.RED_400),
                            ft.Text(
                                _("Could not load file details"),
                                size=14,
                                italic=True,
                                color=ft.Colors.RED_400,
                            ),
                        ],
                        spacing=8,
                    )
                ]
                self.details_container.visible = True
                self.details_container.opacity = 1
                yield
                
        except Exception as e:
            # Handle any errors during loading
            self.loading_row.visible = False
            self.details_container.content.controls = [
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=16, color=ft.Colors.RED_400),
                        ft.Text(
                            _("Error loading file details"),
                            size=14,
                            italic=True,
                            color=ft.Colors.RED_400,
                        ),
                    ],
                    spacing=8,
                )
            ]
            self.details_container.visible = True
            self.details_container.opacity = 1
            yield
    
    async def overwrite_button_click(self, event: ft.Event[ft.TextButton]):
        self.user_choice = 'overwrite'
        self.choice_event.set()
        self.close()
    
    async def skip_button_click(self, event: ft.Event[ft.TextButton]):
        self.user_choice = 'skip'
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
