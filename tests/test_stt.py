"""Tests for speech-to-text recognition (engines + error handling)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import speech_recognition as sr

from voice.recognizer import Recognizer, STTError


def _settings(**overrides):
    defaults = {"stt_engine": "google", "voice_language": "en-US"}
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _audio():
    return sr.AudioData(b"\x00" * 3200, 16000, 2)


def test_google_engine_returns_text(monkeypatch):
    monkeypatch.setattr(
        sr.Recognizer,
        "recognize_google",
        lambda self, audio, language="en": "hello world",
    )
    recognizer = Recognizer(_settings())
    assert recognizer.recognize(_audio()) == "hello world"


def test_google_unknown_value_returns_none(monkeypatch):
    def raise_unknown(self, audio, language="en"):
        raise sr.UnknownValueError

    monkeypatch.setattr(sr.Recognizer, "recognize_google", raise_unknown)
    recognizer = Recognizer(_settings())
    assert recognizer.recognize(_audio()) is None


def test_google_request_error_raises_friendly(monkeypatch):
    def raise_request(self, audio, language="en"):
        raise sr.RequestError("network down")

    monkeypatch.setattr(sr.Recognizer, "recognize_google", raise_request)
    recognizer = Recognizer(_settings())
    with pytest.raises(STTError, match="unreachable"):
        recognizer.recognize(_audio())


def test_engine_selection_from_settings():
    assert Recognizer(_settings(stt_engine="vosk")).engine == "vosk"
    assert Recognizer(_settings(stt_engine="google")).engine == "google"


def test_vosk_missing_model_raises_friendly(monkeypatch):

    recognizer = Recognizer(_settings(stt_engine="vosk", vosk_model_path="/nonexistent/model", data_dir="/tmp"))
    with pytest.raises(STTError):
        try:
            recognizer.recognize(_audio())
        except STTError as exc:
            assert "vosk" in str(exc).lower()
            raise
