"""Tests for the Phase 1 Skills system.

Covers:
- Skill JSON validation
- Skill loading from builtin/custom directories
- Skill registration, enable/disable
- Skill routing / matching
- Skill failure resilience
- Import / export
"""

from __future__ import annotations

import json

import pytest

from skills.loader import load_all_skills, load_skill_file, load_skills_from_directory
from skills.manager import SkillManager
from skills.registry import SkillRegistry
from skills.router import SkillRouter
from skills.validator import SkillValidationError, validate_skill

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_dir(tmp_path):
    builtin = tmp_path / "builtin"
    custom = tmp_path / "custom"
    builtin.mkdir()
    custom.mkdir()
    return tmp_path


@pytest.fixture
def skill_registry(base_dir):
    states = base_dir / "skill_states.json"
    return SkillRegistry(base_dir=base_dir, states_file=states)


@pytest.fixture
def skill_manager(skill_registry):
    return SkillManager(skill_registry)


# ---------------------------------------------------------------------------
# JSON validation
# ---------------------------------------------------------------------------

VALID_SKILL = {
    "id": "test-skill",
    "name": "Test Skill",
    "version": "1.0.0",
    "description": "A test skill.",
    "author": "User",
    "enabled": True,
    "priority": "normal",
    "triggers": ["test", "hello"],
    "capabilities": ["terminal.read"],
    "instructions": ["Do nothing harmful."],
    "permissions": {"terminal.read": True},
}


def test_validate_skill_accepts_valid():
    validate_skill(VALID_SKILL)


def test_validate_skill_rejects_missing_id():
    with pytest.raises(SkillValidationError):
        validate_skill({})


def test_validate_skill_rejects_invalid_priority():
    with pytest.raises(SkillValidationError):
        validate_skill({**VALID_SKILL, "priority": "urgent"})


def test_validate_skill_rejects_empty_triggers():
    with pytest.raises(SkillValidationError):
        validate_skill({**VALID_SKILL, "triggers": []})


def test_validate_skill_rejects_unknown_permission():
    with pytest.raises(SkillValidationError):
        validate_skill({**VALID_SKILL, "permissions": {"unknown_perm": True}})


def test_validate_skill_rejects_non_dict():
    with pytest.raises(SkillValidationError):
        validate_skill("not a dict")


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def test_load_skill_file_success(base_dir):
    path = base_dir / "custom" / "hello.json"
    path.write_text(json.dumps(VALID_SKILL), encoding="utf-8")
    data = load_skill_file(path, source="custom")
    assert data["id"] == "test-skill"
    assert data["_source"] == "custom"


def test_load_skills_from_directory_empty(base_dir):
    result = load_skills_from_directory(base_dir / "custom", source="custom")
    assert result == {}


def test_load_all_skills_merges_builtin_and_custom(base_dir):
    builtin = {
        "id": "builtin-skill",
        "name": "Builtin",
        "version": "1.0.0",
        "description": "Builtin skill.",
        "author": "System",
        "enabled": True,
        "priority": "normal",
        "triggers": ["builtin"],
        "capabilities": ["filesystem.read"],
        "instructions": ["Be helpful."],
        "permissions": {"filesystem.read": True},
    }
    custom = {
        "id": "custom-skill",
        "name": "Custom",
        "version": "1.0.0",
        "description": "Custom skill.",
        "author": "User",
        "enabled": True,
        "priority": "high",
        "triggers": ["custom"],
        "capabilities": ["network.request"],
        "instructions": ["Do custom things."],
        "permissions": {"network.request": True},
    }
    (base_dir / "builtin" / "b.json").write_text(json.dumps(builtin), encoding="utf-8")
    (base_dir / "custom" / "c.json").write_text(json.dumps(custom), encoding="utf-8")
    result = load_all_skills(base_dir)
    assert "builtin-skill" in result
    assert "custom-skill" in result


def test_load_skill_file_skips_invalid_json(base_dir, caplog):
    path = base_dir / "custom" / "bad.json"
    path.write_text("not json", encoding="utf-8")
    result = load_skills_from_directory(base_dir / "custom")
    assert result == {}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def test_registry_load_populates_skills(skill_registry, base_dir):
    path = base_dir / "custom" / "s.json"
    path.write_text(json.dumps(VALID_SKILL), encoding="utf-8")
    skill_registry.load()
    assert skill_registry.get("test-skill") is not None


def test_registry_enable_disable(skill_registry, base_dir):
    path = base_dir / "custom" / "s.json"
    path.write_text(json.dumps(VALID_SKILL), encoding="utf-8")
    skill_registry.load()
    assert skill_registry.enable("test-skill") is True
    assert skill_registry.get("test-skill")["enabled"] is True
    assert skill_registry.disable("test-skill") is True
    assert skill_registry.get("test-skill")["enabled"] is False


def test_registry_delete_builtin_raises(skill_registry, base_dir):
    builtin = {**VALID_SKILL, "id": "builtin-skill"}
    (base_dir / "builtin" / "b.json").write_text(json.dumps(builtin), encoding="utf-8")
    skill_registry.load()
    with pytest.raises(ValueError):
        skill_registry.delete_skill("builtin-skill")


def test_registry_match_returns_enabled_skills(skill_registry, base_dir):
    path = base_dir / "custom" / "s.json"
    path.write_text(json.dumps(VALID_SKILL), encoding="utf-8")
    skill_registry.load()
    matches = skill_registry.match("please test this")
    assert len(matches) == 1
    assert matches[0]["id"] == "test-skill"


def test_registry_match_excludes_disabled(skill_registry, base_dir):
    path = base_dir / "custom" / "s.json"
    path.write_text(json.dumps(VALID_SKILL), encoding="utf-8")
    skill_registry.load()
    skill_registry.disable("test-skill")
    matches = skill_registry.match("please test this")
    assert matches == []


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

def test_manager_install_skill(skill_manager, base_dir):
    skill_id = skill_manager.install_skill(VALID_SKILL)
    assert skill_id == "test-skill"
    assert skill_manager.get_skill("test-skill") is not None
    assert (base_dir / "custom" / "test-skill.json").exists()


def test_manager_enable_disable(skill_manager):
    skill_manager.install_skill(VALID_SKILL)
    assert skill_manager.enable_skill("test-skill") is True
    assert skill_manager.disable_skill("test-skill") is True


def test_manager_remove_custom_skill(skill_manager, base_dir):
    skill_manager.install_skill(VALID_SKILL)
    assert skill_manager.remove_skill("test-skill") is True
    assert skill_manager.get_skill("test-skill") is None
    assert not (base_dir / "custom" / "test-skill.json").exists()


def test_manager_export_skill(skill_manager):
    skill_manager.install_skill(VALID_SKILL)
    exported = skill_manager.export_skill("test-skill")
    data = json.loads(exported)
    assert data["id"] == "test-skill"
    assert "_source" not in data


def test_manager_import_skill(skill_manager):
    json_str = json.dumps(VALID_SKILL)
    skill_id = skill_manager.import_skill(json_str)
    assert skill_id == "test-skill"
    assert skill_manager.get_skill("test-skill") is not None


def test_manager_update_skill(skill_manager):
    skill_manager.install_skill(VALID_SKILL)
    ok = skill_manager.update_skill("test-skill", {"name": "Updated"})
    assert ok is True
    assert skill_manager.get_skill("test-skill")["name"] == "Updated"


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def test_router_returns_matching_skill(skill_registry, base_dir):
    path = base_dir / "custom" / "s.json"
    path.write_text(json.dumps(VALID_SKILL), encoding="utf-8")
    skill_registry.load()
    r = SkillRouter(skill_registry)
    match = r.match_one("please test this")
    assert match is not None
    assert match["id"] == "test-skill"


def test_router_returns_none_when_no_match(skill_registry):
    r = SkillRouter(skill_registry)
    assert r.match_one("nothing matches here") is None


def test_router_returns_multiple_sorted_by_priority(skill_registry, base_dir):
    high = {**VALID_SKILL, "id": "high-skill", "priority": "high", "triggers": ["alpha"]}
    low = {**VALID_SKILL, "id": "low-skill", "priority": "low", "triggers": ["alpha"]}
    (base_dir / "custom" / "high.json").write_text(json.dumps(high), encoding="utf-8")
    (base_dir / "custom" / "low.json").write_text(json.dumps(low), encoding="utf-8")
    skill_registry.load()
    r = SkillRouter(skill_registry)
    matches = r.match("alpha")
    assert [m["id"] for m in matches] == ["high-skill", "low-skill"]


def test_router_excludes_disabled_skills(skill_registry, base_dir):
    path = base_dir / "custom" / "s.json"
    path.write_text(json.dumps(VALID_SKILL), encoding="utf-8")
    skill_registry.load()
    skill_registry.disable("test-skill")
    r = SkillRouter(skill_registry)
    assert r.match_one("test this") is None


# ---------------------------------------------------------------------------
# Failure resilience
# ---------------------------------------------------------------------------

def test_invalid_skill_file_is_skipped_during_load(base_dir, caplog):
    bad = base_dir / "custom" / "bad.json"
    bad.write_text("{invalid json", encoding="utf-8")
    good = base_dir / "custom" / "good.json"
    good.write_text(json.dumps(VALID_SKILL), encoding="utf-8")
    result = load_skills_from_directory(base_dir / "custom")
    assert "test-skill" in result
    assert "bad" not in result


def test_broken_skill_does_not_crash_manager(skill_manager, base_dir):
    bad = base_dir / "custom" / "bad.json"
    bad.write_text("{invalid json", encoding="utf-8")
    good = base_dir / "custom" / "good.json"
    good.write_text(json.dumps(VALID_SKILL), encoding="utf-8")
    skills = skill_manager.load_skills()
    assert any(s["id"] == "test-skill" for s in skills)
