"""TTS engine abstraction for JARVIS Phase 3."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger("jarvis.tts.engine")


class TTSEngine(ABC):
    @abstractmethod
    async def speak(self, text: str, voice: str, speed: float, volume: float, language: str) -> dict[str, Any]:
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        pass

    @abstractmethod
    async def set_voice(self, voice: str) -> None:
        pass

    @abstractmethod
    async def set_speed(self, speed: float) -> None:
        pass

    @abstractmethod
    async def set_volume(self, volume: float) -> None:
        pass


class KokoroTTSEngine(TTSEngine):
    def __init__(self):
        self._initialized = False
        self._voice = "default"
        self._speed = 1.0
        self._volume = 1.0

    async def initialize(self) -> bool:
        try:
            from kokoro_tts import KokoroTTS
            self._kokoro = KokoroTTS()
            self._initialized = True
            logger.info("Kokoro TTS engine initialized")
            return True
        except Exception as exc:
            logger.warning("Kokoro initialization failed: %s", exc)
            return False

    async def shutdown(self) -> None:
        self._initialized = False

    async def speak(self, text: str, voice: str, speed: float, volume: float, language: str) -> dict[str, Any]:
        if not self._initialized:
            return {"success": False, "error": "Engine not initialized"}
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._kokoro.speak, text, voice, speed
            )
            return {"success": True, "result": result}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def set_voice(self, voice: str) -> None:
        self._voice = voice

    async def set_speed(self, speed: float) -> None:
        self._speed = speed

    async def set_volume(self, volume: float) -> None:
        self._volume = volume


class EspeakTTSEngine(TTSEngine):
    def __init__(self):
        self._initialized = False
        self._voice = "default"
        self._speed = 1.0
        self._volume = 1.0

    async def initialize(self) -> bool:
        try:
            import subprocess
            proc = subprocess.run(["espeak-ng", "--version"], capture_output=True, text=True)
            self._initialized = proc.returncode == 0
            return self._initialized
        except Exception:
            return False

    async def shutdown(self) -> None:
        self._initialized = False

    async def speak(self, text: str, voice: str, speed: float, volume: float, language: str) -> dict[str, Any]:
        if not self._initialized:
            return {"success": False, "error": "Engine not initialized"}
        try:
            import subprocess
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                path = f.name
            proc = subprocess.run(
                ["espeak-ng", "-w", path, "-s", str(int(speed * 150)), text],
                capture_output=True, text=True, timeout=30
            )
            if proc.returncode != 0:
                return {"success": False, "error": proc.stderr}
            return {"success": True, "path": path}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def set_voice(self, voice: str) -> None:
        self._voice = voice

    async def set_speed(self, speed: float) -> None:
        self._speed = speed

    async def set_volume(self, volume: float) -> None:
        self._volume = volume


def create_engine(provider: str = "kokoro") -> TTSEngine:
    if provider == "espeak-ng":
        return EspeakTTSEngine()
    return KokoroTTSEngine()
