"""Tests for persona definitions, prompts and runtime switching."""

from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace

from config.personas import PERSONAS, get_persona, persona_payload
from backend.services.persona_service import PersonaService


def _fake_settings(**overrides):
    values = {
        "persona": "jarvis",
        "assistant_name": "JARVIS",
        "accent_color": "#00f0ff",
        "tts_voice": "am_fenrir",
    }
    values.update(overrides)

    class FakeSettings:
        def __init__(self):
            self.persona = values["persona"]
            self.assistant_name = values["assistant_name"]
            self.accent_color = values["accent_color"]
            self.tts_voice = values["tts_voice"]

        def persist(self):
            pass

    return FakeSettings()


def _stub_backend_main(monkeypatch, calls):
    store = SimpleNamespace(set_setting=lambda k, v: calls.append((k, v)))
    memory_manager = SimpleNamespace(store=store)
    monkeypatch.setitem(
        sys.modules,
        "backend.main",
        SimpleNamespace(tts_manager=None, memory_manager=memory_manager),
    )


def test_persona_definitions():
    jarvis = get_persona("jarvis")
    alya = get_persona("alya")
    assert jarvis.gender == "male"
    assert alya.gender == "female"
    assert jarvis.default_voice == "am_fenrir"
    assert alya.default_voice == "af_heart"
    assert jarvis.accent_color == "#00f0ff"
    assert alya.accent_color == "#ff6ec7"


def test_get_persona_falls_back_to_jarvis():
    assert get_persona("unknown") is PERSONAS["jarvis"]
    assert get_persona("ALYA").name == "ALYA"


def test_persona_payload_defaults():
    jarvis = persona_payload("jarvis")
    assert jarvis["accent_color"] == "#00f0ff"
    assert jarvis["default_voice"] == "am_fenrir"
    assert jarvis["logo_id"] == "jarvis"
    assert "alya" in jarvis["available"]


def test_system_prompt_gender_grammar():
    jarvis_prompt = get_persona("jarvis").build_system_prompt("Sir", os_name="Linux")
    alya_prompt = get_persona("alya").build_system_prompt("Sir", os_name="Linux")
    assert "karta" in jarvis_prompt and "raha" in jarvis_prompt and "dunga" in jarvis_prompt
    assert "karti" in alya_prompt and "rahi" in alya_prompt and "dungi" in alya_prompt


def test_apply_persona_on_startup_fixes_stale_values():
    service = PersonaService()
    service.settings = _fake_settings(
        persona="jarvis", accent_color="cyan", tts_voice="cy", assistant_name="OldName"
    )
    asyncio.run(service.apply_persona_on_startup())
    assert service.settings.persona == "jarvis"
    assert service.settings.assistant_name == "JARVIS"
    assert service.settings.accent_color == "#00f0ff"
    assert service.settings.tts_voice == "am_fenrir"


def test_apply_persona_on_startup_keeps_valid_values():
    service = PersonaService()
    service.settings = _fake_settings(
        persona="alya", accent_color="#ff6ec7", tts_voice="af_heart", assistant_name="ALYA"
    )
    asyncio.run(service.apply_persona_on_startup())
    assert service.settings.accent_color == "#ff6ec7"
    assert service.settings.tts_voice == "af_heart"


def test_apply_persona_on_startup_writes_corrections_to_db(monkeypatch):
    recorder = []
    _stub_backend_main(monkeypatch, recorder)

    service = PersonaService()
    service.settings = _fake_settings(
        persona="jarvis", accent_color="cyan", tts_voice="cy", assistant_name="JARVIS"
    )
    asyncio.run(service.apply_persona_on_startup())
    written = dict(recorder)
    assert written["persona"] == "jarvis"
    assert written["accent_color"] == "#00f0ff"
    assert written["tts_voice"] == "am_fenrir"


def test_switch_updates_settings_and_payload(monkeypatch):
    recorder = []
    _stub_backend_main(monkeypatch, recorder)

    service = PersonaService()
    service.settings = _fake_settings()
    payload = asyncio.run(service.switch("alya"))

    assert service.settings.persona == "alya"
    assert service.settings.assistant_name == "ALYA"
    assert service.settings.tts_voice == "af_heart"
    assert service.settings.accent_color == "#ff6ec7"
    assert payload["id"] == "alya"
    assert payload["accent_color"] == "#ff6ec7"

    written = dict(recorder)
    assert written["persona"] == "alya"
    assert written["tts_voice"] == "af_heart"


def test_switch_back_to_jarvis(monkeypatch):
    recorder = []
    _stub_backend_main(monkeypatch, recorder)

    service = PersonaService()
    service.settings = _fake_settings(
        persona="alya", accent_color="#ff6ec7", tts_voice="af_heart", assistant_name="ALYA"
    )
    payload = asyncio.run(service.switch("jarvis"))
    assert payload["id"] == "jarvis"
    assert payload["accent_color"] == "#00f0ff"
    assert service.settings.tts_voice == "am_fenrir"
