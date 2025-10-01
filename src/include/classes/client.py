import asyncio
from websockets import ClientProtocol
from websockets.asyncio.client import ClientConnection


class LockableClientConnection(ClientConnection):
    def __init__(
        self,
        connection: ClientConnection,
    ) -> None:
        self.lock = asyncio.Lock()
        self._wrapped_connection = connection
        super().__init__(
            connection.protocol,
            ping_interval=connection.ping_interval,
            ping_timeout=connection.ping_timeout,
            close_timeout=connection.close_timeout,
            max_queue=connection.max_queue,
            write_limit=connection.write_limit,
        )

    def __getattr__(self, name):
        return getattr(self._wrapped_connection, name)
