---
name: CFMS Configuration & Preferences Manager
description: Expert in application configuration, user preferences, settings management, and state persistence for CFMS Client NEXT.
---

## Configuration System Overview

CFMS Client NEXT uses a dual-layer configuration system:
1. **AppShared**: Singleton managing runtime state and global configuration
2. **User Preferences**: YAML-based persistent settings storage

## AppShared Singleton

**Location**: `include/classes/shared.py`

The `AppShared` class is a thread-safe singleton managing all global application state.

### Implementation Pattern

```python
class AppShared:
    _instance = None
    _instance_lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        # Initialize attributes
        self._initialized = True
```

**Thread Safety**: Uses double-checked locking pattern to ensure only one instance exists, even in multi-threaded environments.

### AppShared Attributes

#### Server Configuration
```python
server_address: Optional[str]          # WebSocket server URL (e.g., "wss://example.com")
_server_address_hash: Optional[str]    # Cached SHA256 hash of server address
server_info: dict[str, Any]            # Server metadata (version, features, etc.)
disable_ssl_enforcement: bool          # SSL validation bypass (dev only)
```

**Server Address Hash**:
```python
@property
def server_address_hash(self) -> Optional[str]:
    """Get hashed server address for cache keys."""
    if self._server_address_hash is not None:
        return self._server_address_hash
    else:
        if not self.server_address:
            raise ValueError("Server address is not set")
        self._server_address_hash = hashlib.sha256(
            self.server_address.encode("utf-8")
        ).hexdigest()
        return self._server_address_hash
```

Used for:
- Unique cache directories per server
- User preference isolation by server

#### Authentication State
```python
username: Optional[str]                # Current logged-in user
token: Optional[str]                   # Authentication token
token_exp: Optional[float]             # Token expiration (Unix timestamp)
nickname: Optional[str]                # Display name
avatar_id: Optional[str]               # User avatar identifier
avatar_path: Optional[str]             # Local path to cached avatar
user_permissions: list[str]            # Permission strings
user_groups: list[str]                 # Group memberships
user_2fa_enabled: bool                 # Whether the user has 2FA enabled
pending_2fa_verification: bool         # Whether 2FA verification is pending
```

#### Services and Connections
```python
conn: Optional[ClientConnection]       # Active WebSocket connection
ph_service: Optional[PermissionHandler] # Mobile permissions service
service_manager: Optional[ServiceManager]  # Background services manager
floating_upgrade_button: Optional[FloatingUpgradeButton]  # Upgrade button reference
```

#### Runtime Flags
```python
is_mobile: bool                        # Whether running on mobile
is_production: bool                    # Whether running from packaged runtime
```

#### User Preferences and Encryption
```python
preferences: dict                      # Loaded from YAML file
user_perference: Optional[UserPreference]  # Typed preference wrapper
dek: Optional[bytes]                   # In-memory Data Encryption Key (never persisted)
```

### Helper Methods

```python
def get_not_none_attribute(self, name: str) -> Any:
    """Get attribute, asserting it is not None."""
    _attr = getattr(self, name)
    assert _attr is not None, f"Attribute '{name}' must not be None"
    return _attr

def dump_preferences(self) -> None:
    """Save current preferences to disk."""
    with open(PREFERENCES_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(self.preferences, f)
```

Usage:
```python
app_shared = AppShared()
conn = app_shared.get_not_none_attribute("conn")  # Raises AssertionError if conn is None

# Save preferences (use this instead of manual YAML writes)
app_shared.dump_preferences()
```

### Usage Pattern

```python
# Always use the singleton
app_shared = AppShared()

# Access shared state
server_url = app_shared.server_address
user_perms = app_shared.user_permissions

# Modify state
app_shared.username = "john_doe"
app_shared.token = "abc123..."

# Check authentication
if app_shared.token and app_shared.username:
    # User is authenticated
    pass
```

## User Preferences (YAML)

**Location**: `{FLET_APP_STORAGE_DATA}/preferences.yaml`

Path constant: `include/classes/shared.py` - `PREFERENCES_PATH`

### Preferences Structure

The default preferences written by `_init_preferences()`:

```yaml
settings:
  language: "zh_CN"               # or "en", etc.
  proxy_settings: null            # null = no proxy, true = system proxy, "http://proxy:port" = custom
  custom_proxy: ""                # Custom proxy URL string
  enable_conn_history_logging: false  # Whether to log connection history
  force_ipv4: false               # Force IPv4 connections only
  update_channel: "stable"        # Update channel: "stable", "beta", "alpha"
```

### Initialization

**Auto-initialization** in `AppShared.__init__()`:
```python
if not os.path.exists(PREFERENCES_PATH):
    self._init_preferences()

with open(PREFERENCES_PATH, "r", encoding="utf-8") as file:
    self.preferences = yaml.safe_load(file)
```

**`_init_preferences()` method**:
```python
def _init_preferences(self) -> None:
    """Initialize preferences file with default values."""
    default_preferences = {
        "settings": {
            "language": "zh_CN",
            "proxy_settings": None,
            "custom_proxy": "",
            "enable_conn_history_logging": False,
            "force_ipv4": False,
            "update_channel": DEFAULT_UPDATE_CHANNEL.value,
        }
    }
    with open(PREFERENCES_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(default_preferences, f)
```

### Accessing Preferences

```python
app_shared = AppShared()

# Get language
language = app_shared.preferences.get("settings", {}).get("language", "zh_CN")

# Get proxy settings
proxy = app_shared.preferences["settings"]["proxy_settings"]

# Get force_ipv4 flag
force_ipv4 = app_shared.preferences["settings"].get("force_ipv4", False)
```

### Modifying Preferences

```python
app_shared = AppShared()

# Modify in memory
app_shared.preferences["settings"]["language"] = "en"

# Persist to file using the built-in method
app_shared.dump_preferences()
```

## Settings UI

### Settings Views

**Location**: `include/ui/models/settings/`

Settings pages organized by category:
- `overview.py`: Settings overview/navigation
- `connection.py`: Connection settings (server URL, proxy, SSL)
- `language.py`: Language/locale settings
- `safety.py`: Security settings
- `twofa.py`: Two-factor authentication settings
- `updates.py`: Update channel settings

Each settings page:
1. Displays current preference values
2. Allows user to modify settings
3. Validates inputs
4. Saves to preferences file
5. Applies changes immediately (if applicable)

### Settings Page Pattern

**Model Example** (`overview.py`):
```python
@route("settings")
class SettingsModel(Model):
    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)
        
        self.appbar = ft.AppBar(title=ft.Text(_("Settings")))
        
        # Settings categories
        self.controls = [
            ft.ListTile(
                title=ft.Text(_("Connection")),
                on_click=lambda e: router.push("/settings/connection")
            ),
            ft.ListTile(
                title=ft.Text(_("Language")),
                on_click=lambda e: router.push("/settings/language")
            ),
            # ... more categories
        ]
```

**Individual Setting Page** (`language.py`):
```python
@route("settings/language")
class LanguageSettingsModel(Model):
    def __init__(self, page: ft.Page, router: Router):
        super().__init__(page, router)
        
        app_shared = AppShared()
        current_lang = app_shared.preferences.get("settings", {}).get("language", "zh_CN")
        
        self.language_dropdown = ft.Dropdown(
            label=_("Language"),
            value=current_lang,
            options=[
                ft.DropdownOption("zh_CN", _("简体中文")),
                ft.DropdownOption("en", _("English")),
            ],
            on_change=self.language_changed
        )
        
        self.controls = [self.language_dropdown]
    
    async def language_changed(self, e):
        app_shared = AppShared()
        new_language = self.language_dropdown.value
        
        # Update in memory
        app_shared.preferences["settings"]["language"] = new_language
        
        # Save to file
        await save_preferences()
        
        # Apply immediately (requires restart in most cases)
        show_info(_("Language changed. Please restart the application."))
```

### Connection Settings

**Key Settings**:
- Server address
- SSL verification enable/disable
- Proxy configuration
- Auto-connect on startup

**UI Example**:
```python
class ConnectionSettingsModel(Model):
    def __init__(self, page, router):
        app_shared = AppShared()
        
        self.server_field = ft.TextField(
            label=_("Server Address"),
            value=app_shared.preferences["settings"]["connection"]["default_server"],
            hint_text="wss://server.example.com"
        )
        
        self.ssl_switch = ft.Switch(
            label=_("Verify SSL Certificates"),
            value=app_shared.preferences["settings"]["safety"]["verify_ssl"],
            on_change=self.ssl_changed
        )
        
        self.proxy_field = ft.TextField(
            label=_("Proxy Server"),
            value=app_shared.preferences["settings"]["proxy_settings"] or "",
            hint_text="http://proxy:8080 or leave blank"
        )
        
        self.save_button = ft.Button(
            _("Save"),
            on_click=self.save_settings
        )
    
    async def save_settings(self, e):
        app_shared = AppShared()
        
        # Validate server address
        server = self.server_field.value
        if not server.startswith("wss://") and not server.startswith("ws://"):
            show_error(_("Server address must start with wss:// or ws://"))
            return
        
        # Update preferences
        app_shared.preferences["settings"]["connection"]["default_server"] = server
        app_shared.preferences["settings"]["proxy_settings"] = self.proxy_field.value or None
        
        # Save
        await save_preferences()
        
        show_success(_("Settings saved"))
```

## Application Constants

**Location**: `include/constants.py`

### Path Configuration

```python
CONSTANT_FILE_ABSPATH = os.path.abspath(__file__)
ROOT_PATH = Path(CONSTANT_FILE_ABSPATH).resolve().parent.parent
LOCALE_PATH = f"{ROOT_PATH}/include/ui/locale"

# Environment-based paths
RUNTIME_PATH = os.environ.get("PYTHONHOME", "")
FLET_APP_STORAGE_TEMP = os.environ.get("FLET_APP_STORAGE_TEMP", ".")
FLET_APP_STORAGE_DATA = os.environ.get("FLET_APP_STORAGE_DATA", ".")

# User data paths
USER_PREFERENCES_PATH = f"{FLET_APP_STORAGE_DATA}/user_preferences"
```

**Platform-Specific Paths**:
- **Desktop**: `FLET_APP_STORAGE_DATA` typically points to user's app data directory
- **Mobile**: Points to app's private storage directory
- **Web**: Limited storage (consider localStorage)

### Version Information

```python
from include.classes.version import ChannelType

CHANNEL = ChannelType.STABLE  # ChannelType.STABLE, .BETA, or .ALPHA
BUILD_VERSION = "v0.6.1"
MODIFIED = "20260221"  # YYYYMMDD format

if CHANNEL == ChannelType.STABLE:
    APP_VERSION = f"{BUILD_VERSION[1:]}.{MODIFIED} NEXT"
else:
    APP_VERSION = f"{BUILD_VERSION[1:]}.{MODIFIED}_{CHANNEL.value} NEXT"
```

### Protocol Version

```python
PROTOCOL_VERSION = 9
```

Used for:
- Server compatibility checks
- Protocol negotiation
- Migration handling

### Application Metadata

```python
DEFAULT_WINDOW_TITLE = "CFMS Client"
GITHUB_REPO = "Creeper19472/cfms_client_next"
```

### CA Certificate Directory

SSL certificates for server validation are stored in the `include/ca/` directory
relative to `ROOT_PATH`. The directory path is used via `capath` in the SSL context:

```python
ssl_context.load_verify_locations(capath=f"{ROOT_PATH}/include/ca/")
```

## State Persistence Strategies

### Session-Only Data (AppShared)

**Characteristics**:
- Stored in memory only
- Cleared on application exit
- Not persisted to disk

**Examples**:
- Authentication tokens
- Active WebSocket connection
- Current user permissions

**Why?**: Security - tokens shouldn't be saved to disk

### Persistent Data (Preferences YAML)

**Characteristics**:
- Stored on disk
- Survives application restart
- User-editable (if careful)

**Examples**:
- Language preference
- Server address
- UI preferences
- Connection settings

**Why?**: User convenience - settings persist across sessions

### Server-Side State

**Characteristics**:
- Stored on server
- Synchronized across devices
- Retrieved after login

**Examples**:
- User profile
- File metadata
- Access permissions
- Audit logs

**Retrieval**:
```python
# After login
response = await do_request_2(action="get_user_profile")
app_shared.user_data = response.data
```

## Configuration Best Practices

### 1. Default Values

Always provide defaults:
```python
language = app_shared.preferences.get("settings", {}).get("language", "zh_CN")
```

### 2. Validation

Validate settings before applying:
```python
def validate_proxy(proxy: str) -> bool:
    if not proxy:
        return True  # Empty is valid (no proxy)
    
    # Validate URL format
    import urllib.parse
    try:
        result = urllib.parse.urlparse(proxy)
        return result.scheme in ["http", "https", "socks5"]
    except:
        return False
```

### 3. Migration

Handle preference schema changes:
```python
def migrate_preferences(prefs: dict) -> dict:
    """Migrate old preference format to new."""
    version = prefs.get("version", 1)
    
    if version < 2:
        # Migrate v1 -> v2
        if "old_setting" in prefs:
            prefs["new_setting"] = prefs.pop("old_setting")
        prefs["version"] = 2
    
    return prefs
```

### 4. Type Safety

Use typed wrappers for complex preferences:
```python
from dataclasses import dataclass

@dataclass
class ConnectionSettings:
    default_server: str
    remember_server: bool
    auto_connect: bool
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            default_server=data.get("default_server", ""),
            remember_server=data.get("remember_server", True),
            auto_connect=data.get("auto_connect", False),
        )
    
    def to_dict(self) -> dict:
        return {
            "default_server": self.default_server,
            "remember_server": self.remember_server,
            "auto_connect": self.auto_connect,
        }
```

### 5. Atomic Writes

Ensure file writes are atomic:
```python
import tempfile
import shutil

async def save_preferences_atomic():
    """Save preferences with atomic write."""
    app_shared = AppShared()
    
    # Write to temp file first
    temp_fd, temp_path = tempfile.mkstemp(suffix='.yaml')
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            yaml.dump(app_shared.preferences, f, default_flow_style=False)
        
        # Atomic rename
        shutil.move(temp_path, PREFERENCES_PATH)
    except:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
```

## Debugging Configuration

### Logging Preferences

```python
import logging

logger = logging.getLogger(__name__)

app_shared = AppShared()
logger.info(f"Server: {app_shared.server_address}")
logger.info(f"Language: {app_shared.preferences.get('settings', {}).get('language')}")
# Don't log sensitive data like tokens!
```

### Configuration Dump

For debugging, create a sanitized config dump:
```python
def dump_config():
    """Dump configuration for debugging (sanitized)."""
    app_shared = AppShared()
    
    config_info = {
        "server_address": app_shared.server_address,
        "username": app_shared.username,
        "has_token": bool(app_shared.token),
        "permissions": app_shared.user_permissions,
        "preferences": {
            "language": app_shared.preferences.get("settings", {}).get("language"),
            "has_proxy": bool(app_shared.preferences.get("settings", {}).get("proxy_settings")),
            # ... other non-sensitive settings
        }
    }
    
    return config_info
```

## Testing Configuration

### Unit Tests

```python
import unittest
from include.classes.config import AppShared

class TestAppShared(unittest.TestCase):
    def test_singleton(self):
        config1 = AppShared()
        config2 = AppShared()
        self.assertIs(config1, config2)
    
    def test_server_hash(self):
        config = AppShared()
        config.server_address = "wss://test.com"
        hash1 = config.server_address_hash
        hash2 = config.server_address_hash
        self.assertEqual(hash1, hash2)  # Cached
```

### Manual Testing

- [ ] Default preferences created on first run
- [ ] Settings persist across restarts
- [ ] Invalid preferences handled gracefully
- [ ] Language changes apply correctly
- [ ] Connection settings save and load
- [ ] AppShared singleton works in multi-threaded context
