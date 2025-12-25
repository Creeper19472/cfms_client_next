"""File transfer utilities for uploading and downloading files to/from the server."""

import asyncio
import base64
import hashlib
import json
import mmap
import os
import shutil
from typing import Awaitable, Callable, Optional

import aiofiles.os
from Crypto.Cipher import AES
from flet import FilePickerFile
from websockets.asyncio.client import ClientConnection

from include.classes.config import AppShared
from include.classes.exceptions.request import InvalidResponseError
from include.classes.exceptions.transmission import (
    FileHashMismatchError,
    FileSizeMismatchError,
)
from include.constants import FLET_APP_STORAGE_TEMP
from include.ui.util.choice import normalize_always_choice
from include.util.connect import get_connection
from include.util.requests import do_request_2


async def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA256 hash of a file using memory-mapped I/O for efficiency.
    
    Uses memory-mapped files for faster hash calculation of large files.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal SHA256 hash string
    """
    with open(file_path, "rb") as f:
        # Use memory-mapped files to map directly to memory
        mmapped_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        return hashlib.sha256(mmapped_file).hexdigest()


async def upload_file_to_server(
    client: ClientConnection, task_id: str, file_path: str
):
    """
    Upload a file to the server over WebSocket connection.
    
    Yields progress updates as (current_bytes, total_bytes) tuples.
    
    Args:
        client: Active WebSocket connection
        task_id: Server task ID for this upload
        file_path: Local path to the file to upload
        
    Yields:
        Tuples of (bytes_uploaded, total_file_size) for progress tracking
        
    Raises:
        ValueError: If server response is invalid
        RuntimeError: If upload is rejected by server
    """

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

    received_response = str(await client.recv())
    if received_response.startswith("ready"):
        ready = True
    elif received_response == "stop":
        ready = False
    else:
        raise RuntimeError

    if ready:

        try:
            chunk_size = int(received_response.split()[1])
            async with aiofiles.open(file_path, "rb") as f:
                while True:
                    chunk = await f.read(chunk_size)
                    await client.send(chunk)

                    yield await f.tell(), file_size

                    if not chunk or len(chunk) < chunk_size:
                        break

            # need to wait for server confirmation
            server_response = json.loads(await client.recv())

        except Exception:
            raise


async def receive_file_from_server(
    client: ClientConnection,
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
        client (ClientConnection): The websocket client connection.
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

    sha256 = response["data"].get("sha256")  # SHA256 of original file
    file_size = response["data"].get("file_size")  # Size of original file
    chunk_size = response["data"].get("chunk_size", 8192)  # Chunk size
    total_chunks = response["data"].get("total_chunks")  # Total chunks

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

        try:
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

            # Get decryption information
            decrypted_data = await client.recv()
            decrypted_data_json: dict = json.loads(decrypted_data)

            aes_key = base64.b64decode(decrypted_data_json["data"].get("key"))

            # Decrypt chunks
            decrypted_chunks = 1
            cipher = AES.new(aes_key, AES.MODE_CFB, iv=iv)  # Initialize cipher

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

                    # remove the chunk file as we go
                    try:
                        await aiofiles.os.remove(chunk_file_path)
                    except Exception:
                        # best-effort cleanup; ignore removal errors here
                        pass

                    decrypted_chunks += 1

            # Delete temporary folder
            yield 2,

            await asyncio.get_event_loop().run_in_executor(
                None, shutil.rmtree, downloading_path
            )

        except GeneratorExit:
            # Clean up partial temp files and partial output file if generator closed early
            loop = asyncio.get_event_loop()

            def _safe_rmtree(path):
                try:
                    if os.path.exists(path):
                        shutil.rmtree(path)
                except Exception:
                    pass

            await loop.run_in_executor(None, _safe_rmtree, downloading_path)

            try:
                if await aiofiles.os.path.exists(file_path):
                    await aiofiles.os.remove(file_path)
            except Exception:
                pass

            raise

    except Exception:
        raise

    # Verify file

    async def _action_verify() -> None:

        if file_size != await aiofiles.os.path.getsize(file_path):
            raise FileSizeMismatchError(
                file_size, await aiofiles.os.path.getsize(file_path)
            )

        # Verify SHA256
        actual_sha256 = await calculate_sha256(file_path)
        if sha256 and actual_sha256 != sha256:
            raise FileHashMismatchError(sha256, actual_sha256)

    yield 3,

    try:
        await _action_verify()
    except Exception:
        await aiofiles.os.remove(file_path)
        raise


async def batch_upload_file_to_server(
    app_shared: AppShared,
    directory_id: Optional[str],
    files: list[FilePickerFile],
    max_size: int = 1024**2 * 4,
    max_retries: int = 3,
    on_conflict_callback: Optional[Callable[[str, str, str], Awaitable[Optional[str]]]] = None,
):
    """
    Upload multiple files to the server with progress tracking and retry logic.
    
    Processes files sequentially, creating a document for each file and uploading
    its contents. Yields progress information for each file. Handles file conflicts
    (409 responses) by calling the optional callback function.
    
    Args:
        app_shared: Application configuration containing auth and connection info
        directory_id: Target directory ID on server, or None for root
        files: List of files to upload
        max_size: Maximum WebSocket message size in bytes (default: 4MB)
        max_retries: Maximum retry attempts per file (default: 3)
        on_conflict_callback: Optional async callback function that receives
            (filename, conflict_type, conflict_id) and returns 'overwrite', 'skip',
            'always_overwrite', 'always_skip', or None. If None, 409 errors are 
            treated as regular errors.
        
    Yields:
        Tuples of (file_index, filename, bytes_uploaded, total_size, exception)
        where exception is None on success or an Exception object on error
        
    Raises:
        AssertionError: If file path is None
    """
    transfer_conn = None
    always_choice = None  # Track "always" choice for batch operations
    try:
        for index, file in enumerate(files):  # process tasks sequentially
            filename, file_path = file.name, file.path
            assert file_path is not None

            for retry in range(max_retries):
                try:
                    # check whether transfer_conn exists
                    if not transfer_conn:
                        transfer_conn = await get_connection(
                            server_address=app_shared.get_not_none_attribute("server_address"),
                            disable_ssl_enforcement=app_shared.disable_ssl_enforcement,
                            proxy=app_shared.preferences["settings"]["proxy_settings"],
                            max_size=max_size,
                        )

                    # create a new task on the server
                    response = await do_request_2(
                        action="create_document",
                        data={
                            "title": filename,
                            "folder_id": directory_id,
                            "access_rules": {},
                        },
                        username=app_shared.username,
                        token=app_shared.token,
                    )

                    if response.code == 409:
                        # Handle conflict (file already exists)
                        conflict_type = response.data.get("type")
                        conflict_id = response.data.get("id")
                        
                        # Check if we can handle this conflict
                        # conflict_id must be a non-empty string for overwrite to work
                        if (conflict_type == "document" and conflict_id and on_conflict_callback):
                            # Use always choice if set, otherwise ask user
                            if always_choice in ('always_overwrite', 'always_skip'):
                                user_choice = normalize_always_choice(always_choice)
                            else:
                                # Ask user what to do
                                user_choice = await on_conflict_callback(
                                    filename, conflict_type, conflict_id
                                )
                                
                                # Store "always" choices for subsequent files
                                if user_choice in ('always_overwrite', 'always_skip'):
                                    always_choice = user_choice
                                    user_choice = normalize_always_choice(user_choice)
                            
                            if user_choice == 'overwrite':
                                # Upload as a new version of the existing document
                                upload_response = await do_request_2(
                                    action="upload_document",
                                    data={
                                        "document_id": conflict_id,
                                    },
                                    username=app_shared.username,
                                    token=app_shared.token,
                                )
                                
                                if upload_response.code != 200:
                                    raise InvalidResponseError(
                                        upload_response,
                                        f"Failed to upload document '{filename}': {upload_response.message}",
                                    )
                                
                                # Get task_id with defensive checks
                                task_id = upload_response.data.get("task_data", {}).get("task_id")
                                if not task_id:
                                    raise InvalidResponseError(
                                        upload_response,
                                        f"Server response missing task_id for '{filename}'",
                                    )
                                
                                async for current_size, total_size in upload_file_to_server(
                                    transfer_conn, task_id, file_path
                                ):
                                    yield index, filename, current_size, total_size, None
                                
                                break  # break the retry loop if successful
                            
                            elif user_choice == 'skip':
                                # Skip this file, but still yield a progress update so callers
                                # can account for this file in their progress tracking.
                                # Use -1, -1 to distinguish from empty files (0, 0)
                                yield index, filename, -1, -1, None
                                break
                            
                            else:
                                # User cancelled, stop all uploads
                                raise InvalidResponseError(
                                    response,
                                    f"Upload cancelled by user",
                                )
                        else:
                            # Can't handle this conflict (no ID, wrong type, or no callback)
                            raise InvalidResponseError(
                                response,
                                f"Failed to create document '{filename}': {response.message}",
                            )
                    
                    elif response.code != 200:
                        raise InvalidResponseError(
                            response,
                            f"Failed to create document '{filename}': {response.message}",
                        )
                    
                    else:
                        # Success - normal flow
                        task_id = response.data.get("task_data", {}).get("task_id")
                        if not task_id:
                            raise InvalidResponseError(
                                response,
                                f"Server response missing task_id for '{filename}'",
                            )

                        async for current_size, total_size in upload_file_to_server(
                            transfer_conn, task_id, file_path
                        ):
                            yield index, filename, current_size, total_size, None

                        break  # break the retry loop if successful

                except InvalidResponseError as exc:
                    yield index, filename, -1, -1, exc
                    break

                except Exception as exc:
                    if transfer_conn:
                        await transfer_conn.close()
                        transfer_conn = None

                    if retry == max_retries - 1:
                        raise

                    continue

    finally:
        if transfer_conn:
            await transfer_conn.close()
            transfer_conn = None