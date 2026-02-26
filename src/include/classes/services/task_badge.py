"""Service for tracking active download task count for badge display."""

import inspect
from typing import Callable, List

from include.classes.datacls import DownloadTaskStatus
from include.classes.services.base import BaseService
from include.classes.shared import AppShared

__all__ = ["TaskBadgeService"]

# Statuses that are considered "in progress" (non-terminal, actively queued/running)
_ACTIVE_STATUSES = {
    DownloadTaskStatus.PENDING,
    DownloadTaskStatus.DOWNLOADING,
    DownloadTaskStatus.DECRYPTING,
    DownloadTaskStatus.VERIFYING,
    DownloadTaskStatus.SCHEDULED,
}


class TaskBadgeService(BaseService):
    """
    Service that tracks the number of active download tasks for badge display.

    Periodically counts active (non-terminal) download tasks and notifies
    registered callbacks when the count changes, enabling UI components to
    update task badges without polling.

    Attributes:
        app_shared: Application shared configuration
    """

    def __init__(
        self,
        app_shared: AppShared,
        enabled: bool = True,
        interval: float = 1.0,
    ):
        """
        Initialize the task badge service.

        Args:
            app_shared: Application shared configuration
            enabled: Whether service is enabled
            interval: How often to check task count (seconds)
        """
        super().__init__(
            name="task_badge",
            enabled=enabled,
            interval=interval,
        )
        self.app_shared = app_shared
        self._last_count: int | None = None
        self._callbacks: List[Callable[[int], None]] = []

    async def execute(self):
        """Check active task count and notify callbacks if count has changed."""
        count = self._get_active_task_count()
        if count != self._last_count:
            self._last_count = count
            for callback in list(self._callbacks):
                try:
                    if inspect.iscoroutinefunction(callback):
                        await callback(count)
                    else:
                        callback(count)
                except Exception as e:
                    self.logger.error(
                        f"Error in task badge callback: {e}", exc_info=True
                    )

    def _get_active_task_count(self) -> int:
        """Get the number of active (non-terminal) download tasks."""
        from include.classes.services.download import DownloadManagerService

        if not self.app_shared.service_manager:
            return 0
        download_service = self.app_shared.service_manager.get_service(
            "download_manager"
        )
        if not isinstance(download_service, DownloadManagerService):
            return 0
        return sum(
            1
            for task in download_service.tasks.values()
            if task.status in _ACTIVE_STATUSES
        )

    @property
    def current_count(self) -> int:
        """Get the last known active task count (0 if not yet checked)."""
        return self._last_count if self._last_count is not None else 0

    def register_callback(self, callback: Callable[[int], None]) -> None:
        """
        Register a callback to be notified when active task count changes.

        Args:
            callback: Function accepting an int (active task count)
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[int], None]) -> None:
        """
        Unregister a previously registered callback.

        Args:
            callback: Function to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
