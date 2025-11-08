"""Application configuration management module."""

import os
import threading
from typing import Any, Optional

import yaml
from flet_permission_handler import PermissionHandler
from websockets.asyncio.client import ClientConnection

from include.constants import FLET_APP_STORAGE_DATA

PREFERENCES_PATH = f"{FLET_APP_STORAGE_DATA}/preferences.yaml"

__all__ = ["AppConfig"]


class AppConfig:
    """
    Singleton application configuration manager.
    
    This class manages global application state including server connection,
    user credentials, and user preferences. It implements the singleton pattern
    to ensure only one instance exists throughout the application lifecycle.
    
    Attributes:
        server_address: URL of the connected server
        server_info: Information about the connected server
        disable_ssl_enforcement: Whether to skip SSL certificate validation
        username: Current logged-in username
        token: Authentication token
        token_exp: Token expiration timestamp
        nickname: User's display name
        user_permissions: List of user permission strings
        user_groups: List of groups the user belongs to
        conn: Active WebSocket connection to server
        ph_service: Permission handler service instance
        preferences: User preferences dictionary loaded from YAML
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

        # Server configuration
        self.server_address: Optional[str] = None
        self.server_info: dict[str, Any] = {}
        self.disable_ssl_enforcement: bool = False
        
        # User authentication
        self.username: Optional[str] = None
        self.token: Optional[str] = None
        self.token_exp: Optional[float] = None
        self.nickname: Optional[str] = None
        self.user_permissions: list[str] = []
        self.user_groups: list[str] = []
        
        # Connection and services
        self.conn: Optional[ClientConnection] = None
        self.ph_service: Optional[PermissionHandler] = None

        # Load preferences
        if not os.path.exists(PREFERENCES_PATH):
            self._init_preferences()

        with open(PREFERENCES_PATH, "r", encoding="utf-8") as file:
            self.preferences = yaml.safe_load(file)

        self._initialized = True

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
            }
        }

        with open(PREFERENCES_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(default_preferences, f)

    def dump_preferences(self) -> None:
        """Save current preferences to disk."""
        with open(PREFERENCES_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.preferences, f)
