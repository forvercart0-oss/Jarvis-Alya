import asyncio
import os
import shutil
import subprocess
import tempfile
from typing import Optional


class TTS:
    """espeak-ng TTS engine. Non-blocking via a worker thread."""

    def __init__(self, settings):
        self.voice = getattr(settings, "tts_voice", "en+f3")
        self.speed = getattr(settings, "tts_speed", 160)
        self.volume = getattr(settings, "tts_volume", 80)
        self._volume = max(0, min(100, self.volume))

    @staticmethod
    def is_available() -> bool:
        return shutil.which("espeak-ng") is not None

    @staticmethod
    def playback_binary() -> Optional[str]:
        for binary in ("pw-play", "paplay", "aplay"):
            if shutil.which(binary):
                return binary
        return None

    def list_voices(self) -> list[str]:
        try:
            out = subprocess.run(["espeak-ng", "--voices"], capture_output=True, text=True).stdout
            voices = []
            for line in out.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 2:
                    voices.append(parts[1])
            return voices or ["en+f3", "en-us", "en-gb"]
        except Exception:
            return ["en+f3", "en-us", "en-gb"]

    def _speak_blocking(self, text: str) -> bool:
        if not text.strip():
            return False
        if not self.is_available():
            return False
        player = self.playback_binary()
        if not player:
            return False
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wav_path = tmp.name
            cmd = [
                "espeak-ng",
                "-w", wav_path,
                "-v", self.voice,
                "-s", str(self.speed),
                text,
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            vol = max(0.0, min(1.0, self._volume / 100.0))
            play_cmd = [player, "--volume", f"{vol:.2f}", wav_path] if player == "pw-play" else [player, wav_path]
            subprocess.run(play_cmd, capture_output=True, check=True)
            try:
                os.unlink(wav_path)
            except OSError:
                pass
            return True
        except Exception:
            return False

    async def speak(self, text: str) -> bool:
        if not text.strip():
            return False
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._speak_blocking, text)

    def set_voice(self, voice: str):
        self.voice = voice

    def set_speed(self, speed: int):
        self.speed = max(50, min(500, int(speed)))

    def set_volume(self, volume: int):
        self._volume = max(0, min(100, int(volume)))
        self.volume = self._volume
