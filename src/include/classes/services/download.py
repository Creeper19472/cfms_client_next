"""Download manager service for centrally managing file downloads."""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Callable
from websockets.asyncio.client import ClientConnection

from include.classes.config import AppShared
from include.classes.datacls import DownloadTask, DownloadTaskStatus
from include.classes.services.base import BaseService, ServiceStatus
from include.util.connect import get_connection
from include.util.requests import do_request_2
from include.util.transfer import receive_file_from_server

__all__ = ["DownloadManagerService"]


class DownloadManagerService(BaseService):
    """
    Download manager service for centrally managing file download tasks.
    
    This service manages a queue of download tasks, handles concurrent downloads,
    tracks progress, and provides an interface for the UI to monitor and control
    download operations.
    
    Attributes:
        tasks: Dictionary of all tasks keyed by task_id
        active_downloads: Set of currently active download task_ids
        max_concurrent: Maximum number of concurrent downloads
        app_shared: Application shared configuration
        on_task_update: Optional callback for task updates
    """
    
    def __init__(
        self,
        app_shared: AppShared,
        enabled: bool = True,
        max_concurrent: int = 3,
        on_task_update: Optional[Callable[[DownloadTask], None]] = None,
    ):
        """
        Initialize the download manager service.
        
        Args:
            app_shared: Application shared configuration
            enabled: Whether service is enabled
            max_concurrent: Maximum concurrent downloads
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
        self.max_concurrent = max_concurrent
        self.on_task_update = on_task_update
        self._download_lock = asyncio.Lock()
        
    async def execute(self):
        """
        Main service execution loop.
        
        Processes pending downloads from the queue if capacity is available.
        """
        # Get pending tasks
        pending_tasks = [
            task for task in self.tasks.values()
            if task.status == DownloadTaskStatus.PENDING
        ]
        
        # Start downloads up to max_concurrent limit
        async with self._download_lock:
            available_slots = self.max_concurrent - len(self.active_downloads)
            
            for task in pending_tasks[:available_slots]:
                # Create download task
                asyncio.create_task(self._download_task(task))
    
    async def _download_task(self, task: DownloadTask):
        """
        Execute a single download task.
        
        Args:
            task: The download task to execute
        """
        task.status = DownloadTaskStatus.DOWNLOADING
        task.started_at = time.time()
        self.active_downloads.add(task.task_id)
        self._notify_task_update(task)
        
        transfer_conn: Optional[ClientConnection] = None
        
        try:
            self.logger.info(f"Starting download: {task.filename} (task_id: {task.task_id})")
            
            # Establish connection
            transfer_conn = await get_connection(
                server_address=self.app_shared.get_not_none_attribute("server_address"),
                disable_ssl_enforcement=self.app_shared.disable_ssl_enforcement,
                proxy=self.app_shared.preferences["settings"]["proxy_settings"],
                max_size=1024**2 * 4,
            )
            
            # Start file transfer
            async for stage, *data in receive_file_from_server(
                transfer_conn, task_id=task.task_id, file_path=task.file_path
            ):
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
            
            # Download completed successfully
            task.status = DownloadTaskStatus.COMPLETED
            task.progress = 1.0
            task.completed_at = time.time()
            self.logger.info(f"Download completed: {task.filename}")
            
        except asyncio.CancelledError:
            # Task was cancelled
            task.status = DownloadTaskStatus.CANCELLED
            task.error = "Download cancelled by user"
            self.logger.info(f"Download cancelled: {task.filename}")
            
        except Exception as e:
            # Download failed
            task.status = DownloadTaskStatus.FAILED
            task.error = str(e)
            self.logger.error(f"Download failed: {task.filename} - {e}", exc_info=True)
            
        finally:
            # Clean up
            self.active_downloads.discard(task.task_id)
            if transfer_conn:
                await transfer_conn.close()
            self._notify_task_update(task)
    
    def add_task(
        self,
        task_id: str,
        file_id: str,
        filename: str,
        file_path: str,
    ) -> DownloadTask:
        """
        Add a new download task to the queue.
        
        Args:
            task_id: Server task ID for the download
            file_id: Document/file ID being downloaded
            filename: Name of the file
            file_path: Local path where file will be saved
            
        Returns:
            The created DownloadTask instance
        """
        task = DownloadTask(
            task_id=task_id,
            file_id=file_id,
            filename=filename,
            file_path=file_path,
            status=DownloadTaskStatus.PENDING,
            created_at=time.time(),
        )
        
        self.tasks[task_id] = task
        self.logger.info(f"Added download task: {filename} (task_id: {task_id})")
        self._notify_task_update(task)
        
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
        
        if task.status in [DownloadTaskStatus.COMPLETED, DownloadTaskStatus.FAILED, DownloadTaskStatus.CANCELLED]:
            self.logger.warning(f"Cannot cancel task {task_id}: task already in terminal state")
            return False
        
        task.status = DownloadTaskStatus.CANCELLED
        task.error = "Cancelled by user"
        self.logger.info(f"Cancelled task: {task.filename} (task_id: {task_id})")
        self._notify_task_update(task)
        
        return True
    
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
    
    def clear_completed_tasks(self) -> int:
        """
        Remove all completed tasks from the task list.
        
        Returns:
            Number of tasks removed
        """
        completed_tasks = [
            task_id for task_id, task in self.tasks.items()
            if task.status == DownloadTaskStatus.COMPLETED
        ]
        
        for task_id in completed_tasks:
            del self.tasks[task_id]
        
        count = len(completed_tasks)
        if count > 0:
            self.logger.info(f"Cleared {count} completed tasks")
        
        return count
    
    def clear_failed_tasks(self) -> int:
        """
        Remove all failed tasks from the task list.
        
        Returns:
            Number of tasks removed
        """
        failed_tasks = [
            task_id for task_id, task in self.tasks.items()
            if task.status == DownloadTaskStatus.FAILED
        ]
        
        for task_id in failed_tasks:
            del self.tasks[task_id]
        
        count = len(failed_tasks)
        if count > 0:
            self.logger.info(f"Cleared {count} failed tasks")
        
        return count
    
    def _notify_task_update(self, task: DownloadTask):
        """
        Notify listeners about task updates.
        
        Args:
            task: The task that was updated
        """
        if self.on_task_update:
            try:
                self.on_task_update(task)
            except Exception as e:
                self.logger.error(f"Error in task update callback: {e}", exc_info=True)
    
    async def on_start(self):
        """Called when the service starts."""
        self.logger.info("Download manager service starting")
        
    async def on_stop(self):
        """Called when the service stops."""
        self.logger.info("Download manager service stopping")
        # Cancel all active downloads
        for task_id in list(self.active_downloads):
            self.cancel_task(task_id)
