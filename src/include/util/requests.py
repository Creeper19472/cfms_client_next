import json, time, ssl
import flet as ft
from include.classes.client import LockableClientConnection
from include.ui.util.notifications import send_error
import threading, asyncio

# from include.function.lockdown import go_lockdown

async def do_request(
    conn: LockableClientConnection,
    action: str,
    data: dict = {},
    message: str = "",
    username=None,
    token=None,
) -> dict:

    request = {
        "action": action,
        "data": data,
        "username": username,
        "token": token,
        "timestamp": time.time(),
    }

    request_json = json.dumps(request, ensure_ascii=False)

    async with conn.lock:
        await conn.send(request_json)
        response = await conn.recv()

    loaded_response: dict = json.loads(response)
    return loaded_response