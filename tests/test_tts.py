"""Tests for TTS (espeak-ng + pw-play pipeline)."""

from __future__ import annotations

import asyncio
import subprocess
from types import SimpleNamespace

from voice.tts import TTS


def _settings(**overrides):
    defaults = {"tts_voice": "en+f3", "tts_speed": 160, "tts_volume": 80}
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _fake_which(monkeypatch):
    def which(name):
        return {
            "espeak-ng": "/usr/bin/espeak-ng",
            "pw-play": "/usr/bin/pw-play",
        }.get(name)

    monkeypatch.setattr("voice.tts.shutil.which", which)


def test_is_available(monkeypatch):
    monkeypatch.setattr("voice.tts.shutil.which", lambda n: "/usr/bin/espeak-ng" if n == "espeak-ng" else None)
    assert TTS.is_available() is True

    monkeypatch.setattr("voice.tts.shutil.which", lambda n: None)
    assert TTS.is_available() is False


def test_playback_binary_fallback_order(monkeypatch):
    def which(name):
        return "/usr/bin/paplay" if name == "paplay" else None

    monkeypatch.setattr("voice.tts.shutil.which", which)
    assert TTS.playback_binary() == "paplay"


def test_speak_runs_espeak_and_play(monkeypatch):
    _fake_which(monkeypatch)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess([], 0)

    monkeypatch.setattr("voice.tts.subprocess.run", fake_run)

    tts = TTS(_settings())
    assert asyncio.run(tts.speak("Hello Sir")) is True

    espeak_call = calls[0]
    assert espeak_call[0] == "espeak-ng"
    assert espeak_call[espeak_call.index("-v") + 1] == "en+f3"
    assert espeak_call[espeak_call.index("-s") + 1] == "160"

    play_call = calls[1]
    assert play_call[0] == "pw-play"
    assert play_call[play_call.index("--volume") + 1] == "0.80"


def test_speak_returns_false_when_espeak_missing(monkeypatch):
    monkeypatch.setattr("voice.tts.shutil.which", lambda n: "/usr/bin/pw-play" if n == "pw-play" else None)
    assert asyncio.run(TTS(_settings()).speak("hello")) is False


def test_speak_returns_false_on_empty_text(monkeypatch):
    _fake_which(monkeypatch)
    assert asyncio.run(TTS(_settings()).speak("")) is False


def test_volume_gets_clamped_to_pw_play_range(monkeypatch):
    _fake_which(monkeypatch)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess([], 0)

    monkeypatch.setattr("voice.tts.subprocess.run", fake_run)

    tts = TTS(_settings(tts_volume=100))
    asyncio.run(tts.speak("loud"))
    assert calls[1][calls[1].index("--volume") + 1] == "1.00"


def test_setters_clamp_values():
    tts = TTS(_settings())
    tts.set_speed(9999)
    assert tts.speed == 500
    tts.set_volume(-5)
    assert tts.volume == 0
    tts.set_volume(150)
    assert tts.volume == 100
    tts.set_voice("ur")
    assert tts.voice == "ur"
