import asyncio
import json
from typing import Any, Dict, Set

from starlette.websockets import WebSocket


class NotificationManager:
    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        payload = json.dumps(message, default=str)
        async with self._lock:
            conns = list(self._connections)

        if not conns:
            return

        to_remove: Set[WebSocket] = set()
        for ws in conns:
            try:
                await ws.send_text(payload)
            except Exception:
                to_remove.add(ws)

        if to_remove:
            async with self._lock:
                for ws in to_remove:
                    self._connections.discard(ws)


notifications = NotificationManager()

import asyncio
import json
from typing import Any, Dict, Set

from starlette.websockets import WebSocket


class NotificationManager:
    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        payload = json.dumps(message, default=str)
        async with self._lock:
            conns = list(self._connections)
        if not conns:
            return

        to_remove: Set[WebSocket] = set()
        for ws in conns:
            try:
                await ws.send_text(payload)
            except Exception:
                to_remove.add(ws)

        if to_remove:
            async with self._lock:
                for ws in to_remove:
                    self._connections.discard(ws)


notifications = NotificationManager()

