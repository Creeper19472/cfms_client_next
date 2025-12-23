# Two-Factor Authentication (2FA) Architecture

## Overview

This document describes the implementation of Two-Factor Authentication (2FA) using TOTP (Time-based One-Time Password) in the CFMS Client NEXT application.

## Architecture Components

### 1. Data Structures

**Location:** `src/include/classes/twofa.py`

- **TwoFactorMethod**: Enum defining supported 2FA methods
  - `TOTP`: Time-based One-Time Password (currently the only supported method)

- **TwoFactorStatus**: Enum defining 2FA status states
  - `DISABLED`: 2FA is not enabled for the user
  - `ENABLED`: 2FA is active and required for login
  - `PENDING_SETUP`: 2FA setup initiated but not yet verified

- **TwoFactorConfig**: Dataclass containing 2FA configuration
  - `method`: The 2FA method (TOTP)
  - `status`: Current status
  - `secret`: TOTP secret key (only during setup)
  - `backup_codes`: List of backup recovery codes
  - `qr_code_uri`: URI for QR code generation (only during setup)

### 2. Global State Management

**Location:** `src/include/classes/config.py` (AppShared singleton)

New attributes added:
- `user_2fa_enabled`: Boolean indicating if the current user has 2FA enabled
- `pending_2fa_verification`: Boolean tracking if 2FA verification is pending during login

### 3. User Interface Components

#### 3.1 2FA Verification Dialog
**Location:** `src/include/ui/controls/dialogs/twofa_verify.py`

Dialog shown during login when 2FA is enabled:
- Input field for 6-digit TOTP code
- Verify and Cancel buttons
- Calls `on_verify_callback` with the entered code
- Disables interactions while verifying

#### 3.2 2FA Setup Dialog
**Location:** `src/include/ui/controls/dialogs/twofa_setup.py`

Dialog for initial 2FA setup:
- Displays QR code for scanning with authenticator apps
- Shows secret key for manual entry
- Input field to verify setup with a test code
- Uses qrcode library to generate QR code from otpauth:// URI
- Calls `on_verify_callback` to confirm setup

#### 3.3 2FA Settings Page
**Location:** `src/include/ui/models/settings/twofa.py`

Settings page for managing 2FA:
- Shows current 2FA status (enabled/disabled)
- Button to enable 2FA (initiates setup flow)
- Button to disable 2FA (with confirmation dialog)
- Communicates with server via WebSocket requests

### 4. Login Flow Integration

**Location:** `src/include/controllers/login.py`

Modified login process:
1. User enters username and password
2. `login` action sent to server
3. Server response indicates if 2FA is required (`requires_2fa` flag)
4. If 2FA required:
   - Store partial login state
   - Show TwoFactorVerifyDialog
   - User enters TOTP code
   - `verify_2fa_login` action sent to server with code
   - On success, complete login with full credentials
5. If 2FA not required, proceed with normal login

Key methods:
- `_action_login()`: Initial login request
- `_verify_2fa_code(code)`: Verify TOTP code
- `_complete_login(username, data)`: Finalize login after verification
- `_cancel_2fa_login()`: Handle 2FA cancellation

### 5. Server Communication Protocol

#### Actions (WebSocket)

**get_2fa_status**
- Request: `{"action": "get_2fa_status", "username": "...", "token": "..."}`
- Response: `{"code": 200, "data": {"enabled": true/false}}`
- Purpose: Check if user has 2FA enabled

**setup_2fa**
- Request: `{"action": "setup_2fa", "data": {"method": "totp"}, "username": "...", "token": "..."}`
- Response: `{"code": 200, "data": {"secret": "...", "qr_uri": "otpauth://..."}}`
- Purpose: Initialize 2FA setup and get secret/QR code

**verify_2fa_setup**
- Request: `{"action": "verify_2fa_setup", "data": {"code": "123456"}, "username": "...", "token": "..."}`
- Response: `{"code": 200}` on success
- Purpose: Verify setup code and enable 2FA

**cancel_2fa_setup**
- Request: `{"action": "cancel_2fa_setup", "username": "...", "token": "..."}`
- Response: `{"code": 200}`
- Purpose: Cancel pending 2FA setup

**disable_2fa**
- Request: `{"action": "disable_2fa", "username": "...", "token": "..."}`
- Response: `{"code": 200}`
- Purpose: Disable 2FA for the user

**login** (modified)
- Request: `{"action": "login", "data": {"username": "...", "password": "..."}}`
- Response: `{"code": 200, "data": {"requires_2fa": true/false, "token": "...", ...}}`
- Purpose: Initial login, indicates if 2FA is required

**verify_2fa_login**
- Request: `{"action": "verify_2fa_login", "data": {"username": "...", "code": "123456"}}`
- Response: `{"code": 200, "data": {"token": "...", "permissions": [...], "groups": [...], ...}}`
- Purpose: Complete login with 2FA verification

### 6. Utility Functions

**Location:** `src/include/util/twofa.py`

Helper functions for TOTP operations:
- `verify_totp_code(secret, code)`: Verify a TOTP code (client-side validation)
- `generate_totp_uri(secret, username, issuer)`: Generate otpauth:// URI
- `get_current_totp_code(secret)`: Get current TOTP code (for testing)
- `format_secret_for_display(secret)`: Format secret with spaces for readability

### 7. Dependencies

Added to `pyproject.toml`:
- `pyotp`: TOTP generation and verification
- `qrcode`: QR code generation
- `pillow`: Image processing for QR codes

## User Workflows

### Enabling 2FA

1. User navigates to Settings → Two-Factor Authentication
2. Clicks "Enable Two-Factor Authentication"
3. Client requests setup from server (`setup_2fa`)
4. Server generates secret and returns with QR URI
5. Client displays QR code and secret in setup dialog
6. User scans QR code with authenticator app (Google Authenticator, Authy, etc.)
7. User enters verification code from app
8. Client sends code to server (`verify_2fa_setup`)
9. Server verifies code and enables 2FA
10. Client updates UI to show 2FA enabled

### Logging in with 2FA

1. User enters username and password
2. Client sends login request
3. Server validates credentials and returns `requires_2fa: true`
4. Client shows 2FA verification dialog
5. User enters 6-digit code from authenticator app
6. Client sends code to server (`verify_2fa_login`)
7. Server verifies code and returns full login credentials
8. Client completes login and navigates to home

### Disabling 2FA

1. User navigates to Settings → Two-Factor Authentication
2. Clicks "Disable Two-Factor Authentication"
3. Client shows confirmation dialog
4. User confirms
5. Client sends disable request (`disable_2fa`)
6. Server disables 2FA
7. Client updates UI to show 2FA disabled

## Security Considerations

1. **Server-side Verification**: All TOTP verification MUST be performed on the server. Client-side utilities are for convenience only.

2. **Secret Handling**: TOTP secrets should only be transmitted during initial setup and never stored client-side permanently.

3. **Time Synchronization**: TOTP relies on accurate time. Ensure both client and server clocks are synchronized (NTP recommended).

4. **Window Tolerance**: A small time window (±30 seconds) is typically used to account for clock drift.

5. **Token Security**: The authentication token should be refreshed/renewed after successful 2FA verification.

6. **Backup Codes**: Consider implementing backup recovery codes for cases where the user loses access to their authenticator device.

7. **Rate Limiting**: Server should implement rate limiting on 2FA verification attempts to prevent brute force attacks.

## Testing Considerations

Since this is a client-side implementation that requires server support:

1. **Manual Testing**: Test the UI flows with a mock/test server that implements the required actions
2. **Integration Testing**: Verify communication with actual server implementation
3. **Error Handling**: Test scenarios like:
   - Invalid codes
   - Network failures during verification
   - Setup cancellation
   - Time synchronization issues

## Future Enhancements

1. **Backup Codes**: Display and allow regeneration of backup recovery codes
2. **Multiple Methods**: Support additional 2FA methods (SMS, email, hardware keys)
3. **Recovery Flow**: Implement account recovery if 2FA device is lost
4. **Trust This Device**: Option to skip 2FA for trusted devices (30 days)
5. **2FA Status Indicators**: Show 2FA status in user profile/account info

## Integration Checklist for Server Implementation

Server must implement the following:

- [ ] Generate TOTP secrets using a secure random generator
- [ ] Store TOTP secrets securely (encrypted at rest)
- [ ] Implement `get_2fa_status` action
- [ ] Implement `setup_2fa` action with secret generation
- [ ] Implement `verify_2fa_setup` action with TOTP verification
- [ ] Implement `cancel_2fa_setup` action
- [ ] Implement `disable_2fa` action
- [ ] Modify `login` action to check 2FA status and return `requires_2fa` flag
- [ ] Implement `verify_2fa_login` action with TOTP verification
- [ ] Generate backup recovery codes (optional but recommended)
- [ ] Implement rate limiting on 2FA verification attempts
- [ ] Log 2FA events for security auditing

## Example Server Response Formats

### setup_2fa Success Response
```json
{
  "code": 200,
  "message": "2FA setup initiated",
  "data": {
    "secret": "JBSWY3DPEHPK3PXP",
    "qr_uri": "otpauth://totp/CFMS:username?secret=JBSWY3DPEHPK3PXP&issuer=CFMS",
    "backup_codes": ["12345678", "23456789", "34567890"]
  },
  "timestamp": 1703347200.0
}
```

### login Response (2FA Required)
```json
{
  "code": 200,
  "message": "2FA verification required",
  "data": {
    "requires_2fa": true,
    "username": "user123"
  },
  "timestamp": 1703347200.0
}
```

### verify_2fa_login Success Response
```json
{
  "code": 200,
  "message": "Login successful",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "exp": 1703433600.0,
    "nickname": "John Doe",
    "permissions": ["read", "write"],
    "groups": ["users"],
    "has_2fa": true
  },
  "timestamp": 1703347200.0
}
```

## Localization Strings

The implementation uses gettext for internationalization. Key strings to translate:

- "Two-Factor Authentication"
- "Verification Code"
- "Enter 6-digit code"
- "Verify"
- "Cancel"
- "Enable Two-Factor Authentication"
- "Disable Two-Factor Authentication"
- "Two-Factor Authentication Status: Enabled"
- "Two-Factor Authentication Status: Disabled"
- "Scan this QR code with your authenticator app"
- "Or enter this key manually"
- "Secret Key (manual entry)"
- "Enter verification code to confirm"
- "Verify and Enable"
- "Invalid verification code"
- "Two-Factor Authentication enabled successfully!"
- "Are you sure you want to disable two-factor authentication?"
- And more...

All strings are already wrapped with `_()` for translation extraction.
