"""Tests for the tool registry: registration, execution, confirmation gates."""

from __future__ import annotations

import asyncio

import pytest

from tools import build_registry
from tools.registry import Tool, ToolRegistry


@pytest.mark.asyncio
async def test_registry_contains_core_tools(tmp_db):
    registry = build_registry(tmp_db)
    names = registry.names()
    for expected in ("terminal", "calculator", "get_time", "read_file", "system_info"):
        assert expected in names


@pytest.mark.asyncio
async def test_calculator_executes(tmp_db):
    registry = build_registry(tmp_db)
    result = await registry.execute("calculator", {"expression": "25 * 48"})
    assert result.success is True
    assert result.result["result"] == 1200


@pytest.mark.asyncio
async def test_unknown_tool_fails(tmp_db):
    registry = build_registry(tmp_db)
    result = await registry.execute("no_such_tool", {})
    assert result.success is False
    assert "Unknown tool" in result.error


@pytest.mark.asyncio
async def test_static_confirmation_gate(tmp_db):
    registry = build_registry(tmp_db)
    result = await registry.execute("shutdown", {})
    assert result.success is False
    assert result.confirmation_required is True
    assert result.confirmation_message


@pytest.mark.asyncio
async def test_confirmed_shutdown_runs(monkeypatch, tmp_db):
    import subprocess

    fake = subprocess.CompletedProcess([], 0, stdout="", stderr="")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return fake

    monkeypatch.setattr("system.linux.run", fake_run)

    registry = build_registry(tmp_db)
    result = await registry.execute("shutdown", {}, confirmed=True)
    assert result.success is True
    assert ["systemctl", "poweroff"] in calls


@pytest.mark.asyncio
async def test_lock_screen_does_not_require_confirmation(monkeypatch, tmp_db):
    import subprocess

    fake = subprocess.CompletedProcess([], 0, stdout="", stderr="")
    monkeypatch.setattr("system.linux.run", lambda cmd, **k: fake)
    monkeypatch.setattr("system.linux.which", lambda *names: "/usr/bin/loginctl")

    registry = build_registry(tmp_db)
    result = await registry.execute("lock_screen", {})
    assert result.confirmation_required is False
    assert result.success is True


@pytest.mark.asyncio
async def test_memory_tools_roundtrip(tmp_db):
    registry = build_registry(tmp_db)
    await registry.execute("remember", {"content": "my favorite color is blue"})
    result = await registry.execute("recall_memories", {"query": "favorite color"})
    assert result.success is True
    assert result.result["memories"]

    forgot = await registry.execute("forget", {"query": "favorite color"})
    assert forgot.success is True


def test_registry_spec_is_openai_compatible(tmp_db):
    registry = build_registry(tmp_db)
    spec = registry.tools_spec()
    assert spec and spec[0]["type"] == "function"
    assert "name" in spec[0]["function"]


@pytest.mark.asyncio
async def test_custom_registration_and_confirmation():
    registry = ToolRegistry()
    calls = []

    async def handler(value: int = 1):
        calls.append(value)
        return {"ok": True}

    registry.register_handler("demo", "A demo tool", {"type": "object", "properties": {}}, handler)

    result = await registry.execute("demo", {"value": 42})
    assert result.success is True
    assert result.result == {"ok": True}
    assert calls == [42]


def test_registry_refuses_duplicate_names():
    registry = ToolRegistry()

    class A(Tool):
        name = "dup"

    class B(Tool):
        name = "dup"

    registry.register(A())
    with pytest.raises(AssertionError):
        registry.register(B())


@pytest.mark.asyncio
async def test_type_error_becomes_friendly_error():
    registry = ToolRegistry()

    class BadArgs(Tool):
        name = "bad_args"

        async def execute(self, needed: int) -> dict:
            return {"needed": needed}

    registry.register(BadArgs())
    result = await registry.execute("bad_args", {})
    assert result.success is False
    assert "Invalid arguments" in result.error


def test_run_sync_helpers(tmp_db):
    """Helper to run a coroutine from a sync test."""

    async def go():
        registry = build_registry(tmp_db)
        return await registry.execute("calculator", {"expression": "2 + 2"})

    result = asyncio.run(go())
    assert result.result["result"] == 4


@pytest.mark.asyncio
async def test_registry_extracts_confirmed_from_arguments(tmp_db):
    registry = build_registry(tmp_db)
    result = await registry.execute("delete_file", {"path": "/tmp/nope.txt", "confirmed": True})
    assert result.success is False
    assert "No such file" in result.error


@pytest.mark.asyncio
async def test_tool_service_confirmed_in_arguments_wins(tmp_db):
    from backend.services.tool_service import ToolService

    registry = build_registry(tmp_db)
    service = ToolService(registry)

    result = await service.execute("delete_file", arguments={"path": "/tmp/nope.txt", "confirmed": True}, confirmed=False)
    assert result.success is False
    assert "No such file" in result.error


@pytest.mark.asyncio
async def test_tool_service_confirmed_kwarg(tmp_db, tmp_path):
    from backend.services.tool_service import ToolService

    registry = build_registry(tmp_db)
    service = ToolService(registry)

    target = tmp_path / "to-delete.txt"
    target.write_text("data")

    result = await service.execute("delete_file", arguments={"path": str(target)}, confirmed=True)
    assert result.success is True
    assert not target.exists()

