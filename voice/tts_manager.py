import asyncio
import logging
import re
from typing import Awaitable, Callable, Optional

from voice.tts import TTS as EspeakTTS
from voice.kokoro_tts import KokoroTTS
from config.settings import get_settings

logger = logging.getLogger("jarvis.tts")

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")


def split_sentences(text: str) -> list[str]:
    """Split text into speakable sentence chunks."""
    parts = [p.strip() for p in _SENTENCE_RE.split(text) if p.strip()]
    return parts or ([text.strip()] if text.strip() else [])


class TTSManager:
    """Async TTS manager with a speaking queue.

    Chunks are enqueued and spoken in order on a worker thread, so the event
    loop is never blocked and sentences can be spoken while the LLM is still
    generating the rest of the response (low-latency voice pipeline).
    """

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.engine = self.settings.tts_engine
        self._espeak = EspeakTTS(self.settings)
        self._kokoro = KokoroTTS(self.settings)
        self._active = self._resolve_engine()
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker: Optional[asyncio.Task] = None
        self._speaking = False
        self._callbacks: list[Callable[[str], Awaitable[None]]] = []
        self._first_audio_callbacks: list[Callable[[], Awaitable[None]]] = []
        if self._kokoro.is_available():
            self._kokoro.on_first_audio(self._on_first_audio)

    def _on_first_audio(self):
        if self._first_audio_callbacks:
            for cb in list(self._first_audio_callbacks):
                try:
                    asyncio.get_running_loop().create_task(cb())
                except RuntimeError:
                    pass

    def _resolve_engine(self):
        if self.engine == "kokoro" and self._kokoro.is_available():
            return self._kokoro
        if self.engine == "espeak-ng" and self._espeak.is_available():
            return self._espeak
        if self._kokoro.is_available():
            return self._kokoro
        if self._espeak.is_available():
            return self._espeak
        return None

    def is_available(self) -> bool:
        return self._active is not None

    @property
    def backend(self) -> Optional[str]:
        if self._active is None:
            return None
        return getattr(self._active, "backend", self.engine)

    def list_voices(self) -> list[str]:
        if self._active is not None and hasattr(self._active, "list_voices"):
            try:
                return self._active.list_voices()
            except Exception:
                pass
        return ["default"]

    def voice_catalog(self) -> list[dict]:
        """Structured voices for the premium UI picker, with engine metadata."""
        if self._active is not None and hasattr(self._active, "voice_catalog"):
            try:
                return self._active.voice_catalog()
            except Exception:
                pass
        try:
            return [{"id": v, "label": v, "group": "Other", "gender": "unknown", "engine": self.engine} for v in self.list_voices()]
        except Exception:
            return []

    def reconfigure(self):
        self.engine = self.settings.tts_engine
        self._espeak = EspeakTTS(self.settings)
        self._kokoro = KokoroTTS(self.settings)
        self._active = self._resolve_engine()
        if self._kokoro.is_available():
            self._kokoro.on_first_audio(self._on_first_audio)

    async def start(self):
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._run())

    async def stop(self):
        if self._worker:
            self._worker.cancel()
            try:
                await self._worker
            except (asyncio.CancelledError, Exception):
                pass
            self._worker = None
        try:
            self._kokoro.shutdown()
        except Exception:
            pass

    async def _run(self):
        while True:
            text = await self._queue.get()
            if text == "__STOP__":
                self._speaking = False
                continue
            self._speaking = True
            await self._emit("tts_start", text)
            try:
                await self._active.speak(text)
            except Exception as exc:
                logger.warning("TTS speak failed: %s", exc)
            self._speaking = False
            await self._emit("tts_end", text)

    async def _emit(self, event: str, text: str):
        for cb in list(self._callbacks):
            try:
                await cb(event, text)
            except Exception:
                pass

    def on_event(self, callback: Callable[[str, str], Awaitable[None]]):
        self._callbacks.append(callback)

    def on_first_audio(self, callback: Callable[[], Awaitable[None]]):
        self._first_audio_callbacks.append(callback)

    def is_speaking(self) -> bool:
        return self._speaking

    async def speak(self, text: str) -> bool:
        """Queue a full utterance for speaking (async, non-blocking)."""
        if not text.strip():
            return False
        if not self.settings.tts_enabled:
            return False
        if not self._active:
            return False
        await self.start()
        self._queue.put_nowait(text)
        return True

    async def speak_chunks(self, text: str) -> bool:
        """Split text into sentences and queue each one."""
        chunks = split_sentences(text)
        for chunk in chunks:
            await self.speak(chunk)
        return bool(chunks)

    async def speak_now(self, text: str) -> bool:
        """Synchronous-style one-shot speak (used by test-voice button)."""
        if not self.settings.tts_enabled or not self._active:
            return False
        return await self._active.speak(text)

    def clear(self):
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    def set_engine(self, engine: str):
        self.engine = engine
        self._active = self._resolve_engine()

    def set_voice(self, voice: str):
        self.settings.tts_voice = voice
        if self._kokoro.is_available():
            self._kokoro.set_voice(voice)
        if self._espeak.is_available():
            self._espeak.set_voice(voice)

    def set_speed(self, speed: int):
        self.settings.tts_speed = int(speed)
        if self._kokoro.is_available():
            self._kokoro.set_speed(speed)
        if self._espeak.is_available():
            self._espeak.set_speed(speed)

    def set_volume(self, volume: int):
        self.settings.tts_volume = int(volume)
        if self._kokoro.is_available():
            self._kokoro.set_volume(volume)
        if self._espeak.is_available():
            self._espeak.set_volume(volume)
