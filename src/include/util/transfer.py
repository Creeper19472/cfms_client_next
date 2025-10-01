import asyncio
import base64
import flet as ft
import websockets, json, mmap, hashlib, os
import aiofiles.os
from include.classes.exceptions.transmission import (
    FileHashMismatchError,
    FileSizeMismatchError,
)
from include.constants import FLET_APP_STORAGE_TEMP
from include.classes.client import LockableClientConnection
from include.util.connect import get_connection
from Crypto.Cipher import AES
import shutil


async def calculate_sha256(file_path):
    # 使用更快的 hashlib 工具和内存映射文件
    with open(file_path, "rb") as f:
        # 使用内存映射文件直接映射到内存
        mmapped_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        return hashlib.sha256(mmapped_file).hexdigest()


async def upload_file_to_server(
    client: LockableClientConnection, task_id: str, file_path: str
):

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
        raise ValueError

    file_size = os.path.getsize(file_path)
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
        raise RuntimeError

    if received_response == "ready":

        try:
            chunk_size = 8192
            async with aiofiles.open(file_path, "rb") as f:
                while True:
                    chunk = await f.read(chunk_size)
                    await client.send(chunk)

                    yield await f.tell(), file_size

                    if not chunk or len(chunk) < chunk_size:
                        break
        except:
            raise


async def receive_file_from_server(
    client: LockableClientConnection,
    task_id: str,
    file_path: str,  # filename: str | None = None
):
    """
    Receives a file from the server over a websocket connection using AES encryption.

    Steps:
        1. Requests file metadata (SHA-256 hash, file size, chunk info) from the server.
        2. Sends readiness acknowledgment to the server.
        3. Receives encrypted file chunks, saves them temporarily.
        4. Receives AES key and IV, decrypts all chunks, and writes the output file.
        5. Deletes temporary chunk files.
        6. Verifies the file size and SHA-256 hash.
        7. Removes the output file if verification fails.

    Args:
        client (LockableClientConnection): The websocket client connection.
        task_id (str): The identifier for the file transfer task.
        file_path (str): The path to save the received file.

    Yields:
        Tuple[int, ...]: Progress updates at various stages.

    Raises:
        ValueError: If the server response is invalid.
        FileSizeMismatchError: If the received file size does not match the expected size.
        FileHashMismatchError: If the received file hash does not match the expected hash.
        Exception: For other errors during transfer or decryption.
    """

    # Send the request for file metadata
    await client.send(
        json.dumps(
            {
                "action": "download_file",
                "data": {"task_id": task_id},
            },
            ensure_ascii=False,
        )
    )

    # Receive file metadata from the server
    response = json.loads(await client.recv())
    if response["action"] != "transfer_file":
        raise ValueError("Invalid action received for file transfer")

    sha256 = response["data"].get("sha256")  # 原始文件的 SHA256
    file_size = response["data"].get("file_size")  # 原始文件的大小
    chunk_size = response["data"].get("chunk_size", 8192)  # 分片大小
    total_chunks = response["data"].get("total_chunks")  # 分片总数

    await client.send("ready")

    downloading_path = FLET_APP_STORAGE_TEMP + "/downloading/" + task_id
    await aiofiles.os.makedirs(downloading_path, exist_ok=True)

    if not file_size:
        async with aiofiles.open(file_path, "wb") as f:
            await f.truncate(0)
        return

    try:

        received_chunks = 0
        iv: bytes = b""

        while received_chunks + 1 <= total_chunks:
            # Receive encrypted data from the server

            data = await client.recv()
            if not data:
                raise ValueError("Received empty data from server")

            data_json: dict = json.loads(data)

            index = data_json["data"].get("index")
            if index == 0:
                iv = base64.b64decode(data_json["data"].get("iv"))
            chunk_hash = data_json["data"].get("hash")  # provided but unused
            chunk_data = base64.b64decode(data_json["data"].get("chunk"))
            chunk_file_path = os.path.join(downloading_path, str(index))

            async with aiofiles.open(chunk_file_path, "wb") as chunk_file:
                await chunk_file.write(chunk_data)

            received_chunks += 1

            if received_chunks < total_chunks:
                received_file_size = chunk_size * received_chunks
            else:
                received_file_size = file_size

            yield 0, received_file_size, file_size

        # 获得解密信息
        decrypted_data = await client.recv()
        decrypted_data_json: dict = json.loads(decrypted_data)

        aes_key = base64.b64decode(decrypted_data_json["data"].get("key"))

        # 解密分块
        decrypted_chunks = 1
        cipher = AES.new(aes_key, AES.MODE_CFB, iv=iv)  # 初始化 cipher

        async with aiofiles.open(file_path, "wb") as out_file:
            while decrypted_chunks <= total_chunks:
                yield 1, decrypted_chunks, total_chunks

                chunk_file_path = os.path.join(
                    downloading_path, str(decrypted_chunks - 1)
                )

                async with aiofiles.open(chunk_file_path, "rb") as chunk_file:
                    encrypted_chunk = await chunk_file.read()
                    decrypted_chunk = cipher.decrypt(encrypted_chunk)
                    await out_file.write(decrypted_chunk)

                # os.remove(chunk_file_path)
                decrypted_chunks += 1

        # 删除临时文件夹
        yield 2,

        await asyncio.get_event_loop().run_in_executor(
            None, shutil.rmtree, downloading_path
        )

    except:
        raise

    # 校验文件

    async def _action_verify() -> None:

        if file_size != await aiofiles.os.path.getsize(file_path):
            raise FileSizeMismatchError(
                file_size, await aiofiles.os.path.getsize(file_path)
            )

        # 校验 SHA256
        actual_sha256 = await calculate_sha256(file_path)
        if sha256 and actual_sha256 != sha256:
            raise FileHashMismatchError(sha256, actual_sha256)

    yield 3,

    try:
        await _action_verify()
    except:
        await aiofiles.os.remove(file_path)
        raise
