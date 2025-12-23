"""Two-Factor Authentication data structures."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TwoFactorMethod(Enum):
    """Available two-factor authentication methods."""
    TOTP = "totp"  # Time-based One-Time Password


class TwoFactorStatus(Enum):
    """Two-factor authentication status."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    PENDING_SETUP = "pending_setup"


@dataclass
class TwoFactorConfig:
    """
    Two-factor authentication configuration.
    
    Attributes:
        method: The 2FA method being used (e.g., TOTP)
        status: Current status of 2FA (enabled/disabled/pending)
        secret: TOTP secret key (only present during setup)
        backup_codes: List of backup recovery codes
        qr_code_uri: URI for QR code display (only present during setup)
    """
    method: TwoFactorMethod
    status: TwoFactorStatus
    secret: Optional[str] = None
    backup_codes: list[str] = field(default_factory=list)
    qr_code_uri: Optional[str] = None
    
    def __post_init__(self):
        if self.backup_codes is None:
            self.backup_codes = []
