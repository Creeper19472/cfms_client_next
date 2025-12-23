# Examples

This directory contains example scripts demonstrating various features of CFMS Client NEXT.

## Available Examples

### totp_demo.py

Demonstrates the Two-Factor Authentication (TOTP) utilities including:
- Secret generation
- OTP URI creation for QR codes
- TOTP code generation
- Code verification
- Secret formatting for display

**Prerequisites:**
```bash
# Install dependencies first
uv sync  # or poetry install
```

**Usage:**
```bash
python examples/totp_demo.py
```

**Note:** This is a demonstration only. In production, TOTP secrets should always be generated and stored securely on the server side.

## Running Examples

All examples should be run from the repository root directory:

```bash
cd /path/to/cfms_client_next
python examples/example_name.py
```
