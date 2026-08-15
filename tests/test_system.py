"""Tests for the system platform abstraction and computer control layer."""

from __future__ import annotations

import asyncio
import platform as _platform

from system import get_platform
from computer.controller import ComputerController


def test_platform_resolves_to_expected_backend(monkeypatch):
    monkeypatch.setattr(_platform, "system", lambda: "Linux")
    assert get_platform().name == "linux"

    monkeypatch.setattr(_platform, "system", lambda: "Windows")
    assert get_platform().name == "windows"

    monkeypatch.setattr(_platform, "system", lambda: "Darwin")
    assert get_platform().name == "macos"


def test_platform_info_returns_string():
    assert isinstance(get_platform().info(), str)
    assert len(get_platform().info()) > 0


def test_computer_controller_exposes_platform_and_input():
    controller = ComputerController()
    assert controller.platform.name in ("linux", "windows", "macos")
    assert hasattr(controller.input, "type_text")
    assert hasattr(controller.input, "click_at")


def test_audio_server_status_is_dict(monkeypatch):
    controller = ComputerController()

    async def fake_audio():
        return {"status": "online"}

    monkeypatch.setattr(controller.platform, "audio_server_status", fake_audio)
    assert asyncio.run(controller.audio_server_status())["status"] == "online"


def test_volume_delegates_to_platform(monkeypatch):
    controller = ComputerController()
    calls = []

    async def fake_set_volume(level):
        calls.append(level)
        return {"ok": True, "level": level}

    monkeypatch.setattr(controller.platform, "set_volume", fake_set_volume)
    result = asyncio.run(controller.set_volume(40))
    assert calls == [40]
    assert result["level"] == 40


def test_screenshot_returns_base64(monkeypatch):
    controller = ComputerController()

    async def fake_screenshot(path, region):
        return {"ok": True, "format": "png", "data": "AAAA"}

    monkeypatch.setattr(controller.platform, "screenshot", fake_screenshot)
    result = asyncio.run(controller.screenshot())
    assert result["data"] == "AAAA"


def test_input_controller_fallback_returns_friendly_error(monkeypatch):
    from computer.input import InputController

    controller = InputController()
    monkeypatch.setattr(controller, "detect", lambda: None)
    result = asyncio.run(controller.type_text("hello"))
    assert result["ok"] is False
    assert "input automation tool" in result["error"]
