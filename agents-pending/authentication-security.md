---
name: CFMS Authentication & Security Specialist
description: Expert in authentication, authorization, security practices, and SSL/TLS implementation for CFMS Client NEXT, covering login, token management, permissions, and encrypted communications.
---

## Security Overview

CFMS Client NEXT implements a comprehensive security model including:
- WebSocket communication over SSL/TLS
- Token-based authentication with optional two-factor authentication (TOTP)
- Role-based access control (RBAC)
- AES file encryption for transfers
- SHA256 hash verification
- CA certificate validation via a bundled CA directory
- Per-user Data Encryption Key (DEK) for config encryption

## Authentication System

### Login Flow

**Login View**: `include/ui/controls/views/login.py`
**Login Model**: `include/ui/models/login.py`
**Login Controller**: `include/controllers/login.py`

**Authentication Steps**:

1. **User Input Collection**:
   ```python
   username = login_form.username_field.value
   password = login_form.password_field.value
   ```

2. **Password Processing**:
   - Passwords are sent to the server as-is over the encrypted WebSocket connection
   - The server handles hashing and salting server-side

3. **Login Request**:
   ```python
   response = await do_request(
       "login",
       {
           "username": username,
           "password": password,  # sent as plaintext over the encrypted channel
       },
   )
   ```

4. **Response Handling**:
   ```python
   if (code := response["code"]) == 200:
       # Regular login without 2FA
       await _complete_login(username, response["data"], password)

   elif code == 202:
       # 2FA verification required
       # Show TwoFactorVerifyDialog and await user code entry
       ...

   elif code == 403:
       # Password must be changed before login
       page.show_dialog(PasswdUserDialog(username, tip=_("Password must be changed before login.")))

   else:
       show_error(_("Login failed: ({code}) {message}").format(
           code=code, message=response["message"]
       ))
   ```

   After successful authentication (`code == 200`), the `_complete_login` helper stores data in `AppShared`:
   ```python
   app_shared.username = username
   app_shared.nickname = data.get("nickname")
   app_shared.token = data["token"]
   app_shared.token_exp = data.get("exp")
   app_shared.user_permissions = data["permissions"]
   app_shared.user_groups = data["groups"]
   app_shared.user_2fa_enabled = data.get("has_2fa", False)
   app_shared.pending_2fa_verification = False
   ```

### Token Management

**Token Storage**:
- Stored in `AppShared.token` (singleton, in-memory only)
- Not persisted to disk for security
- Cleared on logout or application close

**Token Properties**:
```python
app_shared.token: Optional[str]         # JWT or opaque token
app_shared.token_exp: Optional[float]   # Unix timestamp expiration
```

**Token Usage**:
All authenticated requests automatically include the token:
```python
# Automatic token injection in do_request()
response = await do_request_2(
    action="some_action",
    data={...}
    # username and token pulled from AppShared automatically
)
```

**Token Expiration Handling**:
```python
import time

def is_token_expired() -> bool:
    app_shared = AppShared()
    if not app_shared.token_exp:
        return True
    return time.time() >= app_shared.token_exp

# Before long operations
if is_token_expired():
    # Redirect to login
    await page.push_route("/login")
    return
```

**Token Refresh** (if supported by server):
```python
response = await do_request_2(
    action="refresh_token",
    data={}
)

if response.code == 200:
    app_shared.token = response.data["token"]
    app_shared.token_exp = response.data["exp"]
```

### Logout

**Process**:
1. Optionally notify server (if server tracks sessions)
2. Clear authentication data from AppShared
3. Close WebSocket connection
4. Navigate to login/connect screen

```python
async def logout():
    app_shared = AppShared()
    
    # Optional: notify server
    try:
        await do_request_2(action="logout", data={})
    except:
        pass  # Ignore errors
    
    # Clear auth data
    app_shared.username = None
    app_shared.token = None
    app_shared.token_exp = None
    app_shared.nickname = None
    app_shared.user_permissions = []
    app_shared.user_groups = []
    
    # Close connection
    if app_shared.conn:
        await app_shared.conn.close()
        app_shared.conn = None
    
    # Navigate to login
    await page.push_route("/login")
```

## Authorization (Permissions)

### Permission Model

**Permission Storage**:
```python
app_shared.user_permissions: list[str]  # e.g., ["file_upload", "file_delete"]
app_shared.user_groups: list[str]       # e.g., ["admins", "editors"]
```

**Common Permissions**:
- `file_upload`: Upload files
- `file_download`: Download files
- `file_delete`: Delete files
- `file_share`: Share files with others
- `directory_create`: Create directories
- `directory_delete`: Delete directories
- `user_manage`: Manage users (admin)
- `group_manage`: Manage groups (admin)
- `system_config`: Configure system settings (admin)
- `bypass_lockdown`: Access system during lockdown

### Permission Checking

**UI Permission Checks**:
```python
def can_upload_files() -> bool:
    app_shared = AppShared()
    return "file_upload" in app_shared.user_permissions

# In UI code
if can_upload_files():
    upload_button.visible = True
else:
    upload_button.visible = False
```

**Operation Permission Checks**:
```python
async def perform_upload(file_path: str):
    if not can_upload_files():
        send_error(page, _("Permission denied: Cannot upload files"))
        return
    
    # Proceed with upload
    ...
```

**Server-Side Enforcement**:
Even with client-side checks, the server enforces permissions. Handle 403 responses:
```python
response = await do_request_2(action="upload_file", data={...})

if response.code == 403:
    send_error(page, _("Permission denied"))
    # Optionally refresh permissions
    await refresh_user_permissions()
```

### Group-Based Permissions

Groups can provide permissions:
```python
def is_admin() -> bool:
    app_shared = AppShared()
    return "admins" in app_shared.user_groups

def has_permission(permission: str) -> bool:
    app_shared = AppShared()
    # Direct permission check
    if permission in app_shared.user_permissions:
        return True
    # Group-based permission (if server provides)
    # This depends on server implementation
    return False
```

## SSL/TLS Security

### Certificate Validation

**CA Certificate Directory**:
Location: `include/ca/` directory (relative to `ROOT_PATH`)

Contains PEM-encoded certificates:
1. CFMS Validation Root CA (self-signed root)
2. CFMS Intermediate CA (signed by root)

**Purpose**:
- Validate CFMS server certificates
- Prevent man-in-the-middle attacks
- Trust only CFMS-issued certificates

**SSL Context Setup** (`include/util/connect.py`):
```python
ssl_context = ssl.create_default_context()

if not disable_ssl_enforcement:
    # Production mode: Strict validation
    ssl_context.load_verify_locations(capath=f"{ROOT_PATH}/include/ca/")
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
else:
    # Development mode: No validation (INSECURE)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
```

**Best Practices**:
- **NEVER** disable SSL enforcement in production
- Only use `disable_ssl_enforcement=True` for local development
- Regularly update CA certificates when renewed
- Use `wss://` protocol, never `ws://` in production

### Connection Security

**WebSocket URL Format**:
```
wss://server.example.com:8443/ws
```

**Security Features**:
- TLS 1.2+ encryption
- Certificate pinning via integrated CA
- Hostname verification
- No downgrade to unencrypted WebSocket

**Proxy Support** (maintains security):
```python
# System proxy (respects system SSL settings)
proxy=True

# Custom proxy (SSL tunnel through proxy)
proxy="http://proxy.example.com:8080"

# Direct connection
proxy=None
```

## File Transfer Security

### SHA256 Hash Verification

**Purpose**: Ensure file integrity during transfer

**Upload Hash Calculation** (`include/util/transfer.py`):
```python
async def calculate_sha256(file_path: str) -> str:
    with open(file_path, "rb") as f:
        mmapped_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        return hashlib.sha256(mmapped_file).hexdigest()

# Usage
sha256 = await calculate_sha256(file_path)
# Send to server for verification
```

**Download Hash Verification**:
```python
# After download
calculated_hash = await calculate_sha256(downloaded_file)
expected_hash = response.data["sha256"]

if calculated_hash != expected_hash:
    raise FileHashMismatchError(
        f"Hash mismatch: expected {expected_hash}, got {calculated_hash}"
    )
```

### AES File Encryption

**Download Encryption** (server-side encrypted files):

**Metadata**:
```python
# Server sends encryption info
encryption_data = {
    "encrypted": True,
    "key": base64_encoded_key,      # 32 bytes for AES-256
    "iv": base64_encoded_iv,        # 16 bytes IV
}
```

**Decryption Process**:
```python
from Crypto.Cipher import AES
import base64

# Decode key and IV
key = base64.b64decode(encryption_data["key"])
iv = base64.b64decode(encryption_data["iv"])

# Create cipher
cipher = AES.new(key, AES.MODE_CBC, iv)

# Decrypt chunks
decrypted_chunk = cipher.decrypt(encrypted_chunk)

# Remove padding from final chunk
from Crypto.Util.Padding import unpad
final_chunk = unpad(decrypted_chunk, AES.block_size)
```

**Key Management**:
- Encryption keys generated per-transfer (session keys)
- Keys transmitted over SSL WebSocket (secure channel)
- Keys never persisted to disk
- Keys destroyed after transfer completion

## Password Management

### Password Change

**UI**: Password change dialog (`include/ui/controls/dialogs/admin/accounts.py` - `PasswdUserDialog`)
**Controller**: `include/controllers/dialogs/passwd.py`

**Process**:
1. User enters old password
2. User enters new password (twice for confirmation)
3. Client validates: new password meets requirements
4. Send change request with plaintext passwords over the encrypted channel
5. Server validates old password and updates with hashing/salting

```python
async def change_password(old_pass: str, new_pass: str) -> bool:
    # Client-side validation
    if len(new_pass) < 8:
        show_error(_("Password must be at least 8 characters"))
        return False
    
    # Request (passwords sent as plaintext over encrypted connection)
    response = await do_request_2(
        action="change_password",
        data={
            "old_password": old_pass,
            "new_password": new_pass,
        }
    )
    
    if response.code == 200:
        show_success(_("Password changed successfully"))
        return True
    elif response.code == 401:
        show_error(_("Old password is incorrect"))
        return False
    else:
        show_error(_("Failed to change password"))
        return False
```

### Password Requirements

**Client-Side Validation**:
- Minimum length (typically 8+ characters)
- Optional: complexity requirements (uppercase, lowercase, numbers, symbols)
- Not same as username
- Not same as old password

**Server-Side Enforcement**:
- Server performs same validation
- Server may have additional rules
- Server handles hashing with salt

## Security Best Practices

### General Security

1. **Never Store Plaintext Passwords**: Passwords are transmitted over the encrypted WebSocket channel and never stored on disk; the server handles hashing and salting
2. **Use HTTPS/WSS Only**: No unencrypted connections in production
3. **Validate All Inputs**: Both client and server side
4. **Handle Errors Securely**: Don't leak sensitive info in error messages
5. **Minimize Token Lifetime**: Use short-lived tokens, implement refresh
6. **Clear Sensitive Data**: Zero out passwords, tokens on logout
7. **Log Security Events**: Track login failures, permission denials
8. **Rate Limiting**: Implement or respect server rate limits

### Code Security

1. **Dependency Security**: Keep dependencies updated
   ```bash
   # Check for vulnerabilities
   pip-audit
   ```

2. **Avoid Injection**: Use parameterized queries/prepared statements
3. **Sanitize Outputs**: Escape user data in UI
4. **Secure Random**: Use `secrets` module for tokens/keys
   ```python
   import secrets
   token = secrets.token_urlsafe(32)
   ```

5. **Timing Attacks**: Use constant-time comparison for sensitive data
   ```python
   import hmac
   hmac.compare_digest(expected_hash, actual_hash)
   ```

### Data Protection

1. **In-Memory Only**: Don't persist tokens/passwords to disk
2. **Secure Deletion**: Overwrite sensitive data before deletion
3. **File Permissions**: Ensure config files have restrictive permissions
4. **Encrypted Storage**: If storing sensitive data, encrypt it

### Network Security

1. **Certificate Pinning**: Use integrated CA certificates
2. **Proxy Security**: Verify proxy connections maintain SSL
3. **Timeout Settings**: Implement reasonable timeouts
4. **Connection Validation**: Verify server identity before sending credentials

## Threat Model

### Threats Mitigated

- **Man-in-the-Middle (MITM)**: SSL/TLS with certificate validation
- **Credential Theft**: Token-based auth, no password storage
- **Replay Attacks**: Time-limited tokens
- **File Tampering**: SHA256 hash verification
- **Unauthorized Access**: Permission-based access control
- **Eavesdropping**: Encrypted WebSocket communication

### Threats to Consider

- **Client Compromise**: If client device is compromised, in-memory tokens exposed
- **Server Compromise**: Trust relationship assumes server is secure
- **Social Engineering**: User education required
- **Brute Force**: Server should implement rate limiting
- **Token Theft**: If token stolen, valid until expiration

## Security Testing

### Manual Security Checks

- [ ] SSL certificate validation works
- [ ] Connections fail with invalid certificates
- [ ] SSL enforcement cannot be disabled in production builds
- [ ] Tokens expire and require re-authentication
- [ ] Permission checks prevent unauthorized operations
- [ ] 403 responses handled gracefully
- [ ] Passwords never appear in logs or error messages
- [ ] Hash verification catches corrupted files
- [ ] Encrypted downloads decrypt correctly
- [ ] Logout clears all sensitive data

### Automated Security

Consider integrating:
- Static analysis (Bandit for Python)
- Dependency scanning (pip-audit, Safety)
- Secret detection (detect-secrets)
- Code review for security issues

## Compliance Considerations

### Data Handling

- **User Consent**: Ensure users consent to data storage/transmission
- **Data Minimization**: Only collect necessary data
- **Right to Delete**: Implement user data deletion
- **Audit Logs**: Log security-relevant events

### Encryption Standards

- **AES-256**: Industry standard for file encryption
- **SHA-256**: Secure hash for file verification
- **TLS 1.2+**: Modern SSL/TLS versions

## Incident Response

### Security Event Handling

**Suspicious Activity Detection**:
```python
# Track login failures
login_failures = 0

async def handle_login_failure():
    global login_failures
    login_failures += 1
    
    if login_failures >= 3:
        # Lock out or add delay
        await asyncio.sleep(2 ** login_failures)  # Exponential backoff
```

**Token Compromise**:
1. User reports suspicious activity
2. Invalidate current token (logout)
3. Force password change
4. Review audit logs

**Certificate Issues**:
1. Update integrated CA certificates
2. Deploy update to all clients
3. Revoke compromised certificates

## Two-Factor Authentication (2FA)

CFMS Client NEXT supports TOTP-based two-factor authentication.

**Key Attributes in AppShared**:
```python
user_2fa_enabled: bool           # Whether the user has 2FA enabled
pending_2fa_verification: bool   # Whether 2FA verification is pending for current login
```

**Login with 2FA**:
- When the server returns `code == 202`, 2FA verification is required
- The server response `data["method"]` indicates the method (currently `"totp"`)
- `TwoFactorVerifyDialog` is shown to collect the TOTP code or recovery code
- The 2FA code is submitted with another login request including `"2fa_token"` in the data

**Setup/Management UI**:
- `include/ui/models/settings/twofa.py`: 2FA settings model
- `include/ui/controls/dialogs/twofa_setup.py`: Setup dialog
- `include/ui/controls/dialogs/twofa_verify.py`: Verification dialog
- `include/ui/controls/dialogs/backup_codes.py`: Backup codes dialog
- `include/util/twofa.py`: 2FA utility functions
- `include/classes/twofa.py`: 2FA data classes

## Future Security Enhancements

Potential improvements:
- Biometric authentication (mobile)
- Hardware security key support (FIDO2)
- End-to-end encryption for files
- Certificate revocation checking (OCSP)
- Security headers for web deployments
