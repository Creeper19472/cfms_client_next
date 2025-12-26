"""Utilities for making requests to the server over WebSocket."""

import asyncio
import json
import time
import weakref
from typing import Any, Optional

from websockets import ConnectionClosed
from websockets.asyncio.client import ClientConnection

from include.classes.config import AppShared
from include.classes.response import Response
from include.util.connect import get_connection


# Store locks per-connection without attaching them to the connection object
_conn_locks = weakref.WeakKeyDictionary()


async def do_request(
    action: str,
    data: dict[str, Any] = {},
    message: str = "",
    username: Optional[str] = None,
    token: Optional[str] = None,
    max_retries: int = 3,
) -> dict[str, Any]:
    """
    Execute a request to the server with automatic retry on connection failure.

    Sends a request through the active WebSocket connection. If the connection
    is lost, automatically reconnects and retries the request.

    Args:
        action: Action/command name to execute on server
        data: Optional data payload for the request
        message: Optional message string
        username: Username for authentication (uses app config if not provided)
        token: Auth token (uses app config if not provided)
        max_retries: Maximum number of retry attempts (must be >= 1)

    Returns:
        Dictionary response from the server

    Raises:
        AssertionError: If max_retries < 1
        ConnectionError: If all retry attempts fail
    """

    _app_shared = AppShared()
    _conn = _app_shared.get_not_none_attribute("conn")

    assert max_retries >= 1, "max_retries must be at least 1"

    response: dict[str, Any] = {}
    for attempt in range(max_retries):
        try:
            response = await _request(
                _conn,
                action,
                data,
                message,
                username=username,
                token=token,
            )
        except (ConnectionClosed, ConnectionAbortedError, ConnectionResetError):
            if attempt >= max_retries - 1:
                raise
            # Reconnect and retry
            _conn = await get_connection(
                server_address=_app_shared.get_not_none_attribute("server_address"),
                disable_ssl_enforcement=_app_shared.disable_ssl_enforcement,
                proxy=_app_shared.preferences["settings"]["proxy_settings"],
                force_ipv4=_app_shared.preferences["settings"].get("force_ipv4", False),
            )
            _app_shared.conn = _conn
            continue

        break

    return response


async def do_request_2(
    action: str,
    data: dict[str, Any] = {},
    message: str = "",
    username: Optional[str] = None,
    token: Optional[str] = None,
    max_retries: int = 3,
) -> Response:
    """
    Execute a request to the server and return a Response object.

    This is a convenience wrapper around do_request that returns a typed
    Response object instead of a raw dictionary.

    Args:
        action: Action/command name to execute on server
        data: Optional data payload for the request
        message: Optional message string
        username: Username for authentication
        token: Auth token
        max_retries: Maximum number of retry attempts

    Returns:
        Response object containing code, message, data, and timestamp
    """
    response = await do_request(
        action,
        data,
        message,
        username=username,
        token=token,
        max_retries=max_retries,
    )

    return Response(
        code=response["code"],
        message=response.get("message", ""),
        data=response.get("data", {}),
        timestamp=response.get("timestamp", 0.0),
    )


def _get_conn_lock(conn: ClientConnection) -> asyncio.Lock:
    """
    Get or create a lock for a specific connection.

    Uses weak references to avoid keeping connections alive.

    Args:
        conn: WebSocket connection

    Returns:
        Lock associated with the connection
    """
    lock = _conn_locks.get(conn)
    if lock is None:
        lock = asyncio.Lock()
        _conn_locks[conn] = lock
    return lock


async def _request(
    conn: ClientConnection,
    action: str,
    data: dict[str, Any] = {},
    message: str = "",
    username: Optional[str] = None,
    token: Optional[str] = None,
) -> dict[str, Any]:
    """
    Internal function to send a request and receive response.

    Serializes the request to JSON, sends it through the connection,
    and waits for the response. Uses a lock to ensure thread-safety.

    Args:
        conn: Active WebSocket connection
        action: Action name
        data: Request data
        message: Optional message
        username: Username for auth
        token: Auth token

    Returns:
        Dictionary response from server
    """
    request = {
        "action": action,
        "data": data,
        "username": username,
        "token": token,
        "timestamp": time.time(),
    }

    request_json = json.dumps(request, ensure_ascii=False)

    lock = _get_conn_lock(conn)
    async with lock:
        await conn.send(request_json)
        response = await conn.recv()

    loaded_response: dict[str, Any] = json.loads(response)
    return loaded_response
