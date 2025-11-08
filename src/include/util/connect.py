"""Utilities for establishing WebSocket connections to the server."""

import ssl
from typing import Literal

from websockets.asyncio.client import ClientConnection, connect

from include.constants import INTEGRATED_CA_CERT


async def get_connection(
    server_address: str,
    disable_ssl_enforcement: bool = False,
    max_size: int = 2**20,
    proxy: str | Literal[True] | None = True,
) -> ClientConnection:
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
        
    Returns:
        Established WebSocket client connection
        
    Raises:
        Various connection errors from websockets library
    """
    ssl_context = ssl.create_default_context()
    
    if not disable_ssl_enforcement:
        # Use integrated CA certificate for verification
        ssl_context.load_verify_locations(cadata=INTEGRATED_CA_CERT)
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
    else:
        # Disable SSL verification (not recommended for production)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    return await connect(
        server_address, ssl=ssl_context, max_size=max_size, proxy=proxy
    )
