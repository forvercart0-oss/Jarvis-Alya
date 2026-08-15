import threading
from typing import Callable, Optional


class WakeWordDetector:
    def __init__(self, settings):
        self.settings = settings
        self.enabled = getattr(settings, "wake_word_enabled", False)
        self.wake_word = getattr(settings, "wake_word", "Hey JARVIS")
        self.on_wake: Optional[Callable] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        if not self.enabled or self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def _listen_loop(self):
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                while self._running:
                    try:
                        audio = r.listen(source, timeout=3, phrase_time_limit=5)
                        text = r.recognize_google(audio).lower()
                        if self.wake_word.lower() in text:
                            if self.on_wake:
                                self.on_wake()
                    except Exception:
                        continue
        except Exception:
            pass
