"""Utility functions for Two-Factor Authentication operations."""

import pyotp
from typing import Optional


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """
    Verify a TOTP code against a secret.
    
    This is primarily for client-side validation, but the server
    should always perform the final verification.
    
    Args:
        secret: The TOTP secret key (base32 encoded)
        code: The 6-digit code to verify
        window: Number of time windows to check (default 1 = 30s before/after)
        
    Returns:
        True if the code is valid, False otherwise
    """
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)
    except Exception:
        return False


def generate_totp_uri(secret: str, username: str, issuer: str = "CFMS") -> str:
    """
    Generate an otpauth:// URI for QR code generation.
    
    Args:
        secret: The TOTP secret key (base32 encoded)
        username: The user's username/identifier
        issuer: The issuer name (typically application name)
        
    Returns:
        otpauth:// URI string
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def get_current_totp_code(secret: str) -> str:
    """
    Get the current TOTP code for a secret.
    
    This is primarily for testing/debugging purposes.
    
    Args:
        secret: The TOTP secret key (base32 encoded)
        
    Returns:
        Current 6-digit TOTP code
    """
    totp = pyotp.TOTP(secret)
    return totp.now()


def format_secret_for_display(secret: str) -> str:
    """
    Format a secret key for user-friendly display.
    
    Adds spaces every 4 characters for easier manual entry.
    
    Args:
        secret: The TOTP secret key
        
    Returns:
        Formatted secret with spaces (e.g., "ABCD EFGH IJKL")
    """
    return " ".join([secret[i:i+4] for i in range(0, len(secret), 4)])
