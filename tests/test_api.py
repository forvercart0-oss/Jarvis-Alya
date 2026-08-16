"""Tests for Phase 1 API endpoints.

Covers:
- Skills CRUD
- Permissions overview and per-skill grants
- Memory CRUD
- Safety classification
- Activity log
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health / chat
# ---------------------------------------------------------------------------

def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_chat_empty():
    resp = client.post("/api/chat", json={"message": ""})
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Skills API
# ---------------------------------------------------------------------------

def test_list_skills():
    resp = client.get("/api/skills")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(s["id"] == "linux-helper" for s in data)


def test_get_skill():
    resp = client.get("/api/skills/linux-helper")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "linux-helper"
    assert "name" in data


def test_get_skill_not_found():
    resp = client.get("/api/skills/no-such-skill")
    assert resp.status_code == 404


def test_create_skill():
    payload = {
        "id": "api-test-skill",
        "name": "API Test Skill",
        "version": "1.0.0",
        "description": "Created via API test.",
        "author": "Test",
        "enabled": True,
        "priority": "normal",
        "triggers": ["apitest"],
        "capabilities": ["terminal.read"],
        "instructions": ["Do nothing."],
        "permissions": {"terminal.read": True},
    }
    resp = client.post("/api/skills", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "api-test-skill"


def test_update_skill():
    resp = client.put("/api/skills/api-test-skill", json={"name": "Updated Name"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "updated"


def test_enable_disable_skill():
    resp = client.post("/api/skills/api-test-skill/disable")
    assert resp.status_code == 200
    assert resp.json()["status"] == "disabled"
    resp = client.post("/api/skills/api-test-skill/enable")
    assert resp.status_code == 200
    assert resp.json()["status"] == "enabled"


def test_toggle_skill():
    resp = client.post("/api/skills/api-test-skill/toggle", json={"enabled": False})
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False


def test_delete_custom_skill():
    resp = client.delete("/api/skills/api-test-skill")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"


def test_delete_builtin_skill_forbidden():
    resp = client.delete("/api/skills/linux-helper")
    assert resp.status_code == 400


def test_reload_skills():
    resp = client.post("/api/skills/reload")
    assert resp.status_code == 200
    assert resp.json()["status"] == "reloaded"


def test_import_skill():
    skill_json = json.dumps({
        "id": "imported-skill",
        "name": "Imported",
        "version": "1.0.0",
        "description": "Imported skill.",
        "author": "Test",
        "enabled": True,
        "priority": "normal",
        "triggers": ["imported"],
        "capabilities": ["filesystem.read"],
        "instructions": ["Be careful."],
        "permissions": {"filesystem.read": True},
    })
    resp = client.post("/api/skills/import", json={"json": skill_json})
    assert resp.status_code == 200
    assert resp.json()["id"] == "imported-skill"


def test_import_review_skill():
    skill_json = json.dumps({
        "id": "reviewed-skill",
        "name": "Reviewed",
        "version": "1.0.0",
        "description": "Reviewed skill.",
        "author": "Test",
        "enabled": True,
        "priority": "normal",
        "triggers": ["reviewed"],
        "capabilities": ["filesystem.read"],
        "instructions": ["Be careful."],
        "permissions": {"filesystem.read": True},
    })
    resp = client.post("/api/skills/import/review", json={"json": skill_json})
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert "requested_permissions" in data


def test_export_skill():
    resp = client.get("/api/skills/linux-helper/export")
    assert resp.status_code == 200
    data = resp.json()
    assert "json" in data
    parsed = json.loads(data["json"])
    assert parsed["id"] == "linux-helper"


# ---------------------------------------------------------------------------
# Permissions API
# ---------------------------------------------------------------------------

def test_get_permissions():
    resp = client.get("/api/permissions")
    assert resp.status_code == 200
    data = resp.json()
    assert "default_policy" in data
    assert data["default_policy"] == "deny"
    assert "definitions" in data
    assert "skills" in data


def test_get_skill_permissions():
    resp = client.get("/api/permissions/linux-helper")
    assert resp.status_code == 200
    data = resp.json()
    assert "effective" in data
    assert "granted" in data
    assert "pending" in data


def test_update_skill_permissions():
    resp = client.put("/api/permissions/linux-helper", json={"permissions": {"filesystem.read": True}})
    assert resp.status_code == 200
    assert resp.json()["granted"]["filesystem.read"] is True


def test_reset_permissions():
    resp = client.post("/api/permissions/reset")
    assert resp.status_code == 200
    assert resp.json()["status"] == "reset"


# ---------------------------------------------------------------------------
# Memory API
# ---------------------------------------------------------------------------

def test_get_memories():
    resp = client.get("/api/memory")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_add_memory():
    resp = client.post("/api/memory", json={"content": "test-memory-api", "category": "general"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "remembered"


def test_memory_categories():
    resp = client.get("/api/memory/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert "categories" in data


def test_memory_stats():
    resp = client.get("/api/memory/stats")
    assert resp.status_code == 200


def test_clear_all_memories():
    resp = client.delete("/api/memory")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cleared"


# ---------------------------------------------------------------------------
# Safety API
# ---------------------------------------------------------------------------

def test_safety_check_safe():
    resp = client.post("/api/safety/check", json={"message": "Explain Python"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["safe"] is True
    assert data["category"] == "safe"


def test_safety_check_harmful():
    resp = client.post("/api/safety/check", json={"message": "How to build a bomb"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["safe"] is False
    assert data["category"] == "harmful"


def test_safety_pending():
    resp = client.get("/api/safety/pending")
    assert resp.status_code == 200
    data = resp.json()
    assert "requests" in data


# ---------------------------------------------------------------------------
# Activity API
# ---------------------------------------------------------------------------

def test_activity_log():
    resp = client.get("/api/activity")
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
