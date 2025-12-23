"""Base service class for background services."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional

__all__ = ["BaseService", "ServiceStatus"]

# Configuration constants
DEFAULT_STOP_TIMEOUT = 10.0  # Seconds to wait for graceful shutdown


class ServiceStatus:
    """Enumeration of service states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class BaseService(ABC):
    """
    Abstract base class for background services.
    
    Services are long-running background tasks that can be started, stopped,
    and monitored. Each service runs in its own asyncio task and can implement
    custom logic for initialization, execution, and cleanup.
    
    Attributes:
        name: Unique identifier for the service
        enabled: Whether the service should be running
        status: Current service status
        interval: Time in seconds between service executions (for periodic services)
        logger: Logger instance for this service
    """
    
    def __init__(self, name: str, enabled: bool = True, interval: float = 60.0, stop_timeout: float = DEFAULT_STOP_TIMEOUT):
        """
        Initialize the service.
        
        Args:
            name: Unique service name
            enabled: Whether service is enabled by default
            interval: Execution interval in seconds for periodic tasks
            stop_timeout: Seconds to wait for graceful shutdown before forcing
        """
        self.name = name
        self.enabled = enabled
        self.interval = interval
        self.stop_timeout = stop_timeout
        self.status = ServiceStatus.STOPPED
        self.logger = logging.getLogger(f"service.{name}")
        
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
    
    async def start(self) -> bool:
        """
        Start the service.
        
        Returns:
            True if service started successfully, False otherwise
        """
        if not self.enabled:
            self.logger.info(f"Service '{self.name}' is disabled, skipping start")
            return False
            
        if self.status == ServiceStatus.RUNNING:
            self.logger.warning(f"Service '{self.name}' is already running")
            return False
        
        try:
            self.status = ServiceStatus.STARTING
            self.logger.info(f"Starting service '{self.name}'")
            
            # Clear stop event
            self._stop_event.clear()
            
            # Call subclass initialization
            await self.on_start()
            
            # Create and start the main service task
            self._task = asyncio.create_task(self._run())
            
            self.status = ServiceStatus.RUNNING
            self.logger.info(f"Service '{self.name}' started successfully")
            return True
            
        except Exception as e:
            self.status = ServiceStatus.ERROR
            self.logger.error(f"Failed to start service '{self.name}': {e}", exc_info=True)
            return False
    
    async def stop(self) -> bool:
        """
        Stop the service.
        
        Returns:
            True if service stopped successfully, False otherwise
        """
        if self.status != ServiceStatus.RUNNING:
            self.logger.warning(f"Service '{self.name}' is not running")
            return False
        
        try:
            self.status = ServiceStatus.STOPPING
            self.logger.info(f"Stopping service '{self.name}'")
            
            # Signal the service to stop
            self._stop_event.set()
            
            # Wait for the task to complete with timeout
            if self._task:
                try:
                    await asyncio.wait_for(self._task, timeout=self.stop_timeout)
                except asyncio.TimeoutError:
                    self.logger.warning(f"Service '{self.name}' did not stop gracefully, cancelling")
                    self._task.cancel()
                    try:
                        await self._task
                    except asyncio.CancelledError:
                        pass
            
            # Call subclass cleanup
            await self.on_stop()
            
            self.status = ServiceStatus.STOPPED
            self.logger.info(f"Service '{self.name}' stopped successfully")
            return True
            
        except Exception as e:
            self.status = ServiceStatus.ERROR
            self.logger.error(f"Failed to stop service '{self.name}': {e}", exc_info=True)
            return False
    
    async def restart(self) -> bool:
        """
        Restart the service.
        
        Returns:
            True if service restarted successfully, False otherwise
        """
        self.logger.info(f"Restarting service '{self.name}'")
        if self.status == ServiceStatus.RUNNING:
            await self.stop()
        return await self.start()
    
    async def _run(self):
        """
        Main service loop. Should not be overridden by subclasses.
        
        Calls execute() method periodically based on the interval setting.
        """
        try:
            while not self._stop_event.is_set():
                try:
                    # Execute the service logic
                    await self.execute()
                    
                except Exception as e:
                    self.logger.error(f"Error in service '{self.name}' execution: {e}", exc_info=True)
                    # Call error handler
                    await self.on_error(e)
                
                # Wait for the interval or until stop is requested
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self.interval
                    )
                except asyncio.TimeoutError:
                    # Timeout is expected, continue loop
                    pass
                    
        except asyncio.CancelledError:
            self.logger.info(f"Service '{self.name}' task was cancelled")
            raise
        except Exception as e:
            self.status = ServiceStatus.ERROR
            self.logger.error(f"Fatal error in service '{self.name}': {e}", exc_info=True)
    
    @abstractmethod
    async def execute(self):
        """
        Execute the main service logic.
        
        This method is called periodically based on the interval setting.
        Subclasses must implement this method with their specific logic.
        """
        pass
    
    async def on_start(self):
        """
        Called when the service is starting.
        
        Override this method to implement custom initialization logic.
        """
        pass
    
    async def on_stop(self):
        """
        Called when the service is stopping.
        
        Override this method to implement custom cleanup logic.
        """
        pass
    
    async def on_error(self, error: Exception):
        """
        Called when an error occurs during execution.
        
        Override this method to implement custom error handling.
        
        Args:
            error: The exception that occurred
        """
        pass
    
    def is_running(self) -> bool:
        """
        Check if the service is currently running.
        
        Returns:
            True if service is running, False otherwise
        """
        return self.status == ServiceStatus.RUNNING
