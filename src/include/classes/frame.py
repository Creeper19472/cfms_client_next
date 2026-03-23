import asyncio
import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Optional, cast
from websockets.typing import Data
from websockets.asyncio.client import ClientConnection

HEADER_FORMAT = "!IB"  # 4 bytes for frame_id, 1 byte for frame_type
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


class FrameType(IntEnum):
    PROCESS = 0
    CONCLUSION = 1


@dataclass
class Frame:
    frame_id: int
    frame_type: FrameType
    data: bytes


class AsyncStream:
    """Asynchronous stream abstraction over a multiplexed WebSocket connection."""

    def __init__(self, connection: "AsyncMultiplexConnection", frame_id: int):
        self.connection = connection
        self.frame_id = frame_id
        self._queue: asyncio.Queue = asyncio.Queue()

    async def send(self, data: Data, frame_type: FrameType = FrameType.PROCESS):
        await self.connection._send_frame(self.frame_id, frame_type, data)

    async def recv(self) -> Frame:
        frame = await self._queue.get()
        if frame is None:
            raise ConnectionError("MultiplexConnection has been closed.")
        return frame

    def _put_incoming_frame(self, frame: Optional[Frame]):
        self._queue.put_nowait(frame)


class AsyncMultiplexConnection:
    def __init__(self, websocket: ClientConnection):
        self._ws = websocket
        self._next_frame_id = 1

        self._streams: dict[int, AsyncStream] = {}
        self._new_streams: asyncio.Queue[Optional[AsyncStream]] = asyncio.Queue()

        self._is_running = True

        self._dispatcher_task = asyncio.create_task(self._recv_loop())

    def create_stream(self) -> AsyncStream:
        frame_id = self._next_frame_id
        self._next_frame_id += 2

        new_stream = AsyncStream(self, frame_id)
        self._streams[frame_id] = new_stream
        return new_stream

    async def accept_stream(self) -> Optional[AsyncStream]:
        return await self._new_streams.get()

    async def _recv_loop(self):
        try:
            while self._is_running:
                try:
                    raw_payload = cast(bytes, await self._ws.recv())
                except Exception:
                    break

                if len(raw_payload) < HEADER_SIZE:
                    continue

                if isinstance(raw_payload, str):
                    raw_payload = raw_payload.encode("utf-8")

                frame_id, frame_type_val = struct.unpack_from(
                    HEADER_FORMAT, raw_payload
                )
                data = raw_payload[HEADER_SIZE:]

                try:
                    frame_type = FrameType(frame_type_val)
                except ValueError:
                    continue

                frame = Frame(frame_id=frame_id, frame_type=frame_type, data=data)

                if frame.frame_id not in self._streams:
                    new_stream = AsyncStream(self, frame.frame_id)
                    self._streams[frame.frame_id] = new_stream
                    self._new_streams.put_nowait(new_stream)

                target_stream = self._streams[frame.frame_id]
                target_stream._put_incoming_frame(frame)

                if frame.frame_type == FrameType.CONCLUSION:
                    self._streams.pop(frame.frame_id, None)

        finally:
            self._is_running = False
            self._new_streams.put_nowait(None)  # awake accept_stream

            for stream in list(self._streams.values()):
                stream._put_incoming_frame(None)
            self._streams.clear()

    async def _send_frame(self, frame_id: int, frame_type: FrameType, data: Data):
        if isinstance(data, str):
            data = data.encode("utf-8")

        data_len = len(data)
        payload = bytearray(HEADER_SIZE + data_len)

        struct.pack_into(HEADER_FORMAT, payload, 0, frame_id, frame_type.value)

        payload[HEADER_SIZE:] = data

        await self._ws.send(payload)

        if frame_type == FrameType.CONCLUSION:
            self._streams.pop(frame_id, None)

    async def close(self):
        # Signal the receive loop to stop
        self._is_running = False

        # Ensure the dispatcher task is cleaned up
        if self._dispatcher_task is not None and not self._dispatcher_task.done():
            self._dispatcher_task.cancel()
            try:
                await self._dispatcher_task
            except asyncio.CancelledError:
                pass

        # Close the underlying websocket connection
        if hasattr(self._ws, "close"):
            await self._ws.close()
