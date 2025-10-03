from typing import Optional, Any
import threading

from include.classes.client import LockableClientConnection

__all__ = ["AppConfig"]


class AppConfig(object):
    _instance_lock = threading.Lock()

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
    ):
        self.conn = conn
        self.server_address = server_address
        self.server_info = server_info

        self.username = username
        self.token = token
        self.token_exp = token_exp

        self.nickname = nickname
        self.user_permissions = user_permissions
        self.user_groups = user_groups

    def __new__(cls, *args, **kwargs):
        if not hasattr(AppConfig, "_instance"):
            with AppConfig._instance_lock:
                if not hasattr(AppConfig, "_instance"):
                    AppConfig._instance = object.__new__(cls)
        return AppConfig._instance
