"""
Settings models package for the CFMS client UI.

This module serves as a central hub for importing and exporting all settings-related models.
The import order of these models determines their display sequence in the Settings Overview page.

Models (in display order):
    - SettingsModel: Base/overview settings model
    - LanguageSettingsModel: Language and localization settings
    - ConnectionSettingsModel: Network and connection settings
    - StorageSettingsModel: Storage and cache settings
    - SafetySettingsModel: Security, safety and CA certificate management
    - UpdatesSettingsModel: Software updates and version settings
    - TwoFactorSettingsModel: Two-factor authentication settings

Note:
    The order of model imports directly corresponds to the order in which they appear 
    in the Settings Overview UI. Reordering the imports will change the display sequence.
"""

from .overview import SettingsModel
from .language import LanguageSettingsModel
from .connection import ConnectionSettingsModel
from .storage import StorageSettingsModel
from .safety import SafetySettingsModel
from .updates import UpdatesSettingsModel
from .twofa import TwoFactorSettingsModel

__all__ = [
    "SettingsModel",
    "LanguageSettingsModel",
    "ConnectionSettingsModel",
    "StorageSettingsModel",
    "SafetySettingsModel",
    "UpdatesSettingsModel",
    "TwoFactorSettingsModel",
]
