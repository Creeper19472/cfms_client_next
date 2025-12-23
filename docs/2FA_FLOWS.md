# Two-Factor Authentication Flows

This document provides visual flow diagrams for the 2FA implementation.

## Flow 1: Enabling 2FA (First-Time Setup)

```
┌─────────────┐
│   User      │
│ (Logged In) │
└──────┬──────┘
       │
       │ Navigate to Settings
       ▼
┌──────────────────────────┐
│  Settings > 2FA Settings │
│  Status: Disabled        │
└──────┬───────────────────┘
       │
       │ Click "Enable 2FA"
       ▼
┌────────────────────────────────┐
│  Client                        │
│  → setup_2fa                   │
└────────────┬───────────────────┘
             │
             ▼
      ┌─────────────┐
      │   Server    │
      │  Generates  │
      │   Secret    │
      └──────┬──────┘
             │
             │ Returns: secret, qr_uri
             ▼
┌──────────────────────────────────────┐
│  TwoFactorSetupDialog                │
│  ┌────────────────────────────────┐  │
│  │   [QR Code Display]            │  │
│  │                                │  │
│  │   Secret: ABCD EFGH IJKL MNOP  │  │
│  └────────────────────────────────┘  │
│                                      │
│  User scans QR with auth app         │
│  (Google Auth, Authy, etc.)          │
│                                      │
│  [______] ← Enter code from app      │
│  [Verify and Enable]  [Cancel]       │
└──────────────┬───────────────────────┘
               │
               │ User enters code
               ▼
┌────────────────────────────────┐
│  Client                        │
│  → verify_2fa_setup            │
│     { code: "123456" }         │
└────────────┬───────────────────┘
             │
             ▼
      ┌─────────────┐
      │   Server    │
      │  Verifies   │
      │    Code     │
      └──────┬──────┘
             │
             │ Code Valid → 200 OK
             ▼
┌──────────────────────────┐
│  2FA Settings            │
│  Status: ✅ Enabled      │
│  [Disable 2FA]           │
└──────────────────────────┘
```

## Flow 2: Login with 2FA

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       │ Enter username & password
       ▼
┌────────────────────────────────┐
│  Login Screen                  │
│  Username: [________]          │
│  Password: [________]          │
│          [Login]               │
└────────────┬───────────────────┘
             │
             │ Submit credentials
             ▼
      ┌─────────────┐
      │   Server    │
      │  Validates  │
      │ Credentials │
      └──────┬──────┘
             │
             │ If user has 2FA enabled:
             │ Returns: requires_2fa=true
             ▼
┌──────────────────────────────────────┐
│  TwoFactorVerifyDialog               │
│  ┌────────────────────────────────┐  │
│  │ Two-Factor Authentication      │  │
│  │                                │  │
│  │ Enter the 6-digit code from    │  │
│  │ your authenticator app         │  │
│  │                                │  │
│  │ Code: [______]                 │  │
│  │                                │  │
│  │ [Cancel]  [Verify]             │  │
│  └────────────────────────────────┘  │
└──────────────┬───────────────────────┘
               │
               │ User enters code from auth app
               ▼
┌────────────────────────────────┐
│  Client                        │
│  → verify_2fa_login            │
│     { username, code }         │
└────────────┬───────────────────┘
             │
             ▼
      ┌─────────────┐
      │   Server    │
      │  Verifies   │
      │  TOTP Code  │
      └──────┬──────┘
             │
             │ Code Valid → Full auth token
             ▼
┌──────────────────────────┐
│   Home Screen            │
│   (User logged in)       │
└──────────────────────────┘
```

## Flow 3: Disabling 2FA

```
┌─────────────┐
│   User      │
│ (Logged In) │
└──────┬──────┘
       │
       │ Navigate to Settings
       ▼
┌──────────────────────────┐
│  Settings > 2FA Settings │
│  Status: ✅ Enabled      │
│  [Disable 2FA]           │
└──────┬───────────────────┘
       │
       │ Click "Disable 2FA"
       ▼
┌─────────────────────────────────┐
│  Confirmation Dialog            │
│  ┌───────────────────────────┐  │
│  │ Disable 2FA?              │  │
│  │                           │  │
│  │ Are you sure? This will   │  │
│  │ make your account less    │  │
│  │ secure.                   │  │
│  │                           │  │
│  │ [Cancel]  [Disable]       │  │
│  └───────────────────────────┘  │
└──────────────┬──────────────────┘
               │
               │ User confirms
               ▼
┌────────────────────────────────┐
│  Client                        │
│  → disable_2fa                 │
└────────────┬───────────────────┘
             │
             ▼
      ┌─────────────┐
      │   Server    │
      │  Disables   │
      │     2FA     │
      └──────┬──────┘
             │
             │ Success → 200 OK
             ▼
┌──────────────────────────┐
│  2FA Settings            │
│  Status: ⚠️ Disabled     │
│  [Enable 2FA]            │
└──────────────────────────┘
```

## Component Interaction Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                        Client Application                      │
│                                                                │
│  ┌──────────────────┐      ┌──────────────────────────────┐  │
│  │   UI Layer       │      │      Controllers             │  │
│  │                  │      │                              │  │
│  │  - LoginForm     │─────▶│  - LoginFormController       │  │
│  │  - TwoFAVerify   │      │    • _action_login()         │  │
│  │  - TwoFASetup    │      │    • _verify_2fa_code()      │  │
│  │  - TwoFASettings │      │    • _complete_login()       │  │
│  │                  │      │                              │  │
│  └──────────────────┘      └────────┬─────────────────────┘  │
│                                     │                         │
│                                     │                         │
│  ┌──────────────────────────────────▼────────────────┐       │
│  │              AppShared (Singleton)                │       │
│  │  • username, token, permissions                   │       │
│  │  • user_2fa_enabled: bool                         │       │
│  │  • pending_2fa_verification: bool                 │       │
│  │  • conn: WebSocket connection                     │       │
│  └──────────────────┬────────────────────────────────┘       │
│                     │                                         │
│                     │                                         │
│  ┌──────────────────▼────────────────────────────────┐       │
│  │         Utilities & Helpers                       │       │
│  │  • do_request() / do_request_2()                  │       │
│  │  • TOTP utilities (verify, generate)              │       │
│  │  • QR code generation                             │       │
│  └──────────────────┬────────────────────────────────┘       │
│                     │                                         │
└─────────────────────┼─────────────────────────────────────────┘
                      │
                      │ WebSocket (JSON)
                      │
         ┌────────────▼───────────┐
         │                        │
         │    CFMS Server         │
         │                        │
         │  Actions:              │
         │  • get_2fa_status      │
         │  • setup_2fa           │
         │  • verify_2fa_setup    │
         │  • cancel_2fa_setup    │
         │  • disable_2fa         │
         │  • login (modified)    │
         │  • verify_2fa_login    │
         │                        │
         └────────────────────────┘
```

## State Transitions

```
2FA Status State Machine:

    ┌──────────┐
    │ DISABLED │ ◄─────────────────────┐
    └────┬─────┘                       │
         │                             │
         │ setup_2fa                   │
         │                             │
         ▼                             │
    ┌─────────────┐                    │
    │ PENDING     │                    │
    │ SETUP       │                    │
    └────┬────────┘                    │
         │                             │
         │ verify_2fa_setup            │ disable_2fa
         │ (code valid)                │
         │                             │
         ▼                             │
    ┌──────────┐                       │
    │ ENABLED  │───────────────────────┘
    └──────────┘

Cancel during setup: PENDING_SETUP → DISABLED
Invalid verification: remains in PENDING_SETUP
```

## Error Handling Flows

### Invalid Code During Setup

```
User enters code → verify_2fa_setup → Server validates
                                    → Code invalid (400)
                                    → Dialog shows error
                                    → User can retry
                                    → Or cancel setup
```

### Invalid Code During Login

```
User enters code → verify_2fa_login → Server validates
                                    → Code invalid (401)
                                    → Dialog shows error
                                    → User can retry
                                    → Or cancel (back to login)
```

### Network Error

```
Any request → Connection lost → ConnectionClosed exception
                              → do_request() auto-retries (max 3)
                              → Reconnects automatically
                              → Retries request
                              → Or shows error after retries exhausted
```

## Time Synchronization

```
TOTP Time Window:

     -30s        Current        +30s
       │            │             │
    ┌──┴────────────┴────────────┴──┐
    │   Valid Code Window           │
    │   (90 seconds total)          │
    └───────────────────────────────┘
              │
              │ Server validates code
              │ within this window
              ▼
         Code Valid ✅
```

## Security Considerations in Flows

1. **Secret Transmission**: Only during setup (HTTPS/WSS encrypted)
2. **Code Verification**: Always server-side, never client
3. **Rate Limiting**: Server should limit attempts per user
4. **Token Refresh**: New token after successful 2FA verification
5. **Audit Logging**: All 2FA events logged server-side
6. **No Persistence**: Client never stores TOTP secrets

## Authenticator App Compatibility

The implementation is compatible with all TOTP-based authenticator apps:

- ✅ Google Authenticator
- ✅ Microsoft Authenticator
- ✅ Authy
- ✅ 1Password
- ✅ LastPass Authenticator
- ✅ Duo Mobile
- ✅ FreeOTP
- ✅ Any RFC 6238 compliant app

Users scan the QR code or manually enter the secret into their preferred app.
