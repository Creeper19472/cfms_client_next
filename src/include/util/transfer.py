import flet as ft
import websockets, json, os, mmap, hashlib
from include.util.connect import get_connection


async def calculate_sha256(file_path):
    # 使用更快的 hashlib 工具和内存映射文件
    with open(file_path, "rb") as f:
        # 使用内存映射文件直接映射到内存
        mmapped_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        return hashlib.sha256(mmapped_file).hexdigest()
    

async def upload_file_to_server(
    client: websockets.ClientConnection, task_id: str, file_path: str, refresh=True
):

    # upload_lock: threading.Lock = page.session.get("upload_lock")
    # if not upload_lock.acquire(timeout=0):
    #     send_error(page, "不能同时执行多个上传任务")
    #     return

    # try:
    #     client = await get_connection(page.session.get("server_uri"))
    # except (TimeoutError, websockets.exceptions.ConnectionClosedError):
    #     raise

    await client.send(
        json.dumps(
            {
                "action": "upload_file",
                "data": {"task_id": task_id},
            },
            ensure_ascii=False,
        )
    )

    # Receive file metadata from the server
    response = json.loads(await client.recv())
    if response["action"] != "transfer_file":
        # page.logger.error("Invalid action received for file transfer.")
        return

    file_size = os.path.getsize(file_path)

    # if not file_size:
    #     upload_lock.release()
    #     raise ValueError("不能上传空文件")

    sha256 = await calculate_sha256(file_path) if file_size else None

    task_info = {
        "action": "transfer_file",
        "data": {
            "sha256": sha256,
            "file_size": file_size,
        },
    }
    await client.send(json.dumps(task_info, ensure_ascii=False))

    received_response = await client.recv()
    if received_response not in ["ready", "stop"]:
        # upload_lock.release()
        # page.logger.error(
        #     f"Server did not acknowledge readiness for file transfer: {received_response}"
        # )
        raise RuntimeError

    if received_response == "ready":
        # page.logger.info("File transmission begin.")

        try:
            chunk_size = 8192
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    await client.send(chunk)
                    
                    yield f.tell(), file_size

                    if not chunk or len(chunk) < chunk_size:
                        break
        except:
            raise    

    # await client.close()

