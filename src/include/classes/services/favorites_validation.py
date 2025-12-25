"""Service for validating favorites (documents and folders) still exist on the server."""

import asyncio
import inspect
from typing import Set, Callable, List

from include.classes.services.base import BaseService
from include.classes.config import AppShared
from include.util.requests import do_request_2
import threading

__all__ = ["FavoritesValidationService"]


class FavoritesValidationService(BaseService):
    """
    Background service that validates whether favorited items still exist on the server.
    
    This service periodically checks if documents and directories marked as favorites
    still exist on the server. Items that no longer exist are marked as invalid
    to provide better user experience and prevent errors when accessing them.
    
    Attributes:
        app_shared: Shared application state containing user preferences
        invalid_files: Set of file IDs that no longer exist on the server
        invalid_directories: Set of directory IDs that no longer exist on the server
        validation_in_progress: Flag indicating if validation is currently running
    """
    
    def __init__(
        self,
        app_shared: AppShared,
        enabled: bool = True,
        interval: float = 300.0,  # Check every 5 minutes by default
    ):
        """
        Initialize the favorites validation service.
        
        Args:
            app_shared: Shared application state
            enabled: Whether the service is enabled
            interval: Time in seconds between validation checks
            check_on_mount: Whether to check on first mount (when user views homepage)
        """
        super().__init__(name="favorites_validation", enabled=enabled, interval=interval)
        self.app_shared = app_shared
        
        # Track invalid items
        self.invalid_files: Set[str] = set()
        self.invalid_directories: Set[str] = set()
        
        # Track validation state
        self.validation_in_progress = False
        self._first_validation_done = False
        
        # Callbacks to be called after validation completes
        self._on_validation_complete_callbacks: List[Callable] = []

    @property
    def first_validation_done(self) -> bool:
        return self._first_validation_done
    
    async def execute(self):
        """
        Execute the validation check for all favorited items.
        
        This method is called periodically by the base service.
        It checks both files and directories in the user's favorites.
        """
        # Skip if user is not logged in
        if not self.app_shared.username or not self.app_shared.token:
            self.logger.debug("Skipping validation - user not logged in")
            return
        
        # Skip if no user preferences loaded
        if not self.app_shared.user_perference:
            self.logger.debug("Skipping validation - no user preferences")
            return
        
        await self._perform_validation()
    
    async def _perform_validation(self) -> None:
        """
        Perform the actual validation of favorite items.
        
        This method checks each favorited file and directory to see if it
        still exists on the server.
        """
        if self.validation_in_progress:
            self.logger.debug("Validation already in progress, skipping")
            return
        
        self.validation_in_progress = True
        
        try:
            if not self.app_shared.user_perference:
                return
            
            favourites = self.app_shared.user_perference.favourites
            favorite_files = favourites.get("files", {})
            favorite_directories = favourites.get("directories", {})
            
            self.logger.info(
                f"Starting validation of {len(favorite_files)} files and "
                f"{len(favorite_directories)} directories"
            )

            # TODO: Consider batching requests for efficiency
            
            # Validate files
            for file_id in favorite_files:
                await self._validate_file(file_id)
            
            # Validate directories
            for dir_id in favorite_directories:
                await self._validate_directory(dir_id)
            
            self._first_validation_done = True
            self.logger.info(
                f"Validation complete. Invalid items - Files: {len(self.invalid_files)}, "
                f"Directories: {len(self.invalid_directories)}"
            )
            
            # Call all registered callbacks
            for callback in self._on_validation_complete_callbacks:
                try:
                    if inspect.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception as e:
                    self.logger.error(f"Error in validation callback: {e}", exc_info=True)
            
        except Exception as e:
            self.logger.error(f"Error during validation: {e}", exc_info=True)
        finally:
            self.validation_in_progress = False
    
    async def _validate_file(self, file_id: str) -> None:
        """
        Validate if a specific file still exists on the server.
        
        Args:
            file_id: ID of the file to validate
        """
        try:
            response = await do_request_2(
                action="get_document",
                data={"document_id": file_id},
                username=self.app_shared.username,
                token=self.app_shared.token,
                max_retries=1,  # Don't retry too much for validation
            )
            
            if response.code == 200:
                # File exists, remove from invalid set if it was there
                self.invalid_files.discard(file_id)
                self.logger.debug(f"File {file_id} is valid")
            else:
                # File doesn't exist or error occurred
                self.invalid_files.add(file_id)
                self.logger.warning(
                    f"File {file_id} is invalid: ({response.code}) {response.message}"
                )
                
        except Exception as e:
            # On error, mark as invalid to be safe
            self.invalid_files.add(file_id)
            self.logger.error(f"Error validating file {file_id}: {e}")
    
    async def _validate_directory(self, dir_id: str) -> None:
        """
        Validate if a specific directory still exists on the server.
        
        Args:
            dir_id: ID of the directory to validate
        """
        try:
            response = await do_request_2(
                action="list_directory",
                data={"folder_id": dir_id},
                username=self.app_shared.username,
                token=self.app_shared.token,
                max_retries=1,  # Don't retry too much for validation
            )
            
            if response.code == 200:
                # Directory exists, remove from invalid set if it was there
                self.invalid_directories.discard(dir_id)
                self.logger.debug(f"Directory {dir_id} is valid")
            else:
                # Directory doesn't exist or error occurred
                self.invalid_directories.add(dir_id)
                self.logger.warning(
                    f"Directory {dir_id} is invalid: ({response.code}) {response.message}"
                )
                
        except Exception as e:
            # On error, mark as invalid to be safe
            self.invalid_directories.add(dir_id)
            self.logger.error(f"Error validating directory {dir_id}: {e}")
    
    def is_file_valid(self, file_id: str) -> bool:
        """
        Check if a file is valid (exists on server).
        
        Args:
            file_id: ID of the file to check
            
        Returns:
            True if file is valid, False if it's marked as invalid
        """
        return file_id not in self.invalid_files
    
    def is_directory_valid(self, dir_id: str) -> bool:
        """
        Check if a directory is valid (exists on server).
        
        Args:
            dir_id: ID of the directory to check
            
        Returns:
            True if directory is valid, False if it's marked as invalid
        """
        return dir_id not in self.invalid_directories
    
    def mark_file_invalid(self, file_id: str) -> None:
        """
        Mark a file as invalid (typically called when an operation fails).
        
        Args:
            file_id: ID of the file to mark as invalid
        """
        self.invalid_files.add(file_id)
        self.logger.info(f"File {file_id} marked as invalid")
    
    def mark_directory_invalid(self, dir_id: str) -> None:
        """
        Mark a directory as invalid (typically called when an operation fails).
        
        Args:
            dir_id: ID of the directory to mark as invalid
        """
        self.invalid_directories.add(dir_id)
        self.logger.info(f"Directory {dir_id} marked as invalid")
    
    def register_on_validation_complete(self, callback) -> None:
        """
        Register a callback to be called when validation completes.
        
        The callback will be called after each validation run.
        Callback can be sync or async function.
        
        Args:
            callback: Function to call after validation completes
        """
        if callback not in self._on_validation_complete_callbacks:
            self._on_validation_complete_callbacks.append(callback)
    
    def unregister_on_validation_complete(self, callback) -> None:
        """
        Unregister a callback.
        
        Args:
            callback: Function to remove from callbacks
        """
        if callback in self._on_validation_complete_callbacks:
            self._on_validation_complete_callbacks.remove(callback)
    
    def trigger_validation_async(self) -> None:
        """
        Trigger validation to run in the background without blocking.
        """
        if not (self.app_shared.username and self.app_shared.token):
            return

        if self.validation_in_progress:
            self.logger.debug("Validation already in progress, skipping async trigger")
            return

        coro = self._perform_validation()

        # If there's a running event loop in this thread, schedule as a task
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            try:
                loop.create_task(coro)
                return
            except Exception as e:
                self.logger.warning(f"Failed to create task on running loop: {e}")

        # Fallback: try the default event loop (for older code patterns)
        try:
            loop2 = asyncio.get_event_loop()
            if loop2.is_running():
                try:
                    loop2.create_task(coro)
                    return
                except Exception as e:
                    self.logger.warning(f"Failed to create task on default loop: {e}")
        except RuntimeError:
            pass

        # Final fallback: run the coroutine in a dedicated background thread

        def _thread_runner():
            try:
                asyncio.run(coro)
            except Exception as e:
                self.logger.error(f"Async validation failed in thread: {e}", exc_info=True)

        threading.Thread(target=_thread_runner, daemon=True).start()

