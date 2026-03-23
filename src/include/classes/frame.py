import asyncio
import json
import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Optional, cast
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
    data: Any


class AsyncStream:
    """Asynchronous stream abstraction over a multiplexed WebSocket connection."""

    def __init__(self, connection: "AsyncMultiplexConnection", frame_id: int):
        self.connection = connection
        self.frame_id = frame_id
        self._queue: asyncio.Queue = asyncio.Queue()

    async def send(self, data: Any, frame_type: FrameType = FrameType.PROCESS):
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
        self._send_lock = asyncio.Lock()
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
                    raw_payload = await self._ws.recv()
                except Exception:
                    break

                if len(raw_payload) < HEADER_SIZE:
                    continue

                header = cast(bytes, raw_payload[:HEADER_SIZE])
                data = raw_payload[HEADER_SIZE:]
                frame_id, frame_type_val = struct.unpack(HEADER_FORMAT, header)

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

    async def _send_frame(self, frame_id: int, frame_type: FrameType, data: Any):
        header = struct.pack(HEADER_FORMAT, frame_id, frame_type.value)
        if isinstance(data, (dict, list)):
            data_bytes = json.dumps(data).encode("utf-8")
        elif isinstance(data, str):
            data_bytes = data.encode("utf-8")
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode("utf-8")

        payload = header + data_bytes

        async with self._send_lock:
            await self._ws.send(payload)

        if frame_type == FrameType.CONCLUSION:
            self._streams.pop(frame_id, None)

    async def close(self):
        self._is_running = False
        if hasattr(self._ws, "close"):
            await self._ws.close()
