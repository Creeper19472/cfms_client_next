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
│   │   ├── shared.py         # Singleton AppShared for global state
│   │   ├── datacls.py        # Data classes
│   │   ├── response.py       # Response data class
│   │   ├── preferences.py    # User preferences management
│   │   ├── changelog.py      # Version change tracking
│   │   ├── twofa.py          # Two-factor authentication helpers
│   │   ├── version.py        # ChannelType enum for release channels
│   │   ├── exceptions/       # Custom exception classes
│   │   ├── services/         # Background service framework
│   │   │   ├── base.py       # BaseService abstract class
│   │   │   ├── manager.py    # ServiceManager singleton
│   │   │   ├── autoupdate.py # Auto-update service
│   │   │   ├── download.py   # Download manager service
│   │   │   ├── token_refresh.py        # Token refresh service
│   │   │   └── favorites_validation.py # Favorites validation service
│   │   └── ui/
│   │       └── enum.py       # UI enums (SortMode, SortOrder)
│   ├── constants.py          # Application-wide constants
│   ├── controllers/          # Business logic controllers
│   │   ├── base.py           # Controller generic class
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
│   │   ├── issues/           # Known UI framework issues/workarounds
│   │   ├── locale/           # Internationalization files
│   │   │   ├── zh_CN/        # Simplified Chinese translations
│   │   │   └── messages.pot  # Translation template
│   │   ├── models/           # Flet-Model route models
│   │   │   ├── connect.py    # Connection screen
│   │   │   ├── login.py      # Login screen
│   │   │   ├── home.py       # Home screen
│   │   │   ├── manage.py     # Management screen
│   │   │   ├── about.py      # About screen
│   │   │   ├── debugging.py  # Debugging view
│   │   │   ├── settings/     # Settings screens
│   │   │   │   ├── overview.py    # Settings overview
│   │   │   │   ├── connection.py  # Connection settings
│   │   │   │   ├── language.py    # Language settings
│   │   │   │   ├── safety.py      # Safety settings
│   │   │   │   ├── twofa.py       # Two-factor auth settings
│   │   │   │   └── updates.py     # Updates settings
│   │   │   └── wizards/      # Setup wizards
│   │   │       └── welcome.py
│   │   └── util/             # UI utility functions
│   └── util/                 # Core utility functions
│       ├── avatar.py         # Avatar management
│       ├── batch_operations.py # Batch file operations
│       ├── changelog_parser.py # Changelog parsing
│       ├── connect.py        # WebSocket connection utilities
│       ├── create.py         # Resource creation
│       ├── hash.py           # Hash utilities
│       ├── kdf.py            # Key derivation functions
│       ├── locale.py         # Localization utilities
│       ├── passwd.py         # Password utilities
│       ├── requests.py       # Request/response handling
│       ├── transfer.py       # File upload/download
│       ├── tree.py           # Directory tree utilities
│       ├── twofa.py          # 2FA utilities
│       ├── upgrade/          # Application update utilities
│       └── userpref.py       # User preference management
└── main.py                   # Application entry point

```

## Core Architecture Patterns

### 1. Singleton Pattern: AppShared
The `AppShared` class (`include/classes/shared.py`) is a thread-safe singleton that manages global application state:
- Server connection information
- User authentication (username, token, permissions, groups)
- WebSocket connection instance
- User preferences loaded from YAML
- Permission handler service
- Background service manager

**Key Attributes:**
```python
is_mobile: bool                        # Whether running on mobile
is_production: bool                    # Whether running from packaged runtime
server_address: Optional[str]          # WebSocket server URL
server_info: dict[str, Any]            # Server metadata
disable_ssl_enforcement: bool          # SSL validation toggle
username, token, token_exp             # Authentication
nickname: Optional[str]                # User display name
avatar_id: Optional[str]               # User avatar identifier
avatar_path: Optional[str]             # Local path to cached avatar
user_permissions: list[str]            # User permission strings
user_groups: list[str]                 # User group memberships
user_2fa_enabled: bool                 # Whether user has 2FA enabled
pending_2fa_verification: bool         # Whether 2FA verification is pending
conn: Optional[ClientConnection]       # Active WebSocket connection
service_manager: Optional[ServiceManager]  # Background services manager
dek: Optional[bytes]                   # In-memory Data Encryption Key (never persisted)
preferences: dict                      # User preferences from YAML
```

### 2. MVC Pattern with Flet-Model
The application uses the Flet-Model library for routing and view management:
- **Models** (`include/ui/models/`): Route handlers decorated with `@route()`
- **Views** (`include/ui/controls/views/`): UI layout components
- **Controllers** (`include/controllers/`): Business logic handlers extending `Controller`

Example Model:
```python
@route("connect")
class ConnectToServerModel(Model):
    def __init__(self, page: ft.Page, router: Router):
        self.appbar = ft.AppBar(...)
        self.controls = [ConnectForm(), ...]
```

### 3. Generic Controller Pattern
All controllers inherit from `Controller[T]` where T is the control type:
```python
class Controller(Generic[T]):
    control: T                    # The UI control being managed
    app_shared: AppShared        # Singleton config instance
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
- Uses a CA certificate directory (`include/ca/`) for SSL verification
- Configurable SSL enforcement (can disable for testing)
- Supports `force_ipv4` parameter for IPv4-only connections

### Request Handling (`include/util/requests.py`)
- `do_request()`: Execute requests with automatic retry on connection failure; also passes `force_ipv4` preference on reconnect
- `do_request_2()`: Returns typed `Response` objects
- `_request()`: Low-level request execution with connection locking; adds `timestamp` and `nonce` fields to every request
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
- Configures page settings (theme, fonts, window size 1366×768)
- Initializes and registers background services (auto-update, download manager, token refresh, favorites validation) via `ServiceManager`
- Registers keyboard shortcuts (Ctrl+W: semantics debugger, Ctrl+Q: dev dialog)
- Navigates to initial `/connect` route

## Configuration and Preferences

### Constants (`include/constants.py`)
- Version information: `APP_VERSION`, `BUILD_VERSION`, `PROTOCOL_VERSION`
- Release channel: `CHANNEL` (uses `ChannelType` enum: `STABLE`, `ALPHA`, `BETA`)
- Path configuration: `RUNTIME_PATH`, `FLET_APP_STORAGE_TEMP`, `FLET_APP_STORAGE_DATA`
- CA certificates directory path via `ROOT_PATH`
- GitHub repository reference

### User Preferences
- Stored in YAML format at `{FLET_APP_STORAGE_DATA}/preferences.yaml`
- Loaded into `AppShared.preferences` dictionary
- Contains settings like language, proxy configuration, connection settings

## Exception Handling

Custom exception hierarchy:
- `include/classes/exceptions/request.py`: `InvalidResponseError` for bad responses
- `include/classes/exceptions/transmission.py`: `FileHashMismatchError`, `FileSizeMismatchError`
- `include/classes/exceptions/config.py`: `CorruptedEncryptedConfigError` for encrypted config failures

## Best Practices for Development

1. **State Management**: Always use `AppShared()` singleton for shared state
2. **Async Operations**: All I/O must be async; use `await` and `async def`
3. **Error Handling**: Wrap WebSocket operations in try/except for `ConnectionClosed`
4. **Localization**: Import and use `get_translation()` for all user-facing strings
5. **Type Safety**: Use type hints; controllers use Generic[T] pattern
6. **Connection Resilience**: Use `do_request()` which auto-retries on connection loss
7. **UI Updates**: Call `page.update()` or `control.update()` after state changes
8. **Threading**: AppShared uses locks for thread-safety

## Critical Implementation Details

- **Protocol Version**: Current version is 9 (`PROTOCOL_VERSION`)
- **Window Size**: Default 1366x768; non-resizable in production builds, resizable in development
- **Theme**: Dark mode with custom gradient background
- **Font**: Source Han Serif SC (Chinese serif font)
- **Build Tool**: Uses `flet build` for platform-specific packages
- **Package Manager**: Supports both `uv` and `poetry`
- **Background Services**: `ServiceManager` singleton manages auto-update, download, token refresh, and favorites validation services
- **Data Encryption Key (DEK)**: Per-user encryption key derived from login password; stored in `AppShared.dek` in memory only, never persisted

## Known Issues Directory
The `include/ui/issues/` directory contains workarounds for known Flet framework bugs:
- `ani.py`: Animation-related issues
- `daterange.py`: Date range picker issues
- `ph.py`: Permission handler issues

Future agents should check this directory when encountering UI framework bugs.
