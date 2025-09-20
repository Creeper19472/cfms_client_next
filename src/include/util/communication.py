import json, time, ssl
import flet as ft
from websockets.asyncio.client import connect, ClientConnection
from include.ui.util.notifications import send_error
import threading

# from include.function.lockdown import go_lockdown

communication_lock = threading.Lock()

async def build_request(
    conn: ClientConnection,
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

    await conn.send(request_json)
    response = await conn.recv()

    loaded_response: dict = json.loads(response)
    return loaded_response

# def _build_request(
#     conn: Any,
#     action: str,
#     data: dict = {},
#     message: str = "",
#     username=None,
#     token=None,
# ) -> dict:

#     request = {
#         "action": action,
#         "data": data,
#         "username": username,
#         "token": token,
#         "timestamp": time.time(),
#     }

#     request_json = json.dumps(request, ensure_ascii=False)
    
#     if not communication_lock.acquire(timeout=0):
#         ssl_context = ssl.create_default_context()
#         ssl_context.check_hostname = False
#         ssl_context.verify_mode = ssl.CERT_NONE

#         server_uri = page.session.get("server_uri")
#         assert server_uri

#         try:
#             websocket = connect(server_uri, ssl=ssl_context)
#         except:
#             raise

#     else:
#         websocket = page.session.get("websocket")
#         assert websocket
    
#     try:
#         websocket.send(request_json)
#         response = websocket.recv()
#     except:
#         # send_error(page, "连接中断，正在尝试重新连接。")
#         ssl_context = ssl.create_default_context()
#         ssl_context.check_hostname = False
#         ssl_context.verify_mode = ssl.CERT_NONE

#         server_uri = page.session.get("server_uri")
#         assert server_uri

#         websocket = connect(server_uri, ssl=ssl_context)
#         page.session.set("websocket", websocket)

#         # 重发
#         websocket.send(request_json)
#         response = websocket.recv()

#     try:
#         communication_lock.release()
#     except RuntimeError:
#         websocket.close()

#     loaded_response: dict = json.loads(response)
#     if loaded_response.get("code") == 999:
#         go_lockdown(page)

#     return loaded_response