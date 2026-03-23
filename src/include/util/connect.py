"""Utilities for establishing WebSocket connections to the server."""

import socket
import ssl
from typing import Literal

from websockets.asyncio.client import connect

from include.classes.shared import AppShared
from include.constants import ROOT_PATH
from include.classes.frame import AsyncMultiplexConnection, FrameType


async def get_connection(
    server_address: str,
    disable_ssl_enforcement: bool = False,
    max_size: int = 2**20,
    proxy: str | Literal[True] | None = True,
    force_ipv4: bool = False,
) -> AsyncMultiplexConnection:
    """
    Establish a WebSocket connection to the server.

    Creates a secure WebSocket connection with configurable SSL settings
    and proxy support.

    Args:
        server_address: WebSocket server address (e.g., "wss://example.com")
        disable_ssl_enforcement: If True, disable SSL certificate verification
        max_size: Maximum message size in bytes (default: 1MB)
        proxy: Proxy configuration - True for system proxy, string for custom proxy,
               None to disable proxy
        force_ipv4: If True, force the use of IPv4 addresses only

    Returns:
        Established WebSocket client connection

    Raises:
        Various connection errors from websockets library
    """
    ssl_context = ssl.create_default_context()

    if not disable_ssl_enforcement:
        # Use integrated CA certificate for verification
        ssl_context.load_verify_locations(capath=f"{ROOT_PATH}/include/ca/")
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
    else:
        # Disable SSL verification (not recommended for production)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    cert_path = AppShared().preferences["settings"].get("client_cert_path")
    key_path = AppShared().preferences["settings"].get("client_key_path")

    if cert_path and key_path:
        ssl_context.load_cert_chain(certfile=cert_path, keyfile=key_path)

    # Set address family if IPv4 is forced
    family = socket.AF_INET if force_ipv4 else socket.AF_UNSPEC

    return AsyncMultiplexConnection(
        await connect(
            server_address,
            ssl=ssl_context,
            max_size=max_size,
            proxy=proxy,
            family=family,
        )
    )
