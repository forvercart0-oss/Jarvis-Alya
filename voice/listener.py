import asyncio
import subprocess
import sys
import speech_recognition as sr
from typing import Optional


class MicrophoneUnavailableError(Exception):
    pass


_PROBE_SCRIPT = """
import speech_recognition as sr
with sr.Microphone() as source:
    pass
"""


def probe_microphone() -> bool:
    """Test microphone availability in a subprocess.

    PortAudio/PyAudio can abort the process with a native assertion on
    machines with a broken audio stack. Running the probe in a subprocess
    keeps such a crash contained so it never takes down the backend.
    """
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _PROBE_SCRIPT],
            capture_output=True,
            timeout=15,
        )
        return proc.returncode == 0
    except Exception:
        return False


class Listener:
    def __init__(self, settings):
        self.settings = settings
        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold = 4000
        self._recognizer.pause_threshold = 0.8
        self._recognizer.phrase_threshold = 0.3
        self._recognizer.non_speaking_duration = 0.5

    def is_available(self) -> bool:
        return probe_microphone()

    def record(self, max_duration: float = 12.0) -> Optional[sr.AudioData]:
        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self._recognizer.listen(source, timeout=max_duration, phrase_time_limit=max_duration)
                return audio
        except sr.WaitTimeoutError:
            return None
        except Exception:
            raise MicrophoneUnavailableError("Microphone not available.")
