from typing import Any
from include.classes.client import LockableClientConnection
from include.classes.exceptions.request import (
    CreateDirectoryFailureError,
)
from include.util.requests import do_request


async def create_directory(
    conn: LockableClientConnection,
    parent_id: str | None,
    name: str,
    username: str | Any,
    token: str | Any,
    exists_ok: bool = False,
) -> str:
    mkdir_resp = await do_request(
        conn,
        "create_directory",
        data={
            "parent_id": parent_id,
            "name": name,
            "exists_ok": exists_ok,
        },
        username=username,
        token=token,
    )

    if mkdir_resp.get("code") != 200:
        raise CreateDirectoryFailureError(
            name, mkdir_resp.get("message", "Unknown error")
        )
    
    return mkdir_resp["data"]["id"]
