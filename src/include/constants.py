"""Application-wide constants and configuration values."""

import os
from pathlib import Path
from .classes.version import ChannelType


__all__ = [
    "RUNTIME_PATH",
    "FLET_APP_STORAGE_TEMP",
    "FLET_APP_STORAGE_DATA",
    "APP_VERSION",
    "BUILD_VERSION",
    "PROTOCOL_VERSION",
    "DEFAULT_WINDOW_TITLE",
    "GITHUB_REPO",
    "DEFAULT_UPDATE_CHANNEL",
]

# Path Configuration
CONSTANT_FILE_ABSPATH = os.path.abspath(__file__)
ROOT_PATH = Path(CONSTANT_FILE_ABSPATH).resolve().parent.parent
LOCALE_PATH = f"{ROOT_PATH}/include/ui/locale"
RUNTIME_PATH = os.environ.get("PYTHONHOME", "")
FLET_APP_STORAGE_TEMP = os.environ.get("FLET_APP_STORAGE_TEMP", ".")
FLET_APP_STORAGE_DATA = os.environ.get("FLET_APP_STORAGE_DATA", ".")
USER_PREFERENCES_PATH = f"{FLET_APP_STORAGE_DATA}/user_preferences"

# Application Info
DEFAULT_WINDOW_TITLE = "CFMS Client"
GITHUB_REPO = "Creeper19472/cfms_client_next"

# Version Information
CHANNEL = ChannelType.STABLE
BUILD_VERSION = "v0.6.3"
MODIFIED = "20260222"

# Default update channel for user preferences
DEFAULT_UPDATE_CHANNEL = ChannelType.STABLE

if CHANNEL == ChannelType.STABLE:
    APP_VERSION = f"{BUILD_VERSION[1:]}.{MODIFIED} NEXT"
else:
    APP_VERSION = f"{BUILD_VERSION[1:]}.{MODIFIED}_{CHANNEL.value} NEXT"

# Protocol
PROTOCOL_VERSION = 9
