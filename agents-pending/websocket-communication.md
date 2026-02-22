---
name: CFMS WebSocket Communication & Request Handler
description: Expert in WebSocket-based client-server communication for CFMS Client NEXT, covering connection management, request/response handling, error recovery, and protocol implementation.
---

## WebSocket Communication Overview

CFMS Client NEXT communicates with the CFMS server exclusively through **WebSocket** connections. The protocol is JSON-based with a structured request/response pattern, supporting authentication, file transfers, and various document management operations.

### Protocol Version
Current protocol version: **9** (defined in `include/constants.py`)

## Connection Architecture

### Connection Establishment

**Location**: `include/util/connect.py`

```python
async def get_connection(
    server_address: str,
    disable_ssl_enforcement: bool = False,
    max_size: int = 2**20,  # 1MB default message size
    proxy: str | Literal[True] | None = True,
    force_ipv4: bool = False,
) -> ClientConnection
```

**Features**:
- SSL/TLS support with CA certificate directory
- Optional SSL verification bypass for development
- Proxy support (system proxy, custom proxy, or none)
- Configurable maximum message size
- IPv4-only mode via `force_ipv4` parameter

**SSL Configuration**:
```python
ssl_context = ssl.create_default_context()

if not disable_ssl_enforcement:
    # Production: Use CA certificate directory
    ssl_context.load_verify_locations(capath=f"{ROOT_PATH}/include/ca/")
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
else:
    # Development: Disable SSL verification (NOT RECOMMENDED)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
```

**CA Certificate Directory**:
- Located at `include/ca/` relative to `ROOT_PATH`
- Contains root and intermediate CA certificates as PEM files
- Used for validating CFMS server certificates

### Connection State Management

**Global Connection Storage**:
- Stored in `AppShared.conn` (singleton)
- Type: `Optional[ClientConnection]` from `websockets.asyncio.client`
- Accessed via `AppShared().conn`

**Connection Lock Pattern**:
```python
# Per-connection locks stored in WeakKeyDictionary
_conn_locks = weakref.WeakKeyDictionary()

# Usage in _request()
lock = _conn_locks.setdefault(conn, asyncio.Lock())
async with lock:
    # Send and receive operations
```

This prevents concurrent requests on the same connection, which would cause response mismatches.

## Request/Response Protocol

### Request Format

**Location**: `include/util/requests.py`

Standard request structure:
```json
{
    "action": "action_name",
    "data": {
        "key1": "value1",
        "key2": "value2"
    },
    "username": "user123",
    "token": "auth_token_here",
    "timestamp": 1234567890.123,
    "nonce": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Key Fields**:
- `action` (required): Command/operation name
- `data` (optional): Operation-specific payload
- `username` (optional): User identifier (from AppShared if not provided)
- `token` (optional): Authentication token (from AppShared if not provided)
- `timestamp`: Unix timestamp added automatically by `_request()`
- `nonce`: UUID4 string added automatically by `_request()` to prevent replay attacks

### Response Format

**Response Data Class** (`include/classes/response.py`):
```python
@dataclass
class Response:
    code: int               # HTTP-like status code
    message: str            # Human-readable message
    data: dict[str, Any]    # Response payload
    timestamp: float        # Unix timestamp
```

**Status Codes**:
- `200`: Success
- `400`: Bad request
- `401`: Unauthorized
- `403`: Forbidden/Permission denied
- `404`: Not found
- `500`: Server error

## Request Execution Functions

### High-Level API: `do_request()` and `do_request_2()`

**`do_request()`** - Returns raw dictionary:
```python
async def do_request(
    action: str,
    data: dict[str, Any] = {},
    message: str = "",
    username: Optional[str] = None,
    token: Optional[str] = None,
    max_retries: int = 3,
) -> dict[str, Any]
```

**`do_request_2()`** - Returns typed Response object:
```python
async def do_request_2(
    action: str,
    data: dict[str, Any] = {},
    message: str = "",
    username: Optional[str] = None,
    token: Optional[str] = None,
    max_retries: int = 3,
) -> Response
```

**Automatic Retry on Connection Loss**:
Both functions automatically handle connection failures:
1. Catch `ConnectionClosed`, `ConnectionAbortedError`, `ConnectionResetError`
2. Reconnect using `get_connection()` with saved server settings
3. Update `AppShared.conn` with new connection
4. Retry the request
5. Fail after `max_retries` attempts

Example usage:
```python
response = await do_request_2(
    action="list_directory",
    data={"directory_id": dir_id}
)

if response.code == 200:
    files = response.data.get("files", [])
    # Process files
elif response.code == 403:
    # Permission denied
    show_error("No permission to list files")
```

### Low-Level API: `_request()`

**Internal function** - Not for direct use:
```python
async def _request(
    conn: ClientConnection,
    action: str,
    data: dict[str, Any] = {},
    message: str = "",
    username: Optional[str] = None,
    token: Optional[str] = None,
) -> dict[str, Any]
```

**Process**:
1. Acquire connection lock
2. Build request JSON
3. Send via `conn.send(json.dumps(...))`
4. Receive response via `conn.recv()`
5. Parse JSON and return

**Thread Safety**:
Uses per-connection locks to ensure only one request is in-flight per connection at a time.

## Common Request Patterns

### Authentication

**Login Request**:
```python
response = await do_request_2(
    action="login",
    data={
        "username": username,
        "password": password_hash,  # Typically hashed
    }
)

if response.code == 200:
    token = response.data["token"]
    token_exp = response.data["exp"]
    # Store in AppShared
    app_shared.username = username
    app_shared.token = token
    app_shared.token_exp = token_exp
```

### File Operations

**List Files**:
```python
response = await do_request_2(
    action="list_directory",
    data={"directory_id": dir_id}
)

files = response.data.get("files", [])
directories = response.data.get("directories", [])
```

**Create Directory**:
```python
response = await do_request_2(
    action="create_directory",
    data={
        "parent_id": parent_id,
        "name": directory_name,
    }
)
```

**Delete File**:
```python
response = await do_request_2(
    action="delete_file",
    data={"file_id": file_id}
)
```

### User Management

**Get User Info**:
```python
response = await do_request_2(
    action="get_user_info",
    data={"username": username}
)

user_data = response.data.get("user", {})
```

**Change Password**:
```python
response = await do_request_2(
    action="change_password",
    data={
        "old_password": old_pass_hash,
        "new_password": new_pass_hash,
    }
)
```

## File Transfer Protocol

### Upload Protocol

**Location**: `include/util/transfer.py`

**Process**:
1. Initiate upload task (via standard request)
2. Switch to binary transfer protocol
3. Send file metadata (SHA256, size)
4. Receive "ready" or "stop" from server
5. Stream file in chunks with progress reporting

**Upload Function**:
```python
async def upload_file_to_server(
    client: ClientConnection,
    task_id: str,
    file_path: str
) -> AsyncIterator[tuple[int, int]]:  # Yields (bytes_sent, total_bytes)
```

**Protocol Flow**:
```
Client → Server: {"action": "upload_file", "data": {"task_id": "..."}}
Server → Client: {"action": "transfer_file"}
Client → Server: {"action": "transfer_file", "data": {"sha256": "...", "file_size": 12345}}
Server → Client: "ready" or "stop"
Client → Server: [binary chunks with size prefix]
Server → Client: "success" or error
```

**Chunking**:
- Files sent in 8192-byte chunks
- Each chunk prefixed with 4-byte size (big-endian)
- Progress yielded after each chunk

### Download Protocol

**Download Function**:
```python
async def download_file_from_server(
    client: ClientConnection,
    task_id: str,
    save_path: str,
    progress_callback: Optional[Callable] = None
)
```

**AES Encryption Support**:
- Server may send encrypted files (AES-256-CBC)
- Encryption key and IV sent in initial metadata
- Client decrypts chunks on-the-fly

**Protocol Flow**:
```
Client → Server: {"action": "download_file", "data": {"task_id": "..."}}
Server → Client: {"action": "transfer_file", "data": {"encrypted": true/false, "key": "...", "iv": "...", "file_size": 12345}}
Client → Server: "ready"
Server → Client: [binary chunks with size prefix]
Client → Server: "success" or error
Server → Client: Hash verification response
```

### Batch Upload

**Batch Upload Generator**:
```python
async def batch_upload_file_to_server(
    app_shared: AppShared,
    directory_id: str,
    files: list[FilePickerFile]
) -> AsyncIterator[tuple[int, str, int, int, Optional[Exception]]]:
    # Yields: (index, filename, current_size, file_size, exception)
```

**Features**:
- Uploads multiple files sequentially
- Creates server upload tasks automatically
- Yields progress for each file
- Yields exceptions without stopping iteration (allows error recovery)

## Error Handling

### Exception Types

**Request Exceptions** (`include/classes/exceptions/request.py`):
```python
class InvalidResponseError(Exception):
    """Raised when server response is invalid or error code received"""
    def __init__(self, response: Response):
        self.response = response
```

**Transmission Exceptions** (`include/classes/exceptions/transmission.py`):
```python
class FileHashMismatchError(Exception):
    """SHA256 hash mismatch after transfer"""

class FileSizeMismatchError(Exception):
    """File size mismatch after transfer"""
```

### Connection Loss Handling

**Automatic Reconnection**:
```python
for attempt in range(max_retries):
    try:
        response = await _request(conn, action, data, message, username, token)
    except (ConnectionClosed, ConnectionAbortedError, ConnectionResetError):
        if attempt >= max_retries - 1:
            raise
        # Reconnect
        conn = await get_connection(
            server_address=app_shared.get_not_none_attribute("server_address"),
            disable_ssl_enforcement=app_shared.disable_ssl_enforcement,
            proxy=app_shared.preferences["settings"]["proxy_settings"],
            force_ipv4=app_shared.preferences["settings"].get("force_ipv4", False),
        )
        app_shared.conn = conn
        continue
    break
```

**Best Practice**:
Always use `do_request()` or `do_request_2()` which include retry logic, rather than calling `_request()` directly.

## Proxy Support

**Proxy Configuration**:
- Stored in `AppShared.preferences["settings"]["proxy_settings"]`
- Types: `True` (system proxy), `"http://proxy:port"` (custom), `None` (no proxy)
- Custom proxy string stored separately in `"custom_proxy"` preference key

**Usage**:
```python
conn = await get_connection(
    server_address="wss://server.example.com",
    proxy=app_shared.preferences["settings"]["proxy_settings"],
    force_ipv4=app_shared.preferences["settings"].get("force_ipv4", False),
)
```

## Best Practices

1. **Always Use High-Level Functions**: Prefer `do_request_2()` over `_request()`
2. **Handle Response Codes**: Check `response.code` before accessing `response.data`
3. **Use AppShared for Auth**: Let functions pull `username` and `token` from AppShared
4. **Verify File Hashes**: Always calculate and verify SHA256 for uploads/downloads
5. **Progress Feedback**: Use async generators to report upload/download progress to UI
6. **Error Recovery**: Catch `InvalidResponseError` and handle specific codes (403, 404, etc.)
7. **Connection Reuse**: Don't create new connections; use `AppShared.conn`
8. **Async Operations**: All WebSocket operations must be `async`/`await`
9. **Lock Awareness**: Don't manually send/recv on `AppShared.conn`; use request functions
10. **Timeout Handling**: Consider implementing timeouts for long-running operations

## Security Considerations

### SSL/TLS
- **Always** use SSL in production (`disable_ssl_enforcement=False`)
- Integrated CA certificates prevent MITM attacks
- Only disable SSL for local development/testing

### Authentication Tokens
- Tokens stored in `AppShared.token`
- Token expiration in `AppShared.token_exp` (Unix timestamp)
- Check expiration before long-running operations
- Re-authenticate if token expired

### Password Handling
- Never send plaintext passwords
- Hash passwords? No — passwords are sent as plaintext over the encrypted WebSocket channel; the server handles hashing

### File Encryption
- Server may encrypt files with AES-256-CBC
- Encryption keys transmitted securely over SSL WebSocket
- Keys used only for single transfer session

## Debugging

### Developer Tools
- **Ctrl+W**: Toggle semantics debugger
- **Ctrl+Q**: Open `DevRequestDialog` for manual request testing
- Allows sending arbitrary JSON requests
- Useful for testing new protocol commands

### Logging
Consider adding logging for:
- Connection establishment/failure
- Request/response JSON (sanitize sensitive data)
- File transfer progress
- Reconnection attempts

### Common Issues
1. **Response Mismatch**: Multiple concurrent requests without locking
2. **Connection Closed**: Network interruption or server restart
3. **Hash Mismatch**: File corrupted during transfer or read
4. **Permission Denied (403)**: User lacks required permission
5. **Token Expired (401)**: Need to re-authenticate

## Protocol Extensions

When adding new actions:
1. Define action name (e.g., `"new_action"`)
2. Document expected `data` structure
3. Document response `data` structure
4. Update protocol version if breaking changes
5. Add helper function in appropriate utility module
6. Handle new response codes if introduced

Example:
```python
async def do_new_action(param1: str, param2: int) -> CustomResult:
    """Perform new action with parameters."""
    response = await do_request_2(
        action="new_action",
        data={
            "param1": param1,
            "param2": param2,
        }
    )
    
    if response.code != 200:
        raise InvalidResponseError(response)
    
    return CustomResult(response.data)
```
