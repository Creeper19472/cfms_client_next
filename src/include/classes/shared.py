"""Application configuration management module."""

import os
import threading
import hashlib
from typing import Any, Optional, TYPE_CHECKING

import yaml
from flet_permission_handler import PermissionHandler
from websockets.asyncio.client import ClientConnection

from include.classes.preferences import UserPreference
from include.constants import FLET_APP_STORAGE_DATA, DEFAULT_UPDATE_CHANNEL

if TYPE_CHECKING:
    from include.classes.services.manager import ServiceManager
    from include.ui.controls.buttons.upgrade import FloatingUpgradeButton

PREFERENCES_PATH = f"{FLET_APP_STORAGE_DATA}/preferences.yaml"

__all__ = ["AppShared"]


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
        ph_service (Optional[PermissionHandler]): The permission handler service.
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
        clear_user_state(): Clears all user authentication and session state (for logout).
        save_current_user_tasks(): Saves the current user's download tasks to disk.
        prepare_logout(): Saves tasks and preferences before clearing user state.
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
        self.conn: Optional[ClientConnection] = None
        self.ph_service: Optional[PermissionHandler] = None
        self.service_manager: Optional["ServiceManager"] = None
        self.floating_upgrade_button: Optional["FloatingUpgradeButton"] = None

        # User preferences
        self.user_perference: Optional[UserPreference] = None

        # In-memory Data Encryption Key for user config encryption (never persisted)
        self.dek: Optional[bytes] = None

        # Load preferences
        if not os.path.exists(PREFERENCES_PATH):
            self._init_preferences()

        with open(PREFERENCES_PATH, "r", encoding="utf-8") as file:
            self.preferences = yaml.safe_load(file)

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
        default_preferences = {
            "settings": {
                "language": "zh_CN",
                "proxy_settings": None,
                "custom_proxy": "",
                "enable_conn_history_logging": False,
                "force_ipv4": False,
                "update_channel": DEFAULT_UPDATE_CHANNEL.value,  # Channel for checking updates
            }
        }

        with open(PREFERENCES_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(default_preferences, f)

    def dump_preferences(self) -> None:
        """Save current preferences to disk and user preferences if logged in."""
        # Save application-level preferences
        with open(PREFERENCES_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.preferences, f)
        
        # Save user-specific preferences if user is logged in
        if self.username is not None and self.user_perference is not None:
            from include.util.userpref import save_user_preference
            save_user_preference(self.username, self.user_perference)

    def clear_user_state(self) -> None:
        """Clear all user-specific authentication and session state.

        Call this when logging out.  Server connection and server
        configuration are intentionally preserved so the login screen can
        reuse the existing connection.
        """
        self.username = None
        self.token = None
        self.token_exp = None
        self.nickname = None
        self.avatar_id = None
        self.avatar_path = None
        self.user_permissions = []
        self.user_groups = []
        self.user_2fa_enabled = False
        self.pending_2fa_verification = False
        self.user_perference = None
        self.dek = None

    async def save_current_user_tasks(self) -> None:
        """Save the current user's in-progress download tasks to disk.

        This is a convenience wrapper around the download manager service's
        persistence method.  It is safe to call even when no user is logged in
        or when the service is not available — in those cases it does nothing.
        """
        if self.service_manager:
            from include.classes.services.download import DownloadManagerService

            download_service = self.service_manager.get_service(
                DownloadManagerService.SERVICE_NAME, DownloadManagerService
            )
            if download_service:
                await download_service._save_tasks()

    async def prepare_logout(self) -> None:
        """Persist state and save in-progress tasks before clearing user session.

        Call this immediately before :meth:`clear_user_state` when logging out
        or switching accounts.  It saves the current user's download tasks to
        disk and flushes application and user preferences so nothing is lost.

        This coroutine is separated from :meth:`clear_user_state` so that the
        caller remains responsible for navigation after the state is cleared.
        """
        await self.save_current_user_tasks()
        self.dump_preferences()
