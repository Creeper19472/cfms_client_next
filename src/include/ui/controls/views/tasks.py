"""Tasks view for displaying and managing download tasks."""

from typing import TYPE_CHECKING, Optional, cast
import os
import flet as ft

from include.classes.shared import AppShared
from include.classes.datacls import DownloadTask, DownloadTaskStatus
from include.classes.services.download import DownloadManagerService
from include.util.locale import get_translation
from include.ui.util.notifications import send_error

if TYPE_CHECKING:
    from include.ui.models.home import HomeModel

t = get_translation()
_ = t.gettext


class TaskTile(ft.Card):
    """
    UI component representing a single download task.

    Displays task information including filename, progress, status, and controls.
    """

    def __init__(self, task: DownloadTask, parent_view: "TasksView"):
        super().__init__()
        self.task = task
        self.parent_view = parent_view

        # Check if file exists for completed tasks
        self.file_exists = True
        if task.status == DownloadTaskStatus.COMPLETED:
            self.file_exists = os.path.exists(task.file_path)

        # Create progress bar
        self.progress_bar = ft.ProgressBar(
            value=task.progress,
            bar_height=4,
        )

        # Create status text
        self.status_text = ft.Text(
            value=self._get_status_text(),
            size=12,
            color=self._get_status_color(),
        )

        # Create progress info text
        self.progress_info = ft.Text(
            value=self._get_progress_info(),
            size=11,
            color=ft.Colors.GREY_400,
        )

        # Create control buttons
        # Open file button (only visible for completed tasks)

        self.open_file_button = ft.IconButton(
            icon=ft.Icons.OPEN_IN_NEW,
            icon_size=16,
            tooltip=_("Open file"),
            on_click=self._on_open_file,
            visible=task.status == DownloadTaskStatus.COMPLETED and self.file_exists,
        )

        # Delete file button (only visible for completed tasks)
        self.delete_file_button = ft.IconButton(
            icon=ft.Icons.DELETE,
            icon_size=16,
            tooltip=_("Delete file and task"),
            on_click=self._on_delete_file,
            visible=task.status == DownloadTaskStatus.COMPLETED,
        )

        # Pause/Resume button (only if server supports resume)
        # If resume not supported, only show cancel button
        self.pause_resume_button = ft.IconButton(
            icon=(
                ft.Icons.PAUSE
                if task.status == DownloadTaskStatus.DOWNLOADING
                else ft.Icons.PLAY_ARROW
            ),
            icon_size=16,
            tooltip=(
                _("Pause")
                if task.status == DownloadTaskStatus.DOWNLOADING
                else _("Resume")
            ),
            on_click=self._on_pause_resume,
            visible=(
                task.supports_resume
                and task.status
                in [
                    DownloadTaskStatus.DOWNLOADING,
                    DownloadTaskStatus.PAUSED,
                    DownloadTaskStatus.PENDING,
                ]
            ),
        )

        # Cancel button
        # If resume not supported, show for downloading tasks too
        self.cancel_button = ft.IconButton(
            icon=ft.Icons.CANCEL,
            icon_size=16,
            tooltip=_("Cancel"),
            on_click=self._on_cancel,
            visible=task.status
            in [
                DownloadTaskStatus.PENDING,
                DownloadTaskStatus.DOWNLOADING,
                DownloadTaskStatus.DECRYPTING,
                DownloadTaskStatus.VERIFYING,
                DownloadTaskStatus.PAUSED,
                DownloadTaskStatus.SCHEDULED,
            ],
        )

        # Priority badge
        self.priority_badge_text = ft.Text(
            value=f"P{task.priority}",
            size=10,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
        )
        self.priority_badge = ft.Container(
            content=self.priority_badge_text,
            bgcolor=ft.Colors.ORANGE if task.priority > 0 else ft.Colors.GREY,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            border_radius=10,
            visible=task.priority != 0,
        )

        # Status icon and color
        self.status_icon = ft.Icon(
            icon=self._get_status_icondata(),
            size=20,
            color=self._get_status_color(),
        )

        # File missing warning badge (only for completed tasks where file is missing)
        self.file_missing_badge = ft.Container(
            content=ft.Text(
                value=_("File missing"),
                size=10,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
            ),
            bgcolor=ft.Colors.GREY,
            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            border_radius=10,
            visible=task.status == DownloadTaskStatus.COMPLETED
            and not self.file_exists,
        )

        # Set progress bar visibility
        self.progress_bar.visible = task.status not in [
            DownloadTaskStatus.COMPLETED,
            DownloadTaskStatus.FAILED,
            DownloadTaskStatus.CANCELLED,
        ]

        # Build the tile
        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.status_icon,
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(
                                                value=task.filename,
                                                size=14,
                                                weight=ft.FontWeight.BOLD,
                                                overflow=ft.TextOverflow.ELLIPSIS,
                                            ),
                                            self.priority_badge,
                                            self.file_missing_badge,
                                        ],
                                        spacing=5,
                                    ),
                                    self.status_text,
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            self.open_file_button,
                            self.delete_file_button,
                            self.pause_resume_button,
                            self.cancel_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.progress_bar,
                    self.progress_info,
                ],
                spacing=5,
                expand=True,
                expand_loose=True,
            ),
            padding=10,
        )

    def _get_status_icondata(self) -> ft.IconData:
        """Get icon based on task status."""
        status_icons = {
            DownloadTaskStatus.PENDING: ft.Icons.SCHEDULE,
            DownloadTaskStatus.DOWNLOADING: ft.Icons.DOWNLOAD,
            DownloadTaskStatus.PAUSED: ft.Icons.PAUSE_CIRCLE,
            DownloadTaskStatus.DECRYPTING: ft.Icons.LOCK_OPEN,
            DownloadTaskStatus.VERIFYING: ft.Icons.VERIFIED,
            DownloadTaskStatus.COMPLETED: ft.Icons.CHECK_CIRCLE,
            DownloadTaskStatus.FAILED: ft.Icons.ERROR,
            DownloadTaskStatus.CANCELLED: ft.Icons.CANCEL,
            DownloadTaskStatus.SCHEDULED: ft.Icons.ACCESS_TIME,
        }
        return status_icons.get(self.task.status, ft.Icons.HELP)

    def _get_status_color(self) -> str:
        """Get color based on task status."""
        status_colors = {
            DownloadTaskStatus.PENDING: ft.Colors.GREY,
            DownloadTaskStatus.DOWNLOADING: ft.Colors.BLUE,
            DownloadTaskStatus.PAUSED: ft.Colors.YELLOW,
            DownloadTaskStatus.DECRYPTING: ft.Colors.ORANGE,
            DownloadTaskStatus.VERIFYING: ft.Colors.PURPLE,
            DownloadTaskStatus.COMPLETED: ft.Colors.GREEN,
            DownloadTaskStatus.FAILED: ft.Colors.RED,
            DownloadTaskStatus.CANCELLED: ft.Colors.GREY,
            DownloadTaskStatus.SCHEDULED: ft.Colors.CYAN,
        }
        # Only override the completed status color when the file is missing.
        if self.task.status == DownloadTaskStatus.COMPLETED and not self.file_exists:
            return ft.Colors.GREY

        return status_colors.get(self.task.status, ft.Colors.WHITE)

    def _get_status_text(self) -> str:
        """Get status text based on task status."""
        status_texts = {
            DownloadTaskStatus.PENDING: _("Pending"),
            DownloadTaskStatus.DOWNLOADING: _("Downloading"),
            DownloadTaskStatus.PAUSED: _("Paused"),
            DownloadTaskStatus.DECRYPTING: _("Decrypting"),
            DownloadTaskStatus.VERIFYING: _("Verifying"),
            DownloadTaskStatus.COMPLETED: _("Completed"),
            DownloadTaskStatus.FAILED: _("Failed"),
            DownloadTaskStatus.CANCELLED: _("Cancelled"),
            DownloadTaskStatus.SCHEDULED: _("Scheduled"),
        }
        status_text = status_texts.get(self.task.status, _("Unknown"))

        if self.task.status == DownloadTaskStatus.FAILED and self.task.error:
            status_text += f": {self.task.error}"
        elif (
            self.task.retry_count > 0 and self.task.status == DownloadTaskStatus.PENDING
        ):
            status_text += f" (Retry {self.task.retry_count}/{self.task.max_retries})"

        return status_text

    def _get_progress_info(self) -> str:
        """Get progress information text."""
        if self.task.status == DownloadTaskStatus.COMPLETED:
            return _("Download completed")
        elif self.task.status in [
            DownloadTaskStatus.FAILED,
            DownloadTaskStatus.CANCELLED,
        ]:
            return ""
        elif self.task.total_bytes > 0:
            current_mb = self.task.current_bytes / 1024 / 1024
            total_mb = self.task.total_bytes / 1024 / 1024
            percentage = self.task.progress * 100
            return f"{current_mb:.2f} MB / {total_mb:.2f} MB ({percentage:.1f}%)"
        elif self.task.progress > 0:
            percentage = self.task.progress * 100
            return f"{percentage:.1f}%"
        else:
            return _("Waiting to start...")

    def update_task(self, task: DownloadTask):
        """Update the tile with new task data."""
        self.task = task

        # Check file existence for completed tasks
        if task.status == DownloadTaskStatus.COMPLETED:
            self.file_exists = os.path.exists(task.file_path)
        else:
            self.file_exists = True

        # Update status icon
        self.status_icon.icon = self._get_status_icondata()
        self.status_icon.color = self._get_status_color()

        # Update progress bar
        self.progress_bar.value = task.progress
        self.progress_bar.visible = task.status not in [
            DownloadTaskStatus.COMPLETED,
            DownloadTaskStatus.FAILED,
            DownloadTaskStatus.CANCELLED,
        ]

        # Update status text
        self.status_text.value = self._get_status_text()
        self.status_text.color = self._get_status_color()

        # Update progress info
        self.progress_info.value = self._get_progress_info()

        # Update priority badge
        self.priority_badge.visible = task.priority != 0
        self.priority_badge_text = f"P{task.priority}"
        self.priority_badge.bgcolor = (
            ft.Colors.ORANGE if task.priority > 0 else ft.Colors.GREY
        )

        # Update file missing badge
        self.file_missing_badge.visible = (
            task.status == DownloadTaskStatus.COMPLETED and not self.file_exists
        )

        # Update open file button visibility (only if file exists)
        self.open_file_button.visible = (
            task.status == DownloadTaskStatus.COMPLETED and self.file_exists
        )
        # self.open_file_button.disabled = not AppShared().is_mobile

        # Update delete file button visibility (always visible for completed tasks)
        self.delete_file_button.visible = task.status == DownloadTaskStatus.COMPLETED

        # Update pause/resume button visibility and icons (only if supports_resume)
        self.pause_resume_button.visible = task.supports_resume and task.status in [
            DownloadTaskStatus.DOWNLOADING,
            DownloadTaskStatus.PAUSED,
            DownloadTaskStatus.PENDING,
        ]
        self.pause_resume_button.icon = (
            ft.Icons.PAUSE
            if task.status == DownloadTaskStatus.DOWNLOADING
            else ft.Icons.PLAY_ARROW
        )
        self.pause_resume_button.tooltip = (
            _("Pause") if task.status == DownloadTaskStatus.DOWNLOADING else _("Resume")
        )

        self.cancel_button.visible = task.status in [
            DownloadTaskStatus.PENDING,
            DownloadTaskStatus.DOWNLOADING,
            DownloadTaskStatus.DECRYPTING,
            DownloadTaskStatus.VERIFYING,
            DownloadTaskStatus.PAUSED,
            DownloadTaskStatus.SCHEDULED,
        ]

        # Update the UI
        self.update()

    async def _on_pause_resume(self, e):
        """Handle pause/resume button click."""
        download_service = self.parent_view.download_service
        if download_service:
            if self.task.status == DownloadTaskStatus.DOWNLOADING:
                download_service.pause_task(self.task.task_id)
            elif self.task.status == DownloadTaskStatus.PAUSED:
                download_service.resume_task(self.task.task_id)

    async def _on_cancel(self, e):
        """Handle cancel button click."""
        download_service = self.parent_view.download_service
        if download_service:
            download_service.cancel_task(self.task.task_id)

    async def _on_open_file(self, e):
        """Handle open file button click."""
        assert type(self.page) == ft.Page
        assert self.page.platform

        # Check if file exists before attempting to open
        if not os.path.exists(self.task.file_path):
            # Update the UI to reflect that file is missing
            self.file_exists = False
            self.update_task(self.task)
            return

        try:
            if AppShared().is_mobile:
                # Import OpenFile service
                from flet_open_file import OpenFile

                # Open the downloaded file
                open_file_service = OpenFile()
                await open_file_service.open(self.task.file_path, 3)

            elif self.page.platform.value == "windows":
                os.startfile(self.task.file_path)

            else:
                raise NotImplementedError("Open file not supported on this platform")

        except Exception as exc:
            # Show error if file can't be opened
            send_error(
                self.page, _("Failed to open file: {error}").format(error=str(exc))
            )

    async def _on_delete_file(self, e):
        """Handle delete file button click."""
        download_service = self.parent_view.download_service
        if not download_service:
            return

        # Delete the task and file without confirmation
        success, error_msg = await download_service.delete_task_with_file(
            self.task.task_id
        )

        if success:
            # Refresh the task list to remove the deleted task
            self.parent_view._refresh_tasks()
        else:
            # Show error message
            if self.page and error_msg:
                send_error(
                    self.page,
                    _("Failed to delete: {error}").format(error=error_msg),
                )


class TasksView(ft.Container):
    """
    Main view for displaying and managing download tasks.

    Shows a list of all download tasks with filtering and clearing options.
    """

    def __init__(
        self,
        parent_model: "HomeModel",
        visible: bool = True,
        ref: ft.Ref | None = None,
    ):
        super().__init__(ref=ref, visible=visible, expand=True)

        self.parent_model = parent_model
        self.app_shared = AppShared()
        self.download_service: Optional[DownloadManagerService] = None
        self.task_tiles: dict[str, TaskTile] = {}

        # Create filter dropdown
        self.filter_dropdown = ft.Dropdown(
            label=_("Filter"),
            width=150,
            options=[
                ft.DropdownOption(key="all", text=_("All")),
                ft.DropdownOption(key="active", text=_("Active")),
                ft.DropdownOption(key="paused", text=_("Paused")),
                ft.DropdownOption(key="scheduled", text=_("Scheduled")),
                ft.DropdownOption(key="completed", text=_("Completed")),
                ft.DropdownOption(key="failed", text=_("Failed")),
            ],
            value="all",
            on_select=self._on_filter_select,
        )

        # Create task list view
        self.task_listview = ft.ListView(
            controls=[],
            expand=True,
            spacing=10,
            padding=10,
        )

        # Create empty state
        self.empty_state = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        icon=ft.Icons.DOWNLOAD_DONE,
                        size=64,
                        color=ft.Colors.GREY,
                    ),
                    ft.Text(
                        value=_("No download tasks"),
                        size=16,
                        color=ft.Colors.GREY,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.Alignment.CENTER,
        )

        # Build the view
        self.content = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(
                                value=_("Download Tasks"),
                                size=20,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Row(
                                controls=[
                                    self.filter_dropdown,
                                    ft.PopupMenuButton(
                                        icon=ft.Icons.MORE_VERT,
                                        tooltip=_("More actions"),
                                        items=[
                                            ft.PopupMenuItem(
                                                content=_("Pause all active"),
                                                icon=ft.Icons.PAUSE,
                                                on_click=self._on_pause_all,
                                            ),
                                            ft.PopupMenuItem(
                                                content=_("Resume all paused"),
                                                icon=ft.Icons.PLAY_ARROW,
                                                on_click=self._on_resume_all,
                                            ),
                                            ft.PopupMenuItem(
                                                content=_("Cancel all pending"),
                                                icon=ft.Icons.CANCEL,
                                                on_click=self._on_cancel_all_pending,
                                            ),
                                            ft.PopupMenuItem(),  # Divider
                                            ft.PopupMenuItem(
                                                content=_("Clear completed"),
                                                icon=ft.Icons.CLEAR_ALL,
                                                on_click=self._on_clear_completed,
                                            ),
                                            ft.PopupMenuItem(
                                                content=_("Clear failed"),
                                                icon=ft.Icons.DELETE_SWEEP,
                                                on_click=self._on_clear_failed,
                                            ),
                                        ],
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.REFRESH,
                                        tooltip=_("Refresh"),
                                        on_click=self._on_refresh,
                                    ),
                                ],
                                spacing=5,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        wrap=True if self.app_shared.is_mobile else False,
                        run_alignment=ft.MainAxisAlignment.START,
                    ),
                    padding=10,
                ),
                ft.Divider(height=1),
                ft.Container(
                    content=ft.Stack(
                        controls=[
                            self.task_listview,
                            self.empty_state,
                        ],
                    ),
                    expand=True,
                ),
            ],
            spacing=0,
        )

    def did_mount(self):
        """Called when the view is mounted."""
        # Get download service
        if self.app_shared.service_manager:
            self.download_service = cast(
                DownloadManagerService,
                self.app_shared.service_manager.get_service("download_manager"),
            )

            # Set up task update callback
            if self.download_service:
                self.download_service.add_task_update_callback(self._on_task_update)

        # Refresh task list
        self._refresh_tasks()

    def will_unmount(self):
        """Called when the view is about to be unmounted."""
        # Remove callback when view is unmounted
        if self.download_service:
            self.download_service.remove_task_update_callback(self._on_task_update)

    def _on_task_update(self, task: DownloadTask):
        """
        Callback when a task is updated.

        Args:
            task: The updated task
        """
        # Update or create task tile
        if task.task_id in self.task_tiles:
            # Update existing tile
            self.task_tiles[task.task_id].update_task(task)
        else:
            # Create new tile
            self._add_task_tile(task)

    def _add_task_tile(self, task: DownloadTask):
        """Add a task tile to the list."""
        tile = TaskTile(task, self)
        self.task_tiles[task.task_id] = tile

        # Apply current filter
        if self._should_show_task(task):
            self.task_listview.controls.insert(0, tile)

        # Update empty state
        self._update_empty_state()

        # Update UI
        if self.page:
            self.update()

    def _should_show_task(self, task: DownloadTask) -> bool:
        """Check if task should be shown based on current filter."""
        filter_value = self.filter_dropdown.value

        if filter_value == "all":
            return True
        elif filter_value == "active":
            return task.status in [
                DownloadTaskStatus.PENDING,
                DownloadTaskStatus.DOWNLOADING,
                DownloadTaskStatus.DECRYPTING,
                DownloadTaskStatus.VERIFYING,
            ]
        elif filter_value == "paused":
            return task.status == DownloadTaskStatus.PAUSED
        elif filter_value == "scheduled":
            return task.status == DownloadTaskStatus.SCHEDULED
        elif filter_value == "completed":
            return task.status == DownloadTaskStatus.COMPLETED
        elif filter_value == "failed":
            return task.status in [
                DownloadTaskStatus.FAILED,
                DownloadTaskStatus.CANCELLED,
            ]

        return True

    def _refresh_tasks(self):
        """Refresh the task list from the download service."""
        if not self.download_service:
            return

        # Clear current tiles
        self.task_tiles.clear()
        self.task_listview.controls.clear()

        # Get all tasks
        tasks = self.download_service.get_all_tasks()

        # Sort tasks by created time (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        # Add task tiles
        for task in tasks:
            if self._should_show_task(task):
                tile = TaskTile(task, self)
                self.task_tiles[task.task_id] = tile
                self.task_listview.controls.append(tile)

        # Update empty state
        self._update_empty_state()

        # Update UI
        if self.page:
            self.update()

    def _update_empty_state(self):
        """Update the visibility of the empty state."""
        has_tasks = len(self.task_listview.controls) > 0
        self.empty_state.visible = not has_tasks

    async def _on_filter_select(self, e):
        """Handle filter dropdown change."""
        self._refresh_tasks()

    async def _on_pause_all(self, e):
        """Handle pause all active downloads."""
        if self.download_service:
            active_tasks = [
                task.task_id
                for task in self.download_service.get_all_tasks()
                if task.status == DownloadTaskStatus.DOWNLOADING
            ]
            count = self.download_service.batch_pause_tasks(active_tasks)
            # (
            #     self.logger.info(f"Paused {count} active downloads")
            #     if hasattr(self, "logger")
            #     else None
            # )
            self._refresh_tasks()

    async def _on_resume_all(self, e):
        """Handle resume all paused downloads."""
        if self.download_service:
            paused_tasks = [
                task.task_id
                for task in self.download_service.get_all_tasks()
                if task.status == DownloadTaskStatus.PAUSED
            ]
            count = self.download_service.batch_resume_tasks(paused_tasks)
            self._refresh_tasks()

    async def _on_cancel_all_pending(self, e):
        """Handle cancel all pending downloads."""
        if self.download_service:
            pending_tasks = [
                task.task_id
                for task in self.download_service.get_all_tasks()
                if task.status == DownloadTaskStatus.PENDING
            ]
            count = self.download_service.batch_cancel_tasks(pending_tasks)
            self._refresh_tasks()

    async def _on_clear_completed(self, e):
        """Handle clear completed button click."""
        if self.download_service:
            self.download_service.clear_completed_tasks()
            self._refresh_tasks()

    async def _on_clear_failed(self, e):
        """Handle clear failed button click."""
        if self.download_service:
            self.download_service.clear_failed_tasks()
            self._refresh_tasks()

    async def _on_refresh(self, e):
        """Handle refresh button click."""
        self._refresh_tasks()
