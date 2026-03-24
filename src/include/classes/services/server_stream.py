"""Service for handling server-initiated (push) messages."""

__all__ = ["ServerStreamHandleService"]

import asyncio
import json
from typing import Any, Awaitable, Callable, Dict, List, Optional
import flet as ft

from include.classes.frame import AsyncMultiplexConnection, AsyncStream
from include.classes.services.base import BaseService


# Type alias for message handlers called with (event, data).
MessageHandler = Callable[[str, dict[str, Any], Optional[ft.Page]], Awaitable[None]]


class ServerStreamHandleService(BaseService):
    """Service that accepts and dispatches server-initiated (push) messages.

    The server may proactively open new streams to deliver messages to the
    client without a preceding client request.  This service waits for those
    streams and dispatches their JSON payloads to registered handlers.

    Only one connection is active at a time.

    Usage::

        # Register the service in main.py
        server_stream_service = ServerStreamHandleService(enabled=True)
        service_manager.register(server_stream_service)

        # After establishing a connection, hand it to the service
        server_stream_service.connection = conn

        # Register a handler for a specific server event
        async def on_notify(event: str, data: dict) -> None:
            print(f"Server notification: {data}")

        server_stream_service.add_handler("notify", on_notify)
    """

    def __init__(self, page: Optional[ft.Page] = None, enabled: bool = True) -> None:
        super().__init__(name="server_stream", enabled=enabled, interval=0)

        self.page = page
        self._connection: Optional[AsyncMultiplexConnection] = None
        # Set when set_connection() is called; wakes up a waiting execute().
        self._connection_ready: asyncio.Event = asyncio.Event()

        # Registered handlers keyed by event name.
        self._event_handlers: Dict[str, List[MessageHandler]] = {}
        # Handlers that receive every server-pushed message regardless of event.
        self._fallback_handlers: List[MessageHandler] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def connection(self) -> Optional[AsyncMultiplexConnection]:
        """The currently active connection, or None if no connection is active."""
        return self._connection

    @connection.setter
    def connection(self, connection: Optional[AsyncMultiplexConnection]) -> None:
        """Replace the active connection with *connection*.

        This may be called at any time – including while the service is
        already listening on a previous connection.  The previous connection
        is left open (it may still be used for in-flight requests); the
        listen loop will detect the replacement via the ``_connection_ready``
        event and switch over on the next iteration.

        Args:
            connection: The new :class:`AsyncMultiplexConnection` to listen on.
        """
        self._connection = connection
        if connection is not None:
            self._connection_ready.set()
        else:
            self._connection_ready.clear()

    def add_handler(self, event: str, handler: MessageHandler) -> None:
        """Register *handler* to be called for server-pushed messages whose
        ``event`` field equals *event*.

        Args:
            event: The event name to match (case-sensitive).
            handler: An async callable ``(event, data, page) -> None``.
        """
        self._event_handlers.setdefault(event, []).append(handler)

    def add_fallback_handler(self, handler: MessageHandler) -> None:
        """Register *handler* to be called for **every** server-pushed message,
        regardless of its ``event`` field.

        Args:
            handler: An async callable ``(event, data, page) -> None``.
        """
        self._fallback_handlers.append(handler)

    # ------------------------------------------------------------------
    # BaseService implementation
    # ------------------------------------------------------------------

    async def execute(self) -> None:
        """Accept and dispatch incoming server-pushed streams.

        Waits for a connection to be provided via :meth:`set_connection`,
        then loops over server-initiated streams dispatching each one to
        the registered handlers.  Returns (allowing the base-class run-loop
        to call :meth:`execute` again) as soon as the active connection
        closes **or** is replaced.
        """
        # Block until a connection is available.
        if self._connection is None:
            await self._connection_ready.wait()

        # Consume the "ready" signal so we don't immediately return on the
        # next iteration without waiting for a genuinely new connection.
        self._connection_ready.clear()

        connection = self._connection
        if connection is None:
            # Spurious wake-up; try again on the next execute() call.
            return

        self.logger.debug("Listening for server-pushed messages")

        while True:
            # Race between an incoming server-pushed stream and a new
            # set_connection() call that replaces the current connection.
            accept_task: asyncio.Task = asyncio.create_task(connection.accept_stream())
            ready_task: asyncio.Task = asyncio.create_task(
                self._connection_ready.wait()
            )

            try:
                done, pending = await asyncio.wait(
                    {accept_task, ready_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
            except BaseException:
                # Service is being stopped (CancelledError) or another error;
                # cancel both tasks and propagate the exception.
                accept_task.cancel()
                ready_task.cancel()
                raise

            # Cancel whichever task lost the race.
            for task in pending:
                task.cancel()

            if ready_task in done:
                # A new connection was provided via set_connection(); return so
                # execute() will restart and pick up the new connection.
                self.logger.debug(
                    "Connection replaced; restarting listen loop on new connection"
                )
                return

            # accept_task is in done – a new server-pushed stream arrived.
            try:
                stream: Optional[AsyncStream] = accept_task.result()
            except Exception as exc:
                self.logger.warning(
                    "Error while accepting server-pushed stream: %s", exc
                )
                stream = None

            if stream is None:
                # The connection was closed by the remote end or an error.
                if self._connection is connection:
                    self._connection = None
                self.logger.info("Connection closed; waiting for a new connection")
                return

            # Dispatch the stream concurrently so slow handlers cannot block
            # the processing of other incoming messages.
            asyncio.create_task(self._dispatch_stream(stream))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _dispatch_stream(self, stream: AsyncStream) -> None:
        """Read a single server-pushed stream and invoke registered handlers.

        Args:
            stream: The server-initiated :class:`AsyncStream` to handle.
        """
        try:
            frame = await stream.recv()
            payload: dict = json.loads(frame.data)
        except Exception as exc:
            self.logger.warning("Failed to read/parse server-pushed message: %s", exc)
            return

        event: str = payload.get("event", "")
        data: dict = payload.get("data", {})

        handlers: List[MessageHandler] = list(
            self._event_handlers.get(event, [])
        ) + list(self._fallback_handlers)

        for handler in handlers:
            try:
                await handler(event, data, self.page)
            except Exception as exc:
                self.logger.error(
                    "Handler for event '%s' raised an error: %s",
                    event,
                    exc,
                    exc_info=True,
                )
