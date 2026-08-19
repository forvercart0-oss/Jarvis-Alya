"""TTS queue for JARVIS Phase 3."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger("jarvis.tts.queue")


@dataclass
class TTSItem:
    text: str
    voice: str = "default"
    speed: float = 1.0
    volume: float = 1.0
    language: str = "en"
    priority: int = 0
    timestamp: float = field(default_factory=time.time)


class TTSQueue:
    def __init__(self):
        self._queue: asyncio.Queue[TTSItem] = asyncio.Queue()
        self._processing = False
        self._interrupt = False

    async def put(self, item: TTSItem) -> None:
        await self._queue.put(item)

    async def get(self) -> TTSItem:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()

    def clear(self) -> None:
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except Exception:
                break

    def interrupt(self) -> None:
        self._interrupt = True

    def reset_interrupt(self) -> None:
        self._interrupt = False

    @property
    def size(self) -> int:
        return self._queue.qsize()

    @property
    def should_interrupt(self) -> bool:
        return self._interrupt
