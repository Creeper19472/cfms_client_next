"""Download manager service for centrally managing file downloads."""

import asyncio
import inspect
import json
import os
import time
from typing import Dict, Iterable, List, Optional, Callable, Set
from websockets.asyncio.client import ClientConnection

from include.classes.shared import AppShared
from include.classes.datacls import DownloadTask, DownloadTaskStatus
from include.classes.exceptions.config import CorruptedEncryptedConfigError
from include.classes.services.base import BaseService
from include.constants import FLET_APP_STORAGE_DATA
from include.util.connect import get_connection
from include.util.kdf import encrypt_config, decrypt_config, is_encrypted_config
from include.util.transfer import receive_file_from_server

__all__ = ["DownloadManagerService"]

# Statuses that count towards the navigation badge (non-terminal, actively queued/running)
_ACTIVE_BADGE_STATUSES = {
    DownloadTaskStatus.PENDING,
    DownloadTaskStatus.DOWNLOADING,
    DownloadTaskStatus.DECRYPTING,
    DownloadTaskStatus.VERIFYING,
    DownloadTaskStatus.SCHEDULED,
}

# Directory for task persistence (similar to user_preferences)
DOWNLOAD_TASKS_PATH = f"{FLET_APP_STORAGE_DATA}/download_tasks"

# Legacy path for task persistence (kept for backward compatibility)
TASKS_PERSISTENCE_FILE_LEGACY = f"{FLET_APP_STORAGE_DATA}/download_tasks.json"


class DownloadManagerService(BaseService):
    """
    Download manager service for centrally managing file download tasks.

    This service manages a queue of download tasks, handles concurrent downloads,
    tracks progress, and provides an interface for the UI to monitor and control
    download operations.

    Features:
    - Concurrent download management with configurable limits
    - Pause/Resume functionality
    - Priority queue support
    - Task persistence across restarts
    - Bandwidth limiting
    - Download scheduling
    - Automatic retry on failures
    - Batch operations

    Attributes:
        tasks: Dictionary of all tasks keyed by task_id
        active_downloads: Set of currently active download task_ids
        active_tasks: Set of asyncio tasks for running downloads
        max_concurrent: Maximum number of concurrent downloads
        app_shared: Application shared configuration
        on_task_update_callbacks: List of callbacks for task updates
        on_active_count_changed_callbacks: List of callbacks for active-task count changes
        enable_persistence: Whether to save/load tasks across restarts
    """

    def __init__(
        self,
        app_shared: AppShared,
        enabled: bool = True,
        max_concurrent: int = 3,
        enable_persistence: bool = True,
        on_task_update: Optional[Callable[[DownloadTask], None]] = None,
    ):
        """
        Initialize the download manager service.

        Args:
            app_shared: Application shared configuration
            enabled: Whether service is enabled
            max_concurrent: Maximum concurrent downloads
            enable_persistence: Whether to persist tasks to disk
            on_task_update: Optional callback when task state changes
        """
        super().__init__(
            name="download_manager",
            enabled=enabled,
            interval=1.0,  # Check queue every second
        )
        self.app_shared = app_shared
        self.tasks: Dict[str, DownloadTask] = {}
        self.active_downloads: set[str] = set()
        self.active_tasks: Set[asyncio.Task] = set()
        self.max_concurrent = max_concurrent
        self.enable_persistence = enable_persistence
        self.on_task_update_callbacks: List[Callable[[DownloadTask], None]] = []
        if on_task_update:
            self.on_task_update_callbacks.append(on_task_update)
        self.on_active_count_changed_callbacks: List[Callable[[int], None]] = []
        self._last_active_count: int | None = None
        self._download_lock = asyncio.Lock()

    async def execute(self):
        """
        Main service execution loop.

        Processes pending/scheduled downloads from the queue if capacity is available.
        Handles scheduled downloads and priority-based queue.
        """
        current_time = time.time()

        # Check for scheduled tasks that are ready
        scheduled_tasks = [
            task
            for task in self.tasks.values()
            if task.status == DownloadTaskStatus.SCHEDULED
            and task.scheduled_time is not None
            and task.scheduled_time <= current_time
        ]

        # Move scheduled tasks to pending
        for task in scheduled_tasks:
            task.status = DownloadTaskStatus.PENDING
            task.scheduled_time = None
            self._notify_task_update(task)
            self.logger.info(f"Scheduled task {task.filename} is now pending")

        # Get pending tasks sorted by priority (higher priority first)
        pending_tasks = sorted(
            [
                task
                for task in self.tasks.values()
                if task.status == DownloadTaskStatus.PENDING
            ],
            key=lambda t: t.priority,
            reverse=True,
        )

        # Start downloads up to max_concurrent limit
        async with self._download_lock:
            available_slots = self.max_concurrent - len(self.active_downloads)

            for task in pending_tasks[:available_slots]:
                # Create download task and track it
                download_task = asyncio.create_task(self._download_task(task))
                self.active_tasks.add(download_task)
                download_task.add_done_callback(self.active_tasks.discard)

    async def _download_task(self, task: DownloadTask):
        """
        Execute a single download task with retry logic.

        Args:
            task: The download task to execute
        """
        # Mark task as active under lock
        async with self._download_lock:
            self.active_downloads.add(task.task_id)

        task.status = DownloadTaskStatus.DOWNLOADING
        task.started_at = time.time()
        self._notify_task_update(task)

        transfer_conn: Optional[ClientConnection] = None

        try:
            self.logger.info(
                f"Starting download: {task.filename} (task_id: {task.task_id}, attempt {task.retry_count + 1})"
            )

            # Establish connection
            transfer_conn = await get_connection(
                server_address=self.app_shared.get_not_none_attribute("server_address"),
                disable_ssl_enforcement=self.app_shared.disable_ssl_enforcement,
                proxy=self.app_shared.preferences["settings"]["proxy_settings"],
                max_size=1024**2 * 4,
                force_ipv4=self.app_shared.preferences["settings"].get(
                    "force_ipv4", False
                ),
            )

            # Start file transfer
            async for stage, *data in receive_file_from_server(
                transfer_conn, task_id=task.task_id, file_path=task.file_path
            ):
                # Check if task was cancelled or paused
                if task.status == DownloadTaskStatus.CANCELLED:
                    self.logger.info(f"Download cancelled: {task.filename}")
                    break
                elif task.status == DownloadTaskStatus.PAUSED:
                    self.logger.info(f"Download paused: {task.filename}")
                    task.pause_position = task.current_bytes
                    break

                # Update task based on stage
                task.stage = stage

                match stage:
                    case 0:  # Downloading
                        task.status = DownloadTaskStatus.DOWNLOADING
                        received_file_size, file_size = data
                        task.current_bytes = received_file_size
                        task.total_bytes = file_size
                        if file_size > 0:
                            task.progress = received_file_size / file_size
                        else:
                            task.progress = 1.0
                    case 1:  # Decrypting
                        task.status = DownloadTaskStatus.DECRYPTING
                        decrypted_chunks, total_chunks = data
                        if total_chunks > 0:
                            task.progress = decrypted_chunks / total_chunks
                    case 2:  # Cleaning temporary files
                        task.status = DownloadTaskStatus.VERIFYING
                        task.progress = 0.95
                    case 3:  # Verifying
                        task.status = DownloadTaskStatus.VERIFYING
                        task.progress = 1.0

                self._notify_task_update(task)

                # Apply bandwidth limiting if set
                if task.bandwidth_limit and stage == 0:
                    # Simple bandwidth throttling
                    await asyncio.sleep(0.1)

            # Download completed successfully (unless it was cancelled/paused)
            if task.status not in [
                DownloadTaskStatus.CANCELLED,
                DownloadTaskStatus.PAUSED,
            ]:
                task.status = DownloadTaskStatus.COMPLETED
                task.progress = 1.0
                task.completed_at = time.time()
                self.logger.info(f"Download completed: {task.filename}")

        except asyncio.CancelledError:
            # Task was cancelled via asyncio
            if task.status != DownloadTaskStatus.CANCELLED:
                task.status = DownloadTaskStatus.CANCELLED
                task.error = "Download cancelled by user"
            self.logger.info(f"Download cancelled: {task.filename}")
            raise

        except Exception as e:
            # Download failed - check if we should retry
            task.retry_count += 1

            if task.retry_count < task.max_retries:
                # Retry the download
                task.status = DownloadTaskStatus.PENDING
                task.error = f"Attempt {task.retry_count} failed: {str(e)}. Retrying..."
                self.logger.warning(
                    f"Download failed, will retry: {task.filename} - {e}"
                )
            else:
                # Max retries reached, mark as failed
                task.status = DownloadTaskStatus.FAILED
                task.error = f"Failed after {task.retry_count} attempts: {str(e)}"
                self.logger.error(
                    f"Download failed after {task.retry_count} attempts: {task.filename} - {e}",
                    exc_info=True,
                )

        finally:
            # Clean up under lock
            async with self._download_lock:
                self.active_downloads.discard(task.task_id)
            if transfer_conn:
                await transfer_conn.close()
            self._notify_task_update(task)

            # Save tasks if persistence is enabled
            if self.enable_persistence:
                await self._save_tasks()

    def pause_task(self, task_id: str) -> bool:
        """
        Pause a download task.

        Args:
            task_id: ID of the task to pause

        Returns:
            True if task was paused, False if task not found or not pausable
        """
        task = self.tasks.get(task_id)
        if not task:
            self.logger.warning(f"Cannot pause task {task_id}: task not found")
            return False

        # Check if task supports resume
        if not task.supports_resume:
            self.logger.warning(
                f"Cannot pause task {task_id}: server does not support resume"
            )
            return False

        if task.status not in [
            DownloadTaskStatus.DOWNLOADING,
            DownloadTaskStatus.PENDING,
        ]:
            self.logger.warning(
                f"Cannot pause task {task_id}: task not in pausable state"
            )
            return False

        task.status = DownloadTaskStatus.PAUSED
        self.logger.info(f"Paused task: {task.filename} (task_id: {task_id})")
        self._notify_task_update(task)

        # Save tasks if persistence is enabled
        if self.enable_persistence:
            asyncio.create_task(self._save_tasks())

        return True

    def resume_task(self, task_id: str) -> bool:
        """
        Resume a paused download task.

        Args:
            task_id: ID of the task to resume

        Returns:
            True if task was resumed, False if task not found or not paused
        """
        task = self.tasks.get(task_id)
        if not task:
            self.logger.warning(f"Cannot resume task {task_id}: task not found")
            return False

        if task.status != DownloadTaskStatus.PAUSED:
            self.logger.warning(f"Cannot resume task {task_id}: task not paused")
            return False

        task.status = DownloadTaskStatus.PENDING
        self.logger.info(f"Resumed task: {task.filename} (task_id: {task_id})")
        self._notify_task_update(task)

        # Save tasks if persistence is enabled
        if self.enable_persistence:
            asyncio.create_task(self._save_tasks())

        return True

    # (removed duplicate cancel_task)

    def set_task_priority(self, task_id: str, priority: int) -> bool:
        """
        Set the priority of a pending task.

        Args:
            task_id: ID of the task
            priority: New priority value (higher = processed first)

        Returns:
            True if priority was set, False if task not found or not pending
        """
        task = self.tasks.get(task_id)
        if not task:
            self.logger.warning(
                f"Cannot set priority for task {task_id}: task not found"
            )
            return False

        if task.status not in [
            DownloadTaskStatus.PENDING,
            DownloadTaskStatus.SCHEDULED,
        ]:
            self.logger.warning(
                f"Cannot set priority for task {task_id}: task not pending/scheduled"
            )
            return False

        task.priority = priority
        self.logger.info(f"Set priority {priority} for task: {task.filename}")
        self._notify_task_update(task)

        return True

    def batch_cancel_tasks(self, task_ids: Iterable[str]) -> int:
        """
        Cancel multiple tasks at once.

        Args:
            task_ids: List of task IDs to cancel

        Returns:
            Number of tasks successfully cancelled
        """
        count = 0
        for task_id in task_ids:
            if self.cancel_task(task_id):
                count += 1

        self.logger.info(f"Batch cancelled {count} tasks")
        return count

    def batch_pause_tasks(self, task_ids: List[str]) -> int:
        """
        Pause multiple tasks at once.

        Args:
            task_ids: List of task IDs to pause

        Returns:
            Number of tasks successfully paused
        """
        count = 0
        for task_id in task_ids:
            if self.pause_task(task_id):
                count += 1

        self.logger.info(f"Batch paused {count} tasks")
        return count

    def batch_resume_tasks(self, task_ids: List[str]) -> int:
        """
        Resume multiple paused tasks at once.

        Args:
            task_ids: List of task IDs to resume

        Returns:
            Number of tasks successfully resumed
        """
        count = 0
        for task_id in task_ids:
            if self.resume_task(task_id):
                count += 1

        self.logger.info(f"Batch resumed {count} tasks")
        return count

    def _get_persistence_file_path(self) -> str:
        """
        Get the user-specific persistence file path.

        Uses the same pattern as user_preferences: {server_address_hash}_{username}.json
        This ensures task lists are separated by both server and user.

        Returns:
            Path to the user-specific persistence file. If no user is logged in or
            server address is not set, returns the legacy shared file path for
            backward compatibility.
        """
        username = self.app_shared.username
        if username:
            try:
                server_hash = self.app_shared.server_address_hash
                # Use server_hash + username pattern like user_preferences
                return f"{DOWNLOAD_TASKS_PATH}/{server_hash}_{username}.json"
            except (ValueError, AttributeError):
                # Fall back to legacy if server address not set
                return TASKS_PERSISTENCE_FILE_LEGACY
        else:
            # Fall back to legacy shared file path when no user is logged in
            return TASKS_PERSISTENCE_FILE_LEGACY

    @staticmethod
    def _write_tasks_file(path: str, data: dict, dek: "bytes | None") -> None:
        """Serialise *data* to *path*, encrypting with *dek* when provided.

        When *dek* is ``None``, plaintext is written only if the existing file
        is not already encrypted.  If an encrypted file exists but no DEK is
        available, the file is left unchanged to prevent data loss and a
        security downgrade.
        """
        plaintext = json.dumps(data, separators=(",", ":")).encode("utf-8")
        if dek is not None:
            raw = encrypt_config(plaintext, dek)
            with open(path, "wb") as f:
                f.write(raw)
        else:
            # Do not overwrite an existing encrypted file when no DEK is available.
            if os.path.exists(path):
                try:
                    with open(path, "rb") as existing_file:
                        if is_encrypted_config(existing_file.read()):
                            return
                except OSError:
                    return
            with open(path, "wb") as f:
                f.write(plaintext)

    async def _save_tasks(self):
        """Save tasks to disk for persistence."""
        if not self.enable_persistence:
            return

        try:
            # Save all tasks (including completed ones)
            tasks_to_save = {
                task_id: {
                    "task_id": task.task_id,
                    "file_id": task.file_id,
                    "filename": task.filename,
                    "file_path": task.file_path,
                    "status": task.status.value,
                    "progress": task.progress,
                    "current_bytes": task.current_bytes,
                    "total_bytes": task.total_bytes,
                    "error": task.error,
                    "created_at": task.created_at,
                    "started_at": task.started_at,
                    "completed_at": task.completed_at,
                    "stage": task.stage,
                    "priority": task.priority,
                    "retry_count": task.retry_count,
                    "max_retries": task.max_retries,
                    "scheduled_time": task.scheduled_time,
                    "bandwidth_limit": task.bandwidth_limit,
                    "pause_position": task.pause_position,
                    "supports_resume": task.supports_resume,
                }
                for task_id, task in self.tasks.items()
            }

            # Get user-specific persistence file path
            persistence_file = self._get_persistence_file_path()

            # Ensure directory exists
            os.makedirs(os.path.dirname(persistence_file), exist_ok=True)

            self._write_tasks_file(persistence_file, tasks_to_save, self.app_shared.dek)

            self.logger.debug(
                f"Saved {len(tasks_to_save)} tasks to disk (file: {os.path.basename(persistence_file)})"
            )

        except Exception as e:
            self.logger.error(f"Failed to save tasks: {e}", exc_info=True)

    async def _load_tasks(self):
        """Load tasks from disk."""
        if not self.enable_persistence:
            return

        # Get user-specific persistence file path
        persistence_file = self._get_persistence_file_path()

        if not os.path.exists(persistence_file):
            return

        try:
            with open(persistence_file, "rb") as f:
                raw = f.read()

            dek = self.app_shared.dek
            if is_encrypted_config(raw):
                if dek is None:
                    self.logger.warning(
                        "Task file is encrypted but DEK is not available; skipping load"
                    )
                    return
                try:
                    plaintext = decrypt_config(raw, dek)
                    tasks_data = json.loads(plaintext.decode("utf-8"))
                except (ValueError, json.JSONDecodeError):
                    # DEK present but decryption failed — file was encrypted with
                    # a different (old) DEK, e.g. after a server reset.
                    raise CorruptedEncryptedConfigError(persistence_file)
            else:
                tasks_data = json.loads(raw.decode("utf-8"))
                # Migrate plain-JSON file to encrypted format when DEK is available
                if dek is not None:
                    self._write_tasks_file(persistence_file, tasks_data, dek)

            for task_id, task_dict in tasks_data.items():
                # Convert status string back to enum
                status = DownloadTaskStatus(task_dict["status"])

                # Reset downloading/decrypting tasks to pending
                if status in [
                    DownloadTaskStatus.DOWNLOADING,
                    DownloadTaskStatus.DECRYPTING,
                ]:
                    status = DownloadTaskStatus.PENDING

                task = DownloadTask(
                    task_id=task_dict["task_id"],
                    file_id=task_dict["file_id"],
                    filename=task_dict["filename"],
                    file_path=task_dict["file_path"],
                    status=status,
                    progress=task_dict["progress"],
                    current_bytes=task_dict["current_bytes"],
                    total_bytes=task_dict["total_bytes"],
                    error=task_dict["error"],
                    created_at=task_dict["created_at"],
                    started_at=task_dict["started_at"],
                    completed_at=task_dict["completed_at"],
                    stage=task_dict["stage"],
                    priority=task_dict["priority"],
                    retry_count=task_dict["retry_count"],
                    max_retries=task_dict["max_retries"],
                    scheduled_time=task_dict["scheduled_time"],
                    bandwidth_limit=task_dict["bandwidth_limit"],
                    pause_position=task_dict["pause_position"],
                    supports_resume=task_dict.get(
                        "supports_resume", False
                    ),  # Default to False for backward compatibility
                )

                self.tasks[task_id] = task

            self._last_active_count = self.__get_active_task_count()
            self.logger.info(
                f"Loaded {len(self.tasks)} tasks from disk (file: {os.path.basename(persistence_file)})"
            )

        except CorruptedEncryptedConfigError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to load tasks: {e}", exc_info=True)

    def add_task_update_callback(self, callback: Callable[[DownloadTask], None]):
        """
        Add a callback for task updates.

        Args:
            callback: Callback function to be called when tasks are updated
        """
        if callback not in self.on_task_update_callbacks:
            self.on_task_update_callbacks.append(callback)

    def remove_task_update_callback(self, callback: Callable[[DownloadTask], None]):
        """
        Remove a callback for task updates.

        Args:
            callback: Callback function to remove
        """
        if callback in self.on_task_update_callbacks:
            self.on_task_update_callbacks.remove(callback)

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """
        Get a task by its ID.

        Args:
            task_id: ID of the task to retrieve

        Returns:
            The DownloadTask if found, None otherwise
        """
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[DownloadTask]:
        """
        Get all download tasks.

        Returns:
            List of all DownloadTask instances
        """
        return list(self.tasks.values())

    def get_tasks_by_status(self, status: DownloadTaskStatus) -> List[DownloadTask]:
        """
        Get all tasks with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of DownloadTask instances with the specified status
        """
        return [task for task in self.tasks.values() if task.status == status]

    async def reload_tasks_for_user(self):
        """
        Reload download tasks for the current user.
        This method handles the transition when a user changes by:
        1. Cancelling any active downloads from the previous user
        2. Clearing all cached tasks
        3. Loading tasks for the new user from persistent storage (if enabled)
        The method logs progress at each stage for debugging purposes.
        Raises:
            None
        Returns:
            None
        Note:
            Tasks are not explicitly saved before clearing as the username has already
            been updated, and tasks are saved periodically through auto-save mechanisms.
        """

        self.logger.info(
            f"Reloading tasks for user '{self.app_shared.username or 'anonymous'}'"
        )

        if self.active_downloads:
            self.logger.warning(
                "Cancelling %d active download(s) before reloading tasks for new user",
                len(self.active_downloads),
            )
            self.batch_cancel_tasks(self.active_downloads)

        # Clear current tasks (from previous user or initial state)
        # We don't save here because the username has already been changed,
        # and tasks are auto-saved periodically anyway
        self.tasks.clear()

        # Load tasks for the current user
        if self.enable_persistence:
            await self._load_tasks()
        # Log the result
        self.logger.debug(f"Task reload complete: {len(self.tasks)} tasks loaded")

    def clear_completed_tasks(self) -> int:
        """
        Remove all completed tasks (including cancelled tasks) from the task list.

        Returns:
            Number of tasks removed
        """
        completed_tasks = [
            task_id
            for task_id, task in self.tasks.items()
            if task.status
            in [DownloadTaskStatus.COMPLETED, DownloadTaskStatus.CANCELLED]
        ]

        for task_id in completed_tasks:
            del self.tasks[task_id]

        count = len(completed_tasks)
        if count > 0:
            self.logger.info(f"Cleared {count} completed tasks")

            # Save after clearing
            if self.enable_persistence:
                asyncio.create_task(self._save_tasks())

        return count

    def clear_failed_tasks(self) -> int:
        """
        Remove all failed tasks from the task list.

        Returns:
            Number of tasks removed
        """
        failed_tasks = [
            task_id
            for task_id, task in self.tasks.items()
            if task.status == DownloadTaskStatus.FAILED
        ]

        for task_id in failed_tasks:
            del self.tasks[task_id]

        count = len(failed_tasks)
        if count > 0:
            self.logger.info(f"Cleared {count} failed tasks")

            # Save after clearing
            if self.enable_persistence:
                asyncio.create_task(self._save_tasks())

        return count

    async def delete_task_with_file(self, task_id: str) -> tuple[bool, str | None]:
        """
        Delete a completed task and its associated file.
        Also deletes all other tasks pointing to the same file path.

        Args:
            task_id: ID of the task to delete

        Returns:
            Tuple of (success: bool, error_message: str | None)
            - (True, None) if task and file were deleted successfully
            - (False, error_msg) if deletion failed
        """
        task = self.tasks.get(task_id)
        if not task:
            self.logger.warning(f"Cannot delete task {task_id}: task not found")
            return False, "Task not found"

        if task.status != DownloadTaskStatus.COMPLETED:
            self.logger.warning(
                f"Cannot delete task {task_id}: task not completed (status: {task.status})"
            )
            return False, "Task is not completed"

        file_path = task.file_path

        # Find all tasks pointing to the same file path
        tasks_with_same_file = [
            t for t in self.tasks.values() if t.file_path == file_path
        ]

        # Delete the file if it exists
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                self.logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                error_msg = f"Failed to delete file: {str(e)}"
                self.logger.error(
                    f"Failed to delete file {file_path}: {e}", exc_info=True
                )
                # Do not delete any tasks if file deletion fails
                return False, error_msg

        # Remove all tasks with the same file path
        deleted_count = 0
        for t in tasks_with_same_file:
            if t.task_id in self.tasks:
                # Notify listeners before removing
                self._notify_task_update(t)
                del self.tasks[t.task_id]
                deleted_count += 1
                self.logger.info(f"Deleted task: {t.filename} (task_id: {t.task_id})")

        self.logger.info(
            f"Deleted {deleted_count} task(s) associated with file: {file_path}"
        )

        # Save tasks after deletion
        if self.enable_persistence:
            await self._save_tasks()

        return True, None

    def _notify_task_update(self, task: DownloadTask):
        """
        Notify listeners about task updates.

        Args:
            task: The task that was updated
        """
        for callback in self.on_task_update_callbacks:
            try:
                callback(task)
            except Exception as e:
                self.logger.error(f"Error in task update callback: {e}", exc_info=True)

        # Recompute active count and fire count-change callbacks when it changes.
        # We recount from the full task dict here for correctness; in practice task
        # collections are small (dozens at most) so a full scan is negligible.
        active_count = self.__get_active_task_count()
        if active_count != self._last_active_count:
            self._last_active_count = active_count
            for callback in self.on_active_count_changed_callbacks:
                try:
                    if inspect.iscoroutinefunction(callback):
                        asyncio.create_task(callback(active_count))
                    else:
                        callback(active_count)
                except Exception as e:
                    self.logger.error(
                        f"Error in active count callback: {e}", exc_info=True
                    )

    @property
    def active_task_count(self) -> int:
        """Number of active (non-terminal) download tasks."""
        return self._last_active_count if self._last_active_count is not None else 0

    def __get_active_task_count(self) -> int:
        return sum(1 for t in self.tasks.values() if t.status in _ACTIVE_BADGE_STATUSES)

    def add_active_count_callback(self, callback: Callable[[int], None]) -> None:
        """
        Register a callback to be notified when the active task count changes.

        Args:
            callback: Function accepting an int (new active task count)
        """
        if callback not in self.on_active_count_changed_callbacks:
            self.on_active_count_changed_callbacks.append(callback)

    def remove_active_count_callback(self, callback: Callable[[int], None]) -> None:
        """
        Unregister a previously registered active-count callback.

        Args:
            callback: Function to remove
        """
        if callback in self.on_active_count_changed_callbacks:
            self.on_active_count_changed_callbacks.remove(callback)

    async def on_start(self):
        """Called when the service starts."""
        self.logger.info("Download manager service starting")

        # Load tasks from disk if persistence is enabled
        if self.enable_persistence:
            await self._load_tasks()

    async def on_stop(self):
        """Called when the service stops."""
        self.logger.info("Download manager service stopping")

        # Save tasks before stopping
        if self.enable_persistence:
            await self._save_tasks()

        # Cancel all active downloads
        for task_id in list(self.active_downloads):
            self.cancel_task(task_id)

        # Wait for all active tasks to complete
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks, return_exceptions=True)

    def add_task(
        self,
        task_id: str,
        file_id: str,
        filename: str,
        file_path: str,
        priority: int = 0,
        max_retries: int = 3,
        scheduled_time: Optional[float] = None,
        bandwidth_limit: Optional[int] = None,
        supports_resume: bool = False,
    ) -> DownloadTask:
        """
        Add a new download task to the queue.

        If a completed task already exists with the same file_path, it will be removed
        since the file will be overwritten by this new download.

        Args:
            task_id: Server task ID for the download
            file_id: Document/file ID being downloaded
            filename: Name of the file
            file_path: Local path where file will be saved
            priority: Task priority (higher = processed first, default 0)
            max_retries: Maximum retry attempts (default 3)
            scheduled_time: Unix timestamp to start download (None = start immediately)
            bandwidth_limit: Download speed limit in bytes/second (None = unlimited)
            supports_resume: Whether server supports pause/resume (default False)

        Returns:
            The created DownloadTask instance
        """
        # Check for existing completed tasks with the same file_path
        # These will be overwritten, so remove them to avoid confusion
        tasks_to_remove = []
        for existing_task_id, existing_task in self.tasks.items():
            if (
                existing_task.file_path == file_path
                and existing_task.status == DownloadTaskStatus.COMPLETED
            ):
                tasks_to_remove.append(existing_task_id)
                self.logger.info(
                    f"Removing old completed task {existing_task_id} for {existing_task.filename} "
                    f"as new task will overwrite the file at {file_path}"
                )

        # Remove old completed tasks
        for task_id_to_remove in tasks_to_remove:
            # Notify before removing
            old_task = self.tasks[task_id_to_remove]
            self._notify_task_update(old_task)
            del self.tasks[task_id_to_remove]

        # Determine initial status
        if scheduled_time and scheduled_time > time.time():
            status = DownloadTaskStatus.SCHEDULED
        else:
            status = DownloadTaskStatus.PENDING
            scheduled_time = None

        task = DownloadTask(
            task_id=task_id,
            file_id=file_id,
            filename=filename,
            file_path=file_path,
            status=status,
            created_at=time.time(),
            priority=priority,
            max_retries=max_retries,
            scheduled_time=scheduled_time,
            bandwidth_limit=bandwidth_limit,
            supports_resume=supports_resume,
        )

        self.tasks[task_id] = task
        self.logger.info(
            f"Added download task: {filename} (task_id: {task_id}, priority: {priority}, supports_resume: {supports_resume})"
        )
        self._notify_task_update(task)

        # Save tasks if persistence is enabled
        if self.enable_persistence:
            asyncio.create_task(self._save_tasks())

        return task

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a download task.

        Args:
            task_id: ID of the task to cancel

        Returns:
            True if task was cancelled, False if task not found or not cancellable
        """
        task = self.tasks.get(task_id)
        if not task:
            self.logger.warning(f"Cannot cancel task {task_id}: task not found")
            return False

        if task.status in [
            DownloadTaskStatus.COMPLETED,
            DownloadTaskStatus.FAILED,
            DownloadTaskStatus.CANCELLED,
        ]:
            self.logger.warning(
                f"Cannot cancel task {task_id}: task already in terminal state"
            )
            return False

        # Mark task as cancelled
        task.status = DownloadTaskStatus.CANCELLED
        task.error = "Cancelled by user"
        self.logger.info(f"Cancelled task: {task.filename} (task_id: {task_id})")

        # Cancel the asyncio task if it's running
        for async_task in self.active_tasks:
            # The task will check the status and exit gracefully
            pass

        self._notify_task_update(task)

        return True
