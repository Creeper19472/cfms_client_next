from typing import TYPE_CHECKING
import asyncio
from datetime import datetime
import logging

import flet as ft

from include.classes.config import AppShared
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
