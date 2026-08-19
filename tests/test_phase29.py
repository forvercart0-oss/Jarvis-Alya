"""Tests for Phase 29 advanced memory features."""

from __future__ import annotations

import pytest

from memory.types import ErrorCategory, IdeaStatus, PrivacyLevel, TrustLevel


def test_new_memory_types_exist():
    assert IdeaStatus.IDEA == "idea"
    assert IdeaStatus.PLANNED == "planned"
    assert IdeaStatus.IN_PROGRESS == "in_progress"
    assert IdeaStatus.COMPLETED == "completed"
    assert IdeaStatus.ARCHIVED == "archived"
    assert ErrorCategory.NETWORK == "network"
    assert ErrorCategory.BUILD == "build"
    assert PrivacyLevel.NORMAL == "normal"
    assert TrustLevel.TRUSTED == "trusted"


def test_remember_with_new_fields(tmp_db):
    mem = tmp_db.remember(
        "Test memory",
        privacy_level="private",
        is_pinned=True,
        trust_level="trusted",
        quality_score=0.9,
    )
    assert mem["privacy_level"] == "private"
    assert mem["is_pinned"] is True
    assert mem["trust_level"] == "trusted"
    assert mem["quality_score"] == 0.9


def test_update_memory_tracks_previous_value(tmp_db):
    mem = tmp_db.remember("Original value")
    tmp_db.update_memory(mem["id"], "Updated value")
    updated = tmp_db.get_memory_by_id(mem["id"])
    assert updated["value"] == "Updated value"
    assert updated.get("previous_value") == "Original value"


def test_pin_unpin_memory(tmp_db):
    mem = tmp_db.remember("Pinnable memory")
    pinned = tmp_db.pin_memory(mem["id"])
    assert pinned is not None
    assert pinned["is_pinned"] is True
    unpinned = tmp_db.unpin_memory(mem["id"])
    assert unpinned is not None
    assert unpinned["is_pinned"] is False


def test_set_trust_level(tmp_db):
    mem = tmp_db.remember("Trusted memory")
    result = tmp_db.set_trust_level(mem["id"], "trusted")
    assert result is not None
    assert result["trust_level"] == "trusted"


def test_set_privacy_level(tmp_db):
    mem = tmp_db.remember("Private memory")
    result = tmp_db.set_privacy_level(mem["id"], "private")
    assert result is not None
    assert result["privacy_level"] == "private"


def test_set_quality_score(tmp_db):
    mem = tmp_db.remember("Scored memory")
    result = tmp_db.set_quality_score(mem["id"], 0.85)
    assert result is not None
    assert result["quality_score"] == 0.85


def test_create_idea(tmp_db):
    idea = tmp_db.create_idea("New Project Idea", description="Build a cool app", tags=["coding", "project"], status="idea")
    assert idea["title"] == "New Project Idea"
    assert idea["status"] == "idea"
    assert "coding" in idea["tags"]


def test_get_ideas(tmp_db):
    tmp_db.create_idea("Idea 1", status="idea")
    tmp_db.create_idea("Idea 2", status="planned")
    ideas = tmp_db.get_ideas()
    assert len(ideas) == 2
    planned = tmp_db.get_ideas(status="planned")
    assert len(planned) == 1


def test_update_idea(tmp_db):
    idea = tmp_db.create_idea("Old Title")
    updated = tmp_db.update_idea(idea["id"], {"title": "New Title", "status": "in_progress"})
    assert updated["title"] == "New Title"
    assert updated["status"] == "in_progress"


def test_delete_idea(tmp_db):
    idea = tmp_db.create_idea("Delete Me")
    result = tmp_db.delete_idea(idea["id"])
    assert result is True
    assert tmp_db.get_idea_by_id(idea["id"]) is None


def test_record_error(tmp_db):
    err = tmp_db.record_error("Connection refused", "Restart server", category="network", confidence=0.9)
    assert err["error_signature"] == "Connection refused"
    assert err["resolution"] == "Restart server"
    assert err["category"] == "network"


def test_find_error_resolution(tmp_db):
    tmp_db.record_error("Port 8000 in use", "Kill uvicorn", category="network")
    tmp_db.record_error("Port 8000 already in use", "Stop process", category="network")
    results = tmp_db.find_error_resolution("Port 8000")
    assert len(results) >= 1


def test_get_errors(tmp_db):
    tmp_db.record_error("Error 1", "Fix 1", category="build", project="myproject")
    tmp_db.record_error("Error 2", "Fix 2", category="network")
    errors = tmp_db.get_errors()
    assert len(errors) == 2
    project_errors = tmp_db.get_errors(project="myproject")
    assert len(project_errors) == 1


def test_delete_error(tmp_db):
    err = tmp_db.record_error("Temp error", "Temp fix")
    result = tmp_db.delete_error(err["id"])
    assert result is True


def test_cache_set_and_get(tmp_db):
    cache = tmp_db.cache
    cache.set("test_key", {"data": "test"}, ttl=60)
    result = cache.get("test_key")
    assert result is not None
    assert result["data"] == "test"


def test_cache_invalidate(tmp_db):
    cache = tmp_db.cache
    cache.set("test_key", {"data": "test"})
    cache.invalidate("test_key")
    assert cache.get("test_key") is None


def test_migrator_runs(tmp_db):
    result = tmp_db.run_migration()
    assert "version" in result
    assert result["version"] >= 0


def test_secret_still_blocked(tmp_db):
    with pytest.raises(Exception):
        tmp_db.remember("my key is sk-1234567890abcdefghij")


def test_memory_categories_include_phase29(tmp_db):
    from memory.manager import MEMORY_CATEGORIES
    assert "coding" in MEMORY_CATEGORIES
    assert "technical" in MEMORY_CATEGORIES
    assert "idea" in MEMORY_CATEGORIES
    assert "error" in MEMORY_CATEGORIES
    assert "knowledge" in MEMORY_CATEGORIES


def test_ideas_system_integration(tmp_db):
    idea = tmp_db.create_idea("Test", status="idea")
    assert idea["status"] == "idea"
    updated = tmp_db.update_idea(idea["id"], {"status": "completed"})
    assert updated["status"] == "completed"
    all_ideas = tmp_db.get_ideas()
    assert any(i["id"] == idea["id"] for i in all_ideas)


def test_error_memory_integration(tmp_db):
    err = tmp_db.record_error("Test error", "Test resolution", category="runtime")
    assert err["category"] == "runtime"
    found = tmp_db.find_error_resolution("Test error")
    assert len(found) >= 1
