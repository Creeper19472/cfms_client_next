"""Application-wide constants and configuration values."""

import os
from pathlib import Path
from .classes.version import ChannelType


__all__ = [
    "RUNTIME_PATH",
    "FLET_APP_CONSOLE",
    "FLET_APP_STORAGE_TEMP",
    "FLET_APP_STORAGE_DATA",
    "APP_VERSION",
    "BUILD_VERSION",
    "PROTOCOL_VERSION",
    "DEFAULT_WINDOW_TITLE",
    "GITHUB_REPO",
    "DEFAULT_UPDATE_CHANNEL",
    "CA_CERT_REPO",
    "CA_CERT_API_URL",
]

# Path Configuration
CONSTANT_FILE_ABSPATH = os.path.abspath(__file__)
ROOT_PATH = Path(CONSTANT_FILE_ABSPATH).resolve().parent.parent
LOCALE_PATH = ROOT_PATH / "include" / "ui" / "locale"
RUNTIME_PATH = os.environ.get("PYTHONHOME", "")
FLET_APP_CONSOLE = os.environ.get("FLET_APP_CONSOLE", "")
FLET_APP_STORAGE_TEMP = os.environ.get("FLET_APP_STORAGE_TEMP", ".")
FLET_APP_STORAGE_DATA = os.environ.get("FLET_APP_STORAGE_DATA", ".")
FLET_ASSETS_DIR = os.environ.get("FLET_ASSETS_DIR", None)
LOGFILE_PATH = Path(FLET_APP_STORAGE_TEMP) / "cfms_client.log"
USER_PREFERENCES_PATH = f"{FLET_APP_STORAGE_DATA}/user_preferences"
GLOBAL_PREFERENCES_PATH = f"{FLET_APP_STORAGE_DATA}/preferences.yaml"

# Application Info
DEFAULT_WINDOW_TITLE = "CFMS Client"
GITHUB_REPO = "Creeper19472/cfms_client_next"

# CA certificate store repository (GitHub API)
# Update this constant to change the certificate store source for the whole application.
CA_CERT_REPO = "cfms-dev/ca"
CA_CERT_API_URL = f"https://api.github.com/repos/{CA_CERT_REPO}/contents/"

# Version Information
CHANNEL = ChannelType.STABLE
BUILD_VERSION = "v0.11.0"
MODIFIED = "20260313"

# Default update channel for user preferences
DEFAULT_UPDATE_CHANNEL = ChannelType.STABLE

if CHANNEL == ChannelType.STABLE:
    APP_VERSION = f"{BUILD_VERSION[1:]}.{MODIFIED} NEXT"
else:
    APP_VERSION = f"{BUILD_VERSION[1:]}.{MODIFIED}_{CHANNEL.value} NEXT"

# Protocol
PROTOCOL_VERSION = 9
