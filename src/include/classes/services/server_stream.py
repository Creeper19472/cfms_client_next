"""Service for handling server streams."""

from typing import Optional

from include.classes.frame import AsyncMultiplexConnection
from include.classes.services.base import BaseService


class ServerStreamHandleService(BaseService):
    def __init__(
        self,
        enabled: bool = True,
    ):
        super().__init__(name="server_stream", enabled=enabled, interval=0)
        self.connection: Optional["AsyncMultiplexConnection"] = None

    def set_connection(self, connection: "AsyncMultiplexConnection"):
        self.connection = connection
