---
name: CFMS Authentication & Security Specialist
description: Expert in authentication, authorization, security practices, and SSL/TLS implementation for CFMS Client NEXT, covering login, token management, permissions, and encrypted communications.
---

## Security Overview

CFMS Client NEXT implements a comprehensive security model including:
- WebSocket communication over SSL/TLS
- Token-based authentication
- Role-based access control (RBAC)
- AES file encryption for transfers
- SHA256 hash verification
- Integrated CA certificate validation

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
   - Never send plaintext passwords
   - Hash password client-side (typically SHA256 or similar)
   - Server performs additional hashing/salting

3. **Login Request**:
   ```python
   response = await do_request_2(
       action="login",
       data={
           "username": username,
           "password": password_hash,
       }
   )
   ```

4. **Response Handling**:
   ```python
   if response.code == 200:
       # Success - extract auth data
       token = response.data["token"]
       token_exp = response.data["exp"]  # Unix timestamp
       nickname = response.data.get("nickname", username)
       permissions = response.data.get("permissions", [])
       groups = response.data.get("groups", [])
       
       # Store in AppConfig
       app_config = AppConfig()
       app_config.username = username
       app_config.token = token
       app_config.token_exp = token_exp
       app_config.nickname = nickname
       app_config.user_permissions = permissions
       app_config.user_groups = groups
       
       # Navigate to home
       await page.push_route("/home")
       
   elif response.code == 401:
       # Invalid credentials
       show_error(_("Invalid username or password"))
       
   elif response.code == 403:
       # Account locked or disabled
       show_error(_("Account is locked or disabled"))
   ```

### Token Management

**Token Storage**:
- Stored in `AppConfig.token` (singleton, in-memory only)
- Not persisted to disk for security
- Cleared on logout or application close

**Token Properties**:
```python
app_config.token: Optional[str]         # JWT or opaque token
app_config.token_exp: Optional[float]   # Unix timestamp expiration
```

**Token Usage**:
All authenticated requests automatically include the token:
```python
# Automatic token injection in do_request()
response = await do_request_2(
    action="some_action",
    data={...}
    # username and token pulled from AppConfig automatically
)
```

**Token Expiration Handling**:
```python
import time

def is_token_expired() -> bool:
    app_config = AppConfig()
    if not app_config.token_exp:
        return True
    return time.time() >= app_config.token_exp

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
    app_config.token = response.data["token"]
    app_config.token_exp = response.data["exp"]
```

### Logout

**Process**:
1. Optionally notify server (if server tracks sessions)
2. Clear authentication data from AppConfig
3. Close WebSocket connection
4. Navigate to login/connect screen

```python
async def logout():
    app_config = AppConfig()
    
    # Optional: notify server
    try:
        await do_request_2(action="logout", data={})
    except:
        pass  # Ignore errors
    
    # Clear auth data
    app_config.username = None
    app_config.token = None
    app_config.token_exp = None
    app_config.nickname = None
    app_config.user_permissions = []
    app_config.user_groups = []
    
    # Close connection
    if app_config.conn:
        await app_config.conn.close()
        app_config.conn = None
    
    # Navigate to login
    await page.push_route("/login")
```

## Authorization (Permissions)

### Permission Model

**Permission Storage**:
```python
app_config.user_permissions: list[str]  # e.g., ["file_upload", "file_delete"]
app_config.user_groups: list[str]       # e.g., ["admins", "editors"]
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
    app_config = AppConfig()
    return "file_upload" in app_config.user_permissions

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
    app_config = AppConfig()
    return "admins" in app_config.user_groups

def has_permission(permission: str) -> bool:
    app_config = AppConfig()
    # Direct permission check
    if permission in app_config.user_permissions:
        return True
    # Group-based permission (if server provides)
    # This depends on server implementation
    return False
```

## SSL/TLS Security

### Certificate Validation

**Integrated CA Certificate**:
Location: `include/constants.py` - `INTEGRATED_CA_CERT`

Contains:
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
    ssl_context.load_verify_locations(cadata=INTEGRATED_CA_CERT)
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

**UI**: Password change dialog (`include/ui/controls/dialogs/passwd.py`)
**Controller**: `include/controllers/dialogs/passwd.py`

**Process**:
1. User enters old password
2. User enters new password (twice for confirmation)
3. Client validates: new password meets requirements
4. Client hashes both passwords
5. Send change request
6. Server validates old password
7. Server updates password

```python
async def change_password(old_pass: str, new_pass: str) -> bool:
    # Client-side validation
    if len(new_pass) < 8:
        show_error(_("Password must be at least 8 characters"))
        return False
    
    # Hash passwords
    old_hash = hashlib.sha256(old_pass.encode()).hexdigest()
    new_hash = hashlib.sha256(new_pass.encode()).hexdigest()
    
    # Request
    response = await do_request_2(
        action="change_password",
        data={
            "old_password": old_hash,
            "new_password": new_hash,
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

1. **Never Store Plaintext Passwords**: Always hash before storing/transmitting
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

## Future Security Enhancements

Potential improvements:
- Multi-factor authentication (MFA)
- Biometric authentication (mobile)
- Hardware security key support (FIDO2)
- End-to-end encryption for files
- Certificate revocation checking (OCSP)
- Security headers for web deployments
