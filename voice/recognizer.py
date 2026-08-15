import speech_recognition as sr
from typing import Optional


class STTError(Exception):
    pass


class Recognizer:
    def __init__(self, settings):
        self.engine = getattr(settings, "stt_engine", "google")
        self.language = getattr(settings, "voice_language", "en-US")
        self.vosk_model_path = getattr(settings, "vosk_model_path", "")
        self.data_dir = getattr(settings, "data_dir", "data")
        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold = 4000
        self._recognizer.pause_threshold = 0.8
        self._recognizer.phrase_threshold = 0.3
        self._recognizer.non_speaking_duration = 0.5

    def recognize(self, audio: sr.AudioData) -> Optional[str]:
        if self.engine == "google":
            try:
                return self._recognizer.recognize_google(audio, language=self.language)
            except sr.UnknownValueError:
                return None
            except sr.RequestError as exc:
                raise STTError(f"Speech recognition service unreachable: {exc}") from exc
        if self.engine == "vosk":
            if not self.vosk_model_path:
                raise STTError("Vosk engine selected but no model path configured.")
            try:
                from vosk import Model, KaldiRecognizer
                import json
                model = Model(self.vosk_model_path)
                rec = KaldiRecognizer(model, audio.sample_rate)
                rec.AcceptWaveform(audio.frame_data)
                result = json.loads(rec.FinalResult())
                return result.get("text", "")
            except ImportError as exc:
                raise STTError("Vosk is not installed.") from exc
            except Exception as exc:
                raise STTError(f"Vosk recognition failed: {exc}") from exc
        raise STTError(f"Unknown STT engine: {self.engine}")
