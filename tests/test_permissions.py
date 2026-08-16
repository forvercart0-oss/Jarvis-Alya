"""Tests for the Phase 1 Permission system.

Covers:
- Permission defaults (deny-all)
- Permission grant / denial
- Permission persistence
- Legacy permission key mapping
- Tool permission requirements
- Permission revocation
"""

from __future__ import annotations

import json

import pytest

from permissions.manager import PermissionManager
from permissions.models import ALL_PERMISSIONS, PERMISSION_DESCRIPTIONS
from permissions.policy import TOOL_PERMISSION_REQUIREMENTS
from permissions.registry import requested_permissions, requested_permissions_full

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def perm_path(tmp_path):
    return tmp_path / "permissions.json"


@pytest.fixture
def perm_mgr(perm_path):
    return PermissionManager(perm_path)


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

def test_default_deny_all(perm_mgr):
    for perm in ALL_PERMISSIONS:
        assert perm_mgr.is_allowed("any-skill", perm) is False


def test_effective_returns_only_granted(perm_mgr):
    perm_mgr.grant("skill-1", {"filesystem.read": True})
    effective = perm_mgr.effective("skill-1", {"permissions": {"filesystem.read": True, "network.request": True}})
    assert effective["filesystem.read"] is True
    assert effective["network.request"] in (False, None)


# ---------------------------------------------------------------------------
# Grant / denial
# ---------------------------------------------------------------------------

def test_grant_single_permission(perm_mgr):
    perm_mgr.grant("s1", {"filesystem.read": True})
    assert perm_mgr.is_allowed("s1", "filesystem.read") is True
    assert perm_mgr.is_allowed("s1", "filesystem.write") is False


def test_grant_multiple_permissions(perm_mgr):
    perm_mgr.grant("s1", {"filesystem.read": True, "terminal.read": True, "network.request": False})
    assert perm_mgr.is_allowed("s1", "filesystem.read") is True
    assert perm_mgr.is_allowed("s1", "terminal.read") is True
    assert perm_mgr.is_allowed("s1", "network.request") is False


def test_revoke_removes_permission(perm_mgr):
    perm_mgr.grant("s1", {"filesystem.read": True, "terminal.read": True})
    assert perm_mgr.revoke("s1", "filesystem.read") is True
    assert perm_mgr.is_allowed("s1", "filesystem.read") is False
    assert perm_mgr.is_allowed("s1", "terminal.read") is True


def test_unknown_permission_is_ignored(perm_mgr):
    perm_mgr.grant("s1", {"totally_fake_perm": True})
    # Should not crash and should not grant anything real
    assert perm_mgr.get_granted("s1") == {}


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_permissions_persist_to_disk(perm_path):
    mgr = PermissionManager(perm_path)
    mgr.grant("s1", {"filesystem.write": True})
    mgr.save()
    assert perm_path.exists()
    data = json.loads(perm_path.read_text(encoding="utf-8"))
    assert data["default_policy"] == "deny"
    assert data["skills"]["s1"]["filesystem.write"] is True


def test_permissions_reload_from_disk(perm_path):
    perm_path.write_text(
        json.dumps({"version": 1, "default_policy": "deny", "skills": {"s1": {"filesystem.read": True}}}),
        encoding="utf-8",
    )
    mgr = PermissionManager(perm_path)
    assert mgr.is_allowed("s1", "filesystem.read") is True
    assert mgr.is_allowed("s1", "filesystem.write") is False


def test_reset_clears_all_grants(perm_mgr):
    perm_mgr.grant("s1", {"filesystem.read": True})
    perm_mgr.grant("s2", {"network.request": True})
    count = perm_mgr.reset()
    assert count == 2
    assert perm_mgr.is_allowed("s1", "filesystem.read") is False
    assert perm_mgr.is_allowed("s2", "network.request") is False


def test_reset_skill_clears_single(perm_mgr):
    perm_mgr.grant("s1", {"filesystem.read": True})
    perm_mgr.grant("s2", {"network.request": True})
    ok = perm_mgr.reset_skill("s1")
    assert ok is True
    assert perm_mgr.is_allowed("s1", "filesystem.read") is False
    assert perm_mgr.is_allowed("s2", "network.request") is True


# ---------------------------------------------------------------------------
# Legacy permission mapping
# ---------------------------------------------------------------------------

def test_legacy_keys_are_mapped(perm_mgr):
    perm_mgr.grant("s1", {"filesystem_read": True, "terminal": True})
    assert perm_mgr.is_allowed("s1", "filesystem.read") is True
    assert perm_mgr.is_allowed("s1", "terminal.read") is True
    assert perm_mgr.is_allowed("s1", "terminal.execute") is True


# ---------------------------------------------------------------------------
# Requested permissions extraction
# ---------------------------------------------------------------------------

def test_requested_permissions_from_skill_dict():
    skill = {
        "permissions": {"filesystem.read": True, "network.request": False},
        "capabilities": ["terminal.read", "terminal.execute"],
    }
    perms = requested_permissions(skill)
    assert "filesystem.read" in perms
    assert "terminal.read" in perms
    assert "terminal.execute" in perms
    assert "network.request" not in perms


def test_requested_permissions_full():
    skill = {"permissions": {"filesystem.read": True}, "capabilities": []}
    full = requested_permissions_full(skill)
    assert full["filesystem.read"] is True
    assert full["network.request"] is False


# ---------------------------------------------------------------------------
# Tool permission requirements
# ---------------------------------------------------------------------------

def test_read_file_requires_filesystem_read():
    assert TOOL_PERMISSION_REQUIREMENTS.get("read_file") == ("filesystem.read",)


def test_terminal_requires_terminal_permissions():
    assert "terminal.read" in TOOL_PERMISSION_REQUIREMENTS["terminal"]
    assert "terminal.execute" in TOOL_PERMISSION_REQUIREMENTS["terminal"]


def test_observation_only_tools_have_no_requirements():
    from permissions.policy import OBSERVATION_ONLY_TOOLS
    for tool in ("system_info", "get_time", "calculator"):
        assert tool in OBSERVATION_ONLY_TOOLS


# ---------------------------------------------------------------------------
# Permission definitions
# ---------------------------------------------------------------------------

def test_all_permissions_have_descriptions():
    for perm in ALL_PERMISSIONS:
        assert perm in PERMISSION_DESCRIPTIONS
        desc = PERMISSION_DESCRIPTIONS[perm]
        assert desc.label
        assert desc.description
        assert desc.risk in ("low", "medium", "high")


# ---------------------------------------------------------------------------
# is_tool_allowed
# ---------------------------------------------------------------------------

def test_is_tool_allowed_when_granted(perm_mgr):
    skill = {"permissions": {"filesystem.read": True}, "id": "s1", "enabled": True}
    perm_mgr.grant("s1", {"filesystem.read": True})
    assert perm_mgr.is_tool_allowed("s1", "read_file", skill) is True


def test_is_tool_allowed_when_not_granted(perm_mgr):
    skill = {"permissions": {"filesystem.read": True}, "id": "s1", "enabled": True}
    assert perm_mgr.is_tool_allowed("s1", "read_file", skill) is False


def test_is_tool_allowed_observation_tool_always_true(perm_mgr):
    skill = {"permissions": {}, "id": "s1", "enabled": True}
    assert perm_mgr.is_tool_allowed("s1", "system_info", skill) is True


def test_pending_returns_requested_but_not_granted(perm_mgr):
    skill = {"permissions": {"filesystem.read": True, "filesystem.write": True}, "id": "s1", "enabled": True}
    perm_mgr.grant("s1", {"filesystem.read": True})
    pending = perm_mgr.pending("s1", skill)
    assert pending["filesystem.write"] is True
    assert pending.get("filesystem.read", False) is False
