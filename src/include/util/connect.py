import ssl
from websockets.asyncio.client import connect
from include.constants import INTEGRATED_CA_CERT


async def get_connection(server_address, disable_ssl_enforcement: bool = False):
    ssl_context = ssl.create_default_context()
    if not disable_ssl_enforcement:
        ssl_context.load_verify_locations(cadata=INTEGRATED_CA_CERT)
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
    else:
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    return await connect(server_address, ssl=ssl_context)
