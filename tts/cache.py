"""TTS cache for JARVIS Phase 3."""

from __future__ import annotations

import hashlib
import logging
import os
import tempfile

logger = logging.getLogger("jarvis.tts.cache")


class TTSCache:
    def __init__(self, cache_dir: str | None = None):
        self._cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "jarvis-tts-cache")
        os.makedirs(self._cache_dir, exist_ok=True)
        self._hits = 0
        self._misses = 0

    def _key(self, text: str, voice: str, speed: float, language: str) -> str:
        raw = f"{text}|{voice}|{speed}|{language}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, text: str, voice: str, speed: float, language: str) -> str | None:
        key = self._key(text, voice, speed, language)
        path = os.path.join(self._cache_dir, f"{key}.wav")
        if os.path.exists(path):
            self._hits += 1
            return path
        self._misses += 1
        return None

    def put(self, text: str, voice: str, speed: float, language: str, audio_data: bytes) -> str:
        key = self._key(text, voice, speed, language)
        path = os.path.join(self._cache_dir, f"{key}.wav")
        with open(path, "wb") as f:
            f.write(audio_data)
        return path

    @property
    def stats(self) -> dict[str, int]:
        return {"hits": self._hits, "misses": self._misses}
