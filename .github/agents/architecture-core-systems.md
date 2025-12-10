---
name: CFMS Client Architecture & Core Systems Developer
description: Expert in the overall architecture, design patterns, and core systems of CFMS Client NEXT - a Flet-based document management system client using WebSocket communication.
---

## Repository Overview

CFMS Client NEXT is a confidential document management system client built on the Flet framework (Python UI framework based on Flutter). It communicates with a server via WebSocket connections for secure file management operations.

### Technology Stack
- **Framework**: Flet (≥0.70.0.dev6671) - Python UI framework
- **Communication**: WebSockets with SSL/TLS support
- **Encryption**: PyCryptodome for AES encryption
- **Platforms**: Desktop (Windows, macOS, Linux), Web, and Mobile (Android, iOS)
- **Python Version**: ≥3.12

## Directory Structure

```
src/
├── assets/                    # Application assets (fonts, icons, images)
├── include/
│   ├── classes/              # Core data classes and configuration
│   │   ├── config.py         # Singleton AppConfig for global state
│   │   ├── datacls.py        # Data classes (User)
│   │   ├── response.py       # Response data class
│   │   ├── preferences.py    # User preferences management
│   │   ├── changelog.py      # Version change tracking
│   │   ├── exceptions/       # Custom exception classes
│   │   └── ui/
│   │       └── enum.py       # UI enums (SortMode, SortOrder)
│   ├── constants.py          # Application-wide constants
│   ├── controllers/          # Business logic controllers
│   │   ├── base.py           # BaseController generic class
│   │   ├── connect.py        # Connection management
│   │   ├── login.py          # Login operations
│   │   ├── explorer/         # File explorer controllers
│   │   ├── contextmenus/     # Context menu handlers
│   │   └── dialogs/          # Dialog controllers
│   ├── ui/                   # User interface components
│   │   ├── constants.py      # UI constants
│   │   ├── controls/         # Reusable UI controls
│   │   │   ├── buttons/      # Custom buttons
│   │   │   ├── components/   # Complex UI components
│   │   │   ├── contextmenus/ # Context menu implementations
│   │   │   ├── dialogs/      # Dialog implementations
│   │   │   ├── menus/        # Menu implementations
│   │   │   └── views/        # Main view components
│   │   ├── locale/           # Internationalization files
│   │   │   ├── en/           # English translations
│   │   │   ├── zh_CN/        # Simplified Chinese translations
│   │   │   └── messages.pot  # Translation template
│   │   ├── models/           # Flet-Model route models
│   │   │   ├── connect.py    # Connection screen
│   │   │   ├── login.py      # Login screen
│   │   │   ├── home.py       # Home screen
│   │   │   ├── manage.py     # Management screen
│   │   │   └── settings/     # Settings screens
│   │   └── util/             # UI utility functions
│   ├── util/                 # Core utility functions
│   │   ├── connect.py        # WebSocket connection utilities
│   │   ├── requests.py       # Request/response handling
│   │   ├── transfer.py       # File upload/download
│   │   ├── locale.py         # Localization utilities
│   │   ├── path.py           # Path manipulation
│   │   ├── user.py           # User management
│   │   ├── create.py         # Resource creation
│   │   └── upgrade/          # Application update utilities
│   └── issues/               # Known UI framework issues/workarounds
└── main.py                   # Application entry point

```

## Core Architecture Patterns

### 1. Singleton Pattern: AppConfig
The `AppConfig` class (`include/classes/config.py`) is a thread-safe singleton that manages global application state:
- Server connection information
- User authentication (username, token, permissions, groups)
- WebSocket connection instance
- User preferences loaded from YAML
- Permission handler service

**Key Attributes:**
```python
server_address: Optional[str]          # WebSocket server URL
server_info: dict[str, Any]            # Server metadata
disable_ssl_enforcement: bool          # SSL validation toggle
username, token, token_exp             # Authentication
user_permissions: list[str]            # User permission strings
user_groups: list[str]                 # User group memberships
conn: Optional[ClientConnection]       # Active WebSocket connection
preferences: dict                      # User preferences from YAML
```

### 2. MVC Pattern with Flet-Model
The application uses the Flet-Model library for routing and view management:
- **Models** (`include/ui/models/`): Route handlers decorated with `@route()`
- **Views** (`include/ui/controls/views/`): UI layout components
- **Controllers** (`include/controllers/`): Business logic handlers extending `BaseController`

Example Model:
```python
@route("connect")
class ConnectToServerModel(Model):
    def __init__(self, page: ft.Page, router: Router):
        self.appbar = ft.AppBar(...)
        self.controls = [ConnectForm(), ...]
```

### 3. Generic BaseController Pattern
All controllers inherit from `BaseController[T]` where T is the control type:
```python
class BaseController(Generic[T]):
    control: T                    # The UI control being managed
    app_config: AppConfig        # Singleton config instance
```

This provides consistent access to global state and type-safe control references.

### 4. Async/Await Architecture
All I/O operations are asynchronous:
- WebSocket communication
- File transfers
- UI updates (via `page.update()` or yielding in async generators)
- Request handling with automatic retry on connection loss

### 5. Request/Response Pattern
WebSocket communication uses a structured JSON protocol:
```python
# Request format
{
    "action": "action_name",
    "data": {...},
    "message": "optional message",
    "username": "user",
    "token": "auth_token"
}

# Response format (Response dataclass)
Response(
    code: int,              # HTTP-like status code
    message: str,           # Human-readable message
    data: dict[str, Any],   # Response payload
    timestamp: float        # Unix timestamp
)
```

## Key System Components

### Connection Management (`include/util/connect.py`)
- `get_connection()`: Establishes WebSocket connections with SSL/proxy support
- Uses integrated CA certificates for SSL verification
- Configurable SSL enforcement (can disable for testing)

### Request Handling (`include/util/requests.py`)
- `do_request()`: Execute requests with automatic retry on connection failure
- `do_request_2()`: Returns typed `Response` objects
- `_request()`: Low-level request execution with connection locking
- Uses `WeakKeyDictionary` to store per-connection locks

### File Transfer (`include/util/transfer.py`)
- `upload_file_to_server()`: Chunked file upload with progress tracking
- `batch_upload_file_to_server()`: Batch upload with error handling
- `download_file_from_server()`: Encrypted file download with AES
- Uses memory-mapped I/O for efficient SHA256 calculation
- Supports AES encryption/decryption for file transfers

### Application Entry Point (`main.py`)
- Loads user language preferences
- Sets up localization (gettext)
- Configures page settings (theme, fonts, window size)
- Registers keyboard shortcuts (Ctrl+W: debugger, Ctrl+Q: dev dialog)
- Navigates to initial `/connect` route

## Configuration and Preferences

### Constants (`include/constants.py`)
- Version information: `APP_VERSION`, `BUILD_VERSION`, `PROTOCOL_VERSION`
- Path configuration: `RUNTIME_PATH`, `FLET_APP_STORAGE_TEMP`, `FLET_APP_STORAGE_DATA`
- Integrated CA certificates for SSL
- GitHub repository reference

### User Preferences
- Stored in YAML format at `{FLET_APP_STORAGE_DATA}/preferences.yaml`
- Loaded into `AppConfig.preferences` dictionary
- Contains settings like language, proxy configuration, connection settings

## Exception Handling

Custom exception hierarchy:
- `include/classes/exceptions/request.py`: `InvalidResponseError` for bad responses
- `include/classes/exceptions/transmission.py`: `FileHashMismatchError`, `FileSizeMismatchError`

## Best Practices for Development

1. **State Management**: Always use `AppConfig()` singleton for shared state
2. **Async Operations**: All I/O must be async; use `await` and `async def`
3. **Error Handling**: Wrap WebSocket operations in try/except for `ConnectionClosed`
4. **Localization**: Import and use `get_translation()` for all user-facing strings
5. **Type Safety**: Use type hints; controllers use Generic[T] pattern
6. **Connection Resilience**: Use `do_request()` which auto-retries on connection loss
7. **UI Updates**: Call `page.update()` or `control.update()` after state changes
8. **Threading**: AppConfig uses locks for thread-safety

## Critical Implementation Details

- **Protocol Version**: Current version is 4 (`PROTOCOL_VERSION`)
- **Window Size**: Default 1024x768, non-resizable by default
- **Theme**: Dark mode with custom gradient background
- **Font**: Source Han Serif SC (Chinese serif font)
- **Build Tool**: Uses `flet build` for platform-specific packages
- **Package Manager**: Supports both `uv` and `poetry`

## Known Issues Directory
The `include/issues/` directory contains workarounds for known Flet framework bugs:
- `contextmenu.py`: Context menu issues
- `dialog.py`: Dialog display issues
- `dropdown.py`: Dropdown control issues
- `gesturedetector.py`: Gesture detection issues

Future agents should check this directory when encountering UI framework bugs.
