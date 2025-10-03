from typing import Optional, Any
import threading

from flet_permission_handler import PermissionHandler

from include.classes.client import LockableClientConnection

__all__ = ["AppConfig"]


class AppConfig(object):
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        server_address: Optional[str] = None,
        server_info: dict[str, Any] = {},
        username: Optional[str] = None,
        token: Optional[str] = None,
        token_exp: Optional[float] = None,
        nickname: Optional[str] = None,
        user_permissions: list[str] = [],
        user_groups: list[str] = [],
        conn: Optional[LockableClientConnection] = None,
        ph_service: Optional[PermissionHandler] = None
    ):
        if getattr(self, "_initialized", False):
            return
        self.conn = conn
        self.ph_service = ph_service
        self.server_address = server_address
        self.server_info = server_info if server_info is not None else {}
        self.username = username
        self.token = token
        self.token_exp = token_exp
        self.nickname = nickname
        self.user_permissions = user_permissions
        self.user_groups = user_groups
        self._initialized = True

    def get_not_none_attribute(self, name):
        _attr = getattr(self, name)
        assert _attr is not None
        return _attr
