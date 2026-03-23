"""Application configuration management module."""

import os
import threading
import hashlib
from typing import Any, Optional, TYPE_CHECKING

import yaml

from websockets.asyncio.client import ClientConnection

from include.classes.frame import AsyncMultiplexConnection
from include.classes.preferences import UserPreference
from include.constants import DEFAULT_UPDATE_CHANNEL, GLOBAL_PREFERENCES_PATH
from include.util.merging import merge_with_template

if TYPE_CHECKING:
    from include.classes.services.manager import ServiceManager
    from include.ui.controls.buttons.upgrade import FloatingUpgradeButton
    from include.ui.controls.components.common.monitor import MonitorStack
    import flet as ft

__all__ = ["AppShared"]

GLOBAL_PREFERENCE_TEMPLATE = {
    "settings": {
        "language": "zh_CN",
        "proxy_settings": None,
        "custom_proxy": "",
        "enable_conn_history_logging": False,
        "force_ipv4": False,
        "update_channel": DEFAULT_UPDATE_CHANNEL.value,  # Channel for checking updates
    },
    "license": {"disclaimer_accepted": False},
}


class AppShared:
    """
    AppShared is a singleton class that manages shared application state and configuration.
    This class provides a centralized place to store runtime constants, server configuration,
    user authentication details, connection and service references, and user preferences.
    It ensures only one instance exists throughout the application's lifecycle.
    Attributes:
        is_mobile (bool): Indicates if the application is running on a mobile device.
        server_address (Optional[str]): The address of the server.
        _server_address_hash (Optional[str]): Cached hash of the server address.
        server_info (dict[str, Any]): Information about the connected server.
        disable_ssl_enforcement (bool): Whether SSL enforcement is disabled.
        username (Optional[str]): The username of the authenticated user.
        token (Optional[str]): The authentication token.
        token_exp (Optional[float]): Expiration time of the authentication token.
        nickname (Optional[str]): The user's nickname.
        user_permissions (list[str]): List of permissions assigned to the user.
        user_groups (list[str]): List of groups the user belongs to.
        user_2fa_enabled (bool): Whether the user has 2FA enabled.
        pending_2fa_verification (bool): Whether 2FA verification is pending for login.
        conn (Optional[ClientConnection]): The client connection object.
        service_manager (Optional["ServiceManager"]): The service manager instance.
        floating_upgrade_button (Optional["FloatingUpgradeButton"]): Reference to the upgrade button.
        user_perference (Optional[UserPreference]): The user's preferences.
        dek (Optional[bytes]): In-memory Data Encryption Key for config encryption.
        preferences (dict): Loaded user preferences from disk.
    Methods:
        server_address_hash: Returns the hashed server address for caching purposes.
        get_not_none_attribute(name): Retrieves an attribute value, asserting it is not None.
        _init_preferences(): Initializes the preferences file with default values.
        dump_preferences(): Saves the current preferences to disk.
    """

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        # Runtime constants
        self.is_mobile: bool = False
        self.is_production: bool = False

        # Server configuration
        self.server_address: Optional[str] = None
        self._server_address_hash: Optional[str] = None
        self.server_info: dict[str, Any] = {}
        self.disable_ssl_enforcement: bool = False

        # User authentication
        self.username: Optional[str] = None
        self.token: Optional[str] = None
        self.token_exp: Optional[float] = None
        self.nickname: Optional[str] = None
        self.avatar_id: Optional[str] = None
        self.avatar_path: Optional[str] = None
        self.user_permissions: list[str] = []
        self.user_groups: list[str] = []
        self.user_2fa_enabled: bool = False
        self.pending_2fa_verification: bool = False

        # Connection and services
        self.conn: Optional[AsyncMultiplexConnection] = None
        self.service_manager: Optional["ServiceManager"] = None
        self.floating_upgrade_button: Optional["FloatingUpgradeButton"] = None

        # User preferences
        self.user_perference: Optional[UserPreference] = None

        # In-memory Data Encryption Key for user config encryption (never persisted)
        self.dek: Optional[bytes] = None

        # Control refs
        self.monitor_ref: Optional["ft.Ref[MonitorStack]"] = None

        # Load preferences
        if not os.path.exists(GLOBAL_PREFERENCES_PATH):
            self._init_preferences()

        with open(GLOBAL_PREFERENCES_PATH, "r", encoding="utf-8") as file:
            self.preferences = yaml.safe_load(file)

        # Merge with template to ensure all keys are present
        self.preferences = merge_with_template(
            self.preferences, GLOBAL_PREFERENCE_TEMPLATE
        )

        self._initialized = True

    @property
    def server_address_hash(self) -> Optional[str]:
        """Get the hashed server address for caching purposes."""
        if self._server_address_hash is not None:
            return self._server_address_hash
        else:
            if not self.server_address:
                raise ValueError("Server address is not set")
            self._server_address_hash = hashlib.sha256(
                self.server_address.encode("utf-8")
            ).hexdigest()
            return self._server_address_hash

    def get_not_none_attribute(self, name: str):
        """
        Get an attribute value, asserting it is not None.

        Args:
            name: Name of the attribute to retrieve

        Returns:
            The attribute value

        Raises:
            AssertionError: If the attribute is None
        """
        _attr = getattr(self, name)
        assert _attr is not None, f"Attribute '{name}' must not be None"
        return _attr

    def _init_preferences(self) -> None:
        """Initialize preferences file with default values."""
        with open(GLOBAL_PREFERENCES_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(GLOBAL_PREFERENCE_TEMPLATE, f)

    def dump_preferences(self) -> None:
        """Save current preferences to disk and user preferences if logged in."""
        # Save application-level preferences
        with open(GLOBAL_PREFERENCES_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.preferences, f)

        # Save user-specific preferences if user is logged in
        if self.username is not None and self.user_perference is not None:
            from include.util.userpref import save_user_preference

            save_user_preference(self.username, self.user_perference)
