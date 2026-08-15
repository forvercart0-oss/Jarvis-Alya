"""Tests for the offline heuristic router (used when Groq is unavailable)."""

from __future__ import annotations

import pytest

from brain.groq_client import GroqClient
from brain.router import Router


@pytest.fixture
def router():
    return Router(groq=GroqClient(None))


def _route(router, text):
    return router.heuristic_route(text)


def test_remember_routes_to_memory_tool(router):
    route = _route(router, "remember that my favorite editor is neovim")
    assert route.action == "tool"
    assert route.name == "remember"
    assert route.arguments["content"] == "my favorite editor is neovim"


def test_forget_routes(router):
    route = _route(router, "forget that my favorite editor")
    assert route.name == "forget"
    assert "favorite editor" in route.arguments["query"]


def test_open_app_routes(router):
    route = _route(router, "open Firefox")
    assert route.name == "open_application"
    assert route.arguments["app_name"] == "firefox"


def test_url_routes_to_browser(router):
    route = _route(router, "open https://example.com")
    assert route.name == "open_browser"
    assert "example.com" in route.arguments["url"]


def test_web_search_routes(router):
    route = _route(router, "search the web for pipewire documentation")
    assert route.name == "web_search"
    assert "pipewire" in route.arguments["query"]


def test_cpu_usage_routes(router):
    assert _route(router, "what is my CPU usage?").name == "cpu_usage"
    assert _route(router, "check my memory usage").name == "memory_usage"


def test_time_routes(router):
    assert _route(router, "what time is it").name == "get_time"
    assert _route(router, "what is the date").name == "get_date"


def test_calculate_routes(router):
    route = _route(router, "calculate 25 times 48")
    assert route.name == "calculator"
    assert route.arguments["expression"] == "25*48"


def test_volume_routes(router):
    assert _route(router, "turn volume up").name == "volume_control"
    assert _route(router, "mute the volume").name == "volume_control"
    assert _route(router, "set volume to 40").arguments["level"] == 40


def test_power_routes(router):
    assert _route(router, "lock my computer").name == "lock_screen"
    assert _route(router, "reboot the system").name == "reboot"
    assert _route(router, "shutdown the computer").name == "shutdown"
    assert _route(router, "suspend the system").name == "suspend"


def test_unknown_falls_back_to_respond(router):
    route = _route(router, "tell me a nice story about the sea")
    assert route.action == "respond"


def test_read_file_routes(router):
    route = _route(router, "read /home/me/notes.txt")
    assert route.name == "read_file"
    assert route.arguments["path"] == "/home/me/notes.txt"


def test_decide_uses_heuristics_when_offline(router):
    import asyncio

    route = asyncio.run(router.decide([{"role": "user", "content": "what time is it"}]))
    assert route.name == "get_time"
