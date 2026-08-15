import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("jarvis.ws")


class WSManager:
    def __init__(self):
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)
        logger.info("WebSocket connected (%d active)", len(self._connections))

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._connections.discard(ws)
        logger.info("WebSocket disconnected (%d active)", len(self._connections))

    async def send(self, ws: WebSocket, event: str, data: Any = None):
        try:
            await ws.send_json({"event": event, "data": data or {}})
        except Exception:
            await self.disconnect(ws)

    async def broadcast(self, event: str, data: Any = None):
        payload = {"event": event, "data": data or {}}
        async with self._lock:
            targets = list(self._connections)
        for ws in targets:
            try:
                await ws.send_json(payload)
            except Exception:
                await self.disconnect(ws)

    @property
    def count(self) -> int:
        return len(self._connections)


ws_manager = WSManager()
