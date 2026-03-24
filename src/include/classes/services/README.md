# Service Architecture

This directory contains the background service infrastructure for CFMS Client.

## Overview

The service architecture provides a way to run long-running background tasks that operate independently of the UI. Services are managed centrally through the `ServiceManager` singleton and can be started, stopped, and monitored.

## Components

### BaseService (`base.py`)

Abstract base class for all background services. Provides:
- Automatic lifecycle management (start, stop, restart)
- Periodic execution with configurable intervals
- Error handling and recovery
- Status tracking
- Logging integration

**Key Methods:**
- `execute()` - Override this to implement your service logic (called periodically)
- `on_start()` - Optional initialization hook
- `on_stop()` - Optional cleanup hook
- `on_error(error)` - Optional error handling hook

### ServiceManager (`manager.py`)

Singleton manager for all services. Provides:
- Service registration and unregistration
- Centralized start/stop/restart control
- Query service status
- Bulk operations (start_all, stop_all)

### AutoUpdateService (`autoupdate.py`)

Concrete implementation that checks for application updates periodically.

**Features:**
- Configurable check interval (default: 6 hours)
- Optional immediate check on startup
- User notifications via snackbar
- Manual check triggering

### ServerStreamHandleService (`server_stream.py`)

Service that accepts and dispatches server-initiated (push) messages sent proactively by the server without a preceding client request.

**Features:**
- Listens for server-initiated streams on the active `AsyncMultiplexConnection`
- Single-connection model: only one connection is active at a time
- Seamlessly switches to a new connection when its `connection` property is updated
- Automatically detects and clears disconnected connections
- Handler registry: register callbacks by action name or as catch-all fallback handlers
- Concurrent message dispatch: slow handlers do not block other incoming messages

**Usage:**
```python
# Get the service
server_stream_service = app_shared.service_manager.get_service(
    "server_stream", ServerStreamHandleService
)

# Register a handler for a specific server action
async def on_notify(action: str, data: dict) -> None:
    print(f"Received server notification: {data}")

server_stream_service.add_handler("notify", on_notify)

# Register a fallback handler for any action
async def catch_all(action: str, data: dict) -> None:
    print(f"Unknown server push: action={action}, data={data}")

server_stream_service.add_fallback_handler(catch_all)

# Hand the active connection to the service (called automatically in connect/reconnect flows)
server_stream_service.set_connection(conn)
```

### DownloadManagerService (`download.py`)

Centralized service for managing file downloads from the server.

**Features:**
- Concurrent download management with configurable limits (default: 3)
- Task queue with automatic scheduling
- Real-time progress tracking and status updates
- Task lifecycle management (add, cancel, query)
- Multiple callback support for UI updates
- Automatic retry and error handling
- Integration with existing file transfer utilities

**Task States:**
- PENDING - Task is queued, waiting to start
- DOWNLOADING - File is being downloaded from server
- DECRYPTING - Downloaded chunks are being decrypted
- VERIFYING - File integrity is being verified
- COMPLETED - Download completed successfully
- FAILED - Download failed with error
- CANCELLED - Download was cancelled by user

**Usage:**
```python
# Get the download service
download_service = AppShared().service_manager.get_service("download_manager")

# Add a download task
task = download_service.add_task(
    task_id=server_task_id,
    file_id=document_id,
    filename="document.pdf",
    file_path="/path/to/save/document.pdf"
)

# Monitor progress via callback
def on_task_update(task: DownloadTask):
    print(f"{task.filename}: {task.progress * 100:.1f}%")

download_service.add_task_update_callback(on_task_update)

# Cancel a download
download_service.cancel_task(task_id)

# Query tasks
all_tasks = download_service.get_all_tasks()
active_tasks = download_service.get_tasks_by_status(DownloadTaskStatus.DOWNLOADING)

# Clean up completed tasks
download_service.clear_completed_tasks()
```

### TokenRefreshService (`token_refresh.py`)

Automatic token refresh service that monitors authentication token expiration and renews tokens before they expire.

**Features:**
- Periodic checking of token expiration time
- Automatic token refresh before expiration
- Configurable refresh threshold (default: 5 minutes)
- Seamless token renewal without user interaction
- Detailed logging of token lifecycle

**Configuration:**
- `interval`: Check interval in seconds (default: 60 seconds)
- `refresh_threshold`: Time before expiration to trigger refresh (default: 300 seconds/5 minutes)

**How it works:**
1. Service checks token expiration every minute (configurable)
2. When remaining time falls below threshold, sends `refresh_token` request to server
3. Server responds with new token and expiration time in response data
4. Service updates `AppShared` with new credentials automatically

**Usage:**
The service is automatically registered and started when the application launches. No manual interaction is required.

```python
# Service is registered in main.py
token_refresh_service = TokenRefreshService(
    enabled=True,
    interval=60.0,  # Check every minute
    refresh_threshold=300.0,  # Refresh when < 5 minutes remaining
)
service_manager.register(token_refresh_service)
```

## Usage

### Creating a New Service

```python
from include.classes.services.base import BaseService

class MyService(BaseService):
    def __init__(self, enabled=True, interval=60.0):
        super().__init__(
            name="my_service",
            enabled=enabled,
            interval=interval  # Execute every 60 seconds
        )
    
    async def execute(self):
        """This method is called periodically."""
        # Your service logic here
        self.logger.info("MyService is running!")
    
    async def on_start(self):
        """Optional: Called when service starts."""
        self.logger.info("MyService starting up...")
    
    async def on_stop(self):
        """Optional: Called when service stops."""
        self.logger.info("MyService shutting down...")
```

### Registering and Starting Services

Services are registered in `main.py`:

```python
from include.classes.services.manager import ServiceManager
from include.classes.services.autoupdate import AutoUpdateService

# Get the singleton service manager
service_manager = ServiceManager()

# Create and register your service
my_service = MyService(enabled=True, interval=120.0)
service_manager.register(my_service)

# Start all services
await service_manager.start_all()
```

### Accessing Services from Anywhere

Services can be accessed through the `AppShared` singleton:

```python
from include.classes.config import AppShared

# Get the service manager
service_manager = AppShared().service_manager

# Get a specific service
autoupdate = service_manager.get_service("autoupdate")

# Check if it's running
if autoupdate and autoupdate.is_running():
    # Manually trigger a check
    await autoupdate.check_now()
```

### Controlling Services

```python
from include.classes.config import AppShared

service_manager = AppShared().service_manager

# Start a specific service
await service_manager.start_service("my_service")

# Stop a specific service
await service_manager.stop_service("my_service")

# Restart a service
await service_manager.restart_service("my_service")

# Get all running services
running = service_manager.get_running_services()
for name, service in running.items():
    print(f"{name}: {service.status}")
```

## Service Lifecycle

1. **STOPPED** - Initial state, service is not running
2. **STARTING** - Service is initializing (calls `on_start()`)
3. **RUNNING** - Service is active, `execute()` called periodically
4. **STOPPING** - Service is shutting down (calls `on_stop()`)
5. **ERROR** - Service encountered a fatal error

Services automatically transition between states. The `execute()` method is called repeatedly based on the `interval` setting.

## Error Handling

Services have built-in error recovery:
- Errors in `execute()` are caught and logged
- The `on_error(error)` hook is called for custom handling
- The service continues running after non-fatal errors
- Fatal errors during start/stop transition to ERROR state

## Best Practices

1. **Keep execute() fast**: Long-running operations should be broken into chunks or use executors
2. **Use async/await**: All service methods should be async
3. **Log appropriately**: Use `self.logger` for all logging
4. **Handle errors gracefully**: Implement `on_error()` for custom error handling
5. **Clean up resources**: Use `on_stop()` to release resources
6. **Test service behavior**: Test start, stop, and error conditions

## Example: Auto-Update Service

The `AutoUpdateService` demonstrates best practices:

```python
class AutoUpdateService(BaseService):
    def __init__(self, page=None, enabled=True, interval=3600.0):
        super().__init__(name="autoupdate", enabled=enabled, interval=interval)
        self.page = page
        self.last_checked_version = None
    
    async def execute(self):
        """Check for updates periodically."""
        # Use executor for blocking I/O
        loop = asyncio.get_running_loop()
        latest = await loop.run_in_executor(None, get_latest_release)
        
        if latest and is_new_version(BUILD_VERSION, latest.version):
            if self.last_checked_version != latest.version:
                self.last_checked_version = latest.version
                await self._notify_update_available(latest)
    
    async def check_now(self):
        """Manually trigger an immediate check."""
        # Bypass the interval timer
        return await self.execute()
```

## Testing

See `test_services.py` for examples of testing service functionality.

## Future Enhancements

Potential future improvements:
- Service dependencies (start services in order)
- Service health checks
- Configurable restart policies
- Service metrics and monitoring
- Persistence of service state
