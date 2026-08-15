"""Voice subsystem facade: listener + recognizer + TTS + wake word.

The rest of the application interacts only with ``VoiceService`` (async
``listen()`` and ``speak()``), so STT/TTS engines can be swapped freely.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable

from config.settings import get_settings
from voice.listener import Listener, MicrophoneUnavailableError
from voice.recognizer import Recognizer, STTError
from voice.tts_manager import TTSManager
from voice.wakeword import WakeWordDetector

logger = logging.getLogger("jarvis.voice")


class VoiceService:
    """High-level voice input/output for JARVIS."""

    def __init__(self, settings: Any | None = None) -> None:
        self.settings = settings or get_settings()
        self.listener = Listener(self.settings)
        self.recognizer = Recognizer(self.settings)
        self.tts = TTSManager(self.settings)
        self.wakeword = WakeWordDetector(self.settings)
        self._initialized = False

    # --------------------------------------------------------------- setup
    def initialize(self) -> bool:
        """Probe microphone + TTS availability without starting anything."""
        self._initialized = self.settings.voice_enabled
        if not self._initialized:
            logger.info("Voice disabled by configuration.")
            return False
        mic_ok = self.listener.is_available()
        tts_ok = self.tts.is_available()
        logger.info(
            "Voice ready: mic=%s tts=%s (engine=%s, stt=%s, voice=%s)",
            mic_ok,
            tts_ok,
            self.tts.engine,
            self.recognizer.engine,
            self.tts.settings.tts_voice,
        )
        return mic_ok or tts_ok

    @property
    def mic_available(self) -> bool:
        return self.listener.is_available()

    @property
    def tts_available(self) -> bool:
        return self.tts.is_available()

    @property
    def tts_backend(self) -> str | None:
        return self.tts.backend

    # --------------------------------------------------------------- input
    async def listen(self, max_duration: float = 12.0) -> str | None:
        """Record + transcribe one utterance. Returns text or None."""
        if not self._initialized or not self.listener.is_available():
            return None
        try:
            audio = await asyncio.to_thread(self.listener.record, max_duration)
        except MicrophoneUnavailableError as exc:
            logger.warning("Microphone unavailable: %s", exc)
            return None
        if audio is None:
            return None
        try:
            return await asyncio.to_thread(self.recognizer.recognize, audio)
        except STTError as exc:
            logger.warning("STT failed: %s", exc)
            raise

    async def listen_with_events(self, on_event: Callable[[str], Awaitable[None]] | None) -> str | None:
        """Listen while emitting 'listening' / 'transcribing' events."""
        if on_event:
            await on_event("listening")
        text = await self.listen()
        if text and on_event:
            await on_event("transcribing")
        return text

    # -------------------------------------------------------------- output
    async def speak(self, text: str) -> bool:
        """Speak text through the TTS manager (async, non-blocking)."""
        if not self.settings.voice_enabled:
            return False
        if not text:
            return False
        return await self.tts.speak(text)

    async def speak_now(self, text: str) -> bool:
        """One-shot speak, used by the voice-test endpoint."""
        if not text:
            return False
        return await self.tts.speak_now(text)

    def list_voices(self) -> list[str]:
        return self.tts.list_voices()

    def voice_catalog(self) -> list[dict]:
        return self.tts.voice_catalog()

    def is_available(self) -> bool:
        return self.tts.is_available() or self.listener.is_available()

    # ----------------------------------------------------------- wake word
    def start_wakeword(self, on_wake: Callable[[], Any] | None = None) -> None:
        if on_wake:
            self.wakeword.on_wake = on_wake
        self.wakeword.start()

    def stop_wakeword(self) -> None:
        self.wakeword.stop()

    def shutdown(self) -> None:
        self.stop_wakeword()
        logger.info("Voice service shut down")
