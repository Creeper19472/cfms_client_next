"""
Example service demonstrating how to create custom background services.

This file serves as a template and example for developers who want to add
new background services to the application.
"""

from include.classes.services.base import BaseService

__all__ = ["ExampleService"]


class ExampleService(BaseService):
    """
    Example service that demonstrates the service architecture.
    
    This service periodically performs a simple task and demonstrates
    best practices for implementing custom services.
    
    To use this service:
    1. Copy this file and rename it to your service name
    2. Implement the execute() method with your logic
    3. Register the service in main.py
    
    Example:
        ```python
        # In main.py
        from include.classes.services.example import ExampleService
        
        example_service = ExampleService(
            enabled=True,
            interval=300.0,  # Run every 5 minutes
        )
        service_manager.register(example_service)
        ```
    """
    
    def __init__(
        self,
        enabled: bool = True,
        interval: float = 60.0,
        custom_param: str = "default",
    ):
        """
        Initialize the example service.
        
        Args:
            enabled: Whether the service should start when registered
            interval: How often to execute (in seconds)
            custom_param: Example of a custom parameter
        """
        # Always call super().__init__ with the service name
        super().__init__(
            name="example",  # Unique service identifier
            enabled=enabled,
            interval=interval,
        )
        
        # Store any custom parameters
        self.custom_param = custom_param
        self.execution_count = 0
    
    async def on_start(self):
        """
        Called when the service starts.
        
        Use this for initialization tasks like:
        - Setting up connections
        - Loading configuration
        - Initializing resources
        """
        self.logger.info(
            f"Example service starting with interval={self.interval}s, "
            f"custom_param='{self.custom_param}'"
        )
        self.execution_count = 0
    
    async def execute(self):
        """
        Main service logic - called periodically based on interval.
        
        This method should:
        - Be async (use await for I/O operations)
        - Be relatively quick (long operations should use executors)
        - Handle its own errors when possible
        - Use self.logger for logging
        """
        self.execution_count += 1
        
        self.logger.info(
            f"Example service executing (#{self.execution_count}): "
            f"param='{self.custom_param}'"
        )
        
        # Example: Perform some work
        # await self._do_work()
        
        # Example: Use executor for blocking I/O
        # loop = asyncio.get_running_loop()
        # result = await loop.run_in_executor(None, self._blocking_operation)
    
    async def on_stop(self):
        """
        Called when the service stops.
        
        Use this for cleanup tasks like:
        - Closing connections
        - Saving state
        - Releasing resources
        """
        self.logger.info(
            f"Example service stopping after {self.execution_count} executions"
        )
    
    async def on_error(self, error: Exception):
        """
        Called when an error occurs during execute().
        
        Args:
            error: The exception that was raised
        
        Use this for:
        - Custom error handling
        - Error recovery
        - Notifications
        """
        self.logger.error(
            f"Example service encountered an error: {error}",
            exc_info=True
        )
        
        # Example: Could implement retry logic, notifications, etc.
        # if isinstance(error, ConnectionError):
        #     await self._handle_connection_error()
    
    # Private helper methods (optional)
    
    async def _do_work(self):
        """Example private method for organizing code."""
        # Implement your actual service logic here
        pass
    
    def _blocking_operation(self):
        """
        Example blocking operation that should run in executor.
        
        Returns:
            Result of the operation
        """
        # Blocking I/O or CPU-intensive work here
        return "result"


# Additional example: Stateful service
class StatefulExampleService(BaseService):
    """
    Example service that maintains state between executions.
    """
    
    def __init__(self, enabled: bool = True, interval: float = 60.0):
        super().__init__(name="stateful_example", enabled=enabled, interval=interval)
        self.state_data = {}
        self.last_result = None
    
    async def on_start(self):
        """Load or initialize state."""
        self.logger.info("Loading state...")
        # Could load from file, database, etc.
        self.state_data = {"count": 0, "items": []}
    
    async def execute(self):
        """Update state on each execution."""
        self.state_data["count"] += 1
        self.state_data["items"].append(f"item_{self.state_data['count']}")
        
        self.logger.info(f"State updated: count={self.state_data['count']}")
        
        # Keep only last 10 items
        if len(self.state_data["items"]) > 10:
            self.state_data["items"] = self.state_data["items"][-10:]
    
    async def on_stop(self):
        """Save state before stopping."""
        self.logger.info("Saving state...")
        # Could save to file, database, etc.
        self.logger.info(f"Final state: {self.state_data}")
