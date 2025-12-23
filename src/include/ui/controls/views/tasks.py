"""Tasks view for displaying and managing download tasks."""

from typing import TYPE_CHECKING, Optional
import flet as ft

from include.classes.config import AppShared
from include.classes.datacls import DownloadTask, DownloadTaskStatus
from include.classes.services.download import DownloadManagerService
from include.util.locale import get_translation

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
        self.cancel_button = ft.IconButton(
            icon=ft.Icons.CANCEL,
            icon_size=16,
            tooltip=_("Cancel"),
            on_click=self._on_cancel,
            visible=task.status in [
                DownloadTaskStatus.PENDING,
                DownloadTaskStatus.DOWNLOADING,
                DownloadTaskStatus.DECRYPTING,
                DownloadTaskStatus.VERIFYING,
            ],
        )
        
        # Build the tile
        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(
                                name=self._get_status_icon(),
                                size=20,
                                color=self._get_status_color(),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        value=task.filename,
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    self.status_text,
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            self.cancel_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.progress_bar if task.status not in [
                        DownloadTaskStatus.COMPLETED,
                        DownloadTaskStatus.FAILED,
                        DownloadTaskStatus.CANCELLED,
                    ] else ft.Container(height=0),
                    self.progress_info,
                ],
                spacing=5,
            ),
            padding=10,
        )
    
    def _get_status_icon(self) -> str:
        """Get icon based on task status."""
        status_icons = {
            DownloadTaskStatus.PENDING: ft.Icons.SCHEDULE,
            DownloadTaskStatus.DOWNLOADING: ft.Icons.DOWNLOAD,
            DownloadTaskStatus.DECRYPTING: ft.Icons.LOCK_OPEN,
            DownloadTaskStatus.VERIFYING: ft.Icons.VERIFIED,
            DownloadTaskStatus.COMPLETED: ft.Icons.CHECK_CIRCLE,
            DownloadTaskStatus.FAILED: ft.Icons.ERROR,
            DownloadTaskStatus.CANCELLED: ft.Icons.CANCEL,
        }
        return status_icons.get(self.task.status, ft.Icons.HELP)
    
    def _get_status_color(self) -> str:
        """Get color based on task status."""
        status_colors = {
            DownloadTaskStatus.PENDING: ft.Colors.GREY,
            DownloadTaskStatus.DOWNLOADING: ft.Colors.BLUE,
            DownloadTaskStatus.DECRYPTING: ft.Colors.ORANGE,
            DownloadTaskStatus.VERIFYING: ft.Colors.PURPLE,
            DownloadTaskStatus.COMPLETED: ft.Colors.GREEN,
            DownloadTaskStatus.FAILED: ft.Colors.RED,
            DownloadTaskStatus.CANCELLED: ft.Colors.GREY,
        }
        return status_colors.get(self.task.status, ft.Colors.WHITE)
    
    def _get_status_text(self) -> str:
        """Get status text based on task status."""
        status_texts = {
            DownloadTaskStatus.PENDING: _("Pending"),
            DownloadTaskStatus.DOWNLOADING: _("Downloading"),
            DownloadTaskStatus.DECRYPTING: _("Decrypting"),
            DownloadTaskStatus.VERIFYING: _("Verifying"),
            DownloadTaskStatus.COMPLETED: _("Completed"),
            DownloadTaskStatus.FAILED: _("Failed"),
            DownloadTaskStatus.CANCELLED: _("Cancelled"),
        }
        status_text = status_texts.get(self.task.status, _("Unknown"))
        
        if self.task.status == DownloadTaskStatus.FAILED and self.task.error:
            status_text += f": {self.task.error}"
        
        return status_text
    
    def _get_progress_info(self) -> str:
        """Get progress information text."""
        if self.task.status == DownloadTaskStatus.COMPLETED:
            return _("Download completed")
        elif self.task.status in [DownloadTaskStatus.FAILED, DownloadTaskStatus.CANCELLED]:
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
        
        # Update progress bar
        self.progress_bar.value = task.progress
        
        # Update status text
        self.status_text.value = self._get_status_text()
        self.status_text.color = self._get_status_color()
        
        # Update progress info
        self.progress_info.value = self._get_progress_info()
        
        # Update button visibility
        self.cancel_button.visible = task.status in [
            DownloadTaskStatus.PENDING,
            DownloadTaskStatus.DOWNLOADING,
            DownloadTaskStatus.DECRYPTING,
            DownloadTaskStatus.VERIFYING,
        ]
        
        # Update the UI
        self.update()
    
    async def _on_cancel(self, e):
        """Handle cancel button click."""
        download_service = self.parent_view.download_service
        if download_service:
            download_service.cancel_task(self.task.task_id)


class TasksView(ft.Container):
    """
    Main view for displaying and managing download tasks.
    
    Shows a list of all download tasks with filtering and clearing options.
    """
    
    def __init__(self, parent_model: "HomeModel", ref: ft.Ref | None = None):
        super().__init__(ref=ref, visible=False, expand=True)
        
        self.parent_model = parent_model
        self.app_shared = AppShared()
        self.download_service: Optional[DownloadManagerService] = None
        self.task_tiles: dict[str, TaskTile] = {}
        
        # Create filter dropdown
        self.filter_dropdown = ft.Dropdown(
            label=_("Filter"),
            width=150,
            options=[
                ft.dropdown.Option(key="all", text=_("All")),
                ft.dropdown.Option(key="active", text=_("Active")),
                ft.dropdown.Option(key="completed", text=_("Completed")),
                ft.dropdown.Option(key="failed", text=_("Failed")),
            ],
            value="all",
            on_change=self._on_filter_change,
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
                        name=ft.Icons.DOWNLOAD_DONE,
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
                                    ft.IconButton(
                                        icon=ft.Icons.CLEAR_ALL,
                                        tooltip=_("Clear completed"),
                                        on_click=self._on_clear_completed,
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
            self.download_service = self.app_shared.service_manager.get_service("download_manager")
            
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
        elif filter_value == "completed":
            return task.status == DownloadTaskStatus.COMPLETED
        elif filter_value == "failed":
            return task.status in [DownloadTaskStatus.FAILED, DownloadTaskStatus.CANCELLED]
        
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
    
    async def _on_filter_change(self, e):
        """Handle filter dropdown change."""
        self._refresh_tasks()
    
    async def _on_clear_completed(self, e):
        """Handle clear completed button click."""
        if self.download_service:
            self.download_service.clear_completed_tasks()
            self._refresh_tasks()
    
    async def _on_refresh(self, e):
        """Handle refresh button click."""
        self._refresh_tasks()
