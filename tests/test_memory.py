"""Tests for memory system: conversations, messages, and secret filtering."""

from __future__ import annotations

import pytest

from memory.manager import SecretMemoryError, normalize_category
from memory.secret_filter import contains_secret, filter_memory_text, scan_for_secrets

# ---------------------------------------------------------------------------
# Conversations (original tests preserved)
# ---------------------------------------------------------------------------

def test_create_conversation(tmp_db):
    conv_id = tmp_db.store.create_conversation("Test")
    assert conv_id is not None
    conv = tmp_db.store.get_conversation(conv_id["id"])
    assert conv is not None


def test_add_and_get_messages(tmp_db):
    conv_id = tmp_db.ensure_conversation(None)
    tmp_db.add_message(conv_id, "user", "Hello")
    tmp_db.add_message(conv_id, "assistant", "Hi there")
    msgs = tmp_db.get_history(conv_id)
    assert len(msgs) == 2
    assert msgs[0]["content"] == "Hello"


def test_memory_set_and_get(tmp_db):
    tmp_db.remember("key", "value")
    assert tmp_db.recall("key")[0]["value"] == "value"
    tmp_db.forget("key")
    assert tmp_db.recall("key") == []


# ---------------------------------------------------------------------------
# Secret filter
# ---------------------------------------------------------------------------

def test_scan_clean_text_returns_empty():
    assert scan_for_secrets("hello world") == []


def test_scan_detects_api_key_pattern():
    assert contains_secret("my key is sk-1234567890abcdefghij")


def test_scan_detects_google_api_key():
    assert contains_secret("AIzaSyD-1234567890abcdefghijklmnop")


def test_scan_detects_jwt_token():
    assert contains_secret("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0In0.abcdef")


def test_scan_detects_private_key():
    assert contains_secret("-----BEGIN RSA PRIVATE KEY-----\nMIIBogIBAAJBALRi...")


def test_scan_detects_bearer_token():
    assert contains_secret("Authorization: Bearer abcdef1234567890")


def test_scan_detects_password_assignment():
    assert contains_secret("password = mySecret123")


def test_scan_detects_api_key_assignment():
    assert contains_secret("api_key: abcdef1234567890")


def test_scan_benign_password_mentions_allowed():
    assert not contains_secret("I forgot my password")
    assert not contains_secret("change my password")
    assert not contains_secret("remember to change my password")
    assert not contains_secret("password manager")


def test_filter_memory_text_blocks_secrets():
    safe, saved = filter_memory_text("my token is ghp_1234567890abcdefghij")
    assert saved is False
    assert safe == ""


def test_filter_memory_text_allows_clean():
    safe, saved = filter_memory_text("my favorite color is blue")
    assert saved is True
    assert safe == "my favorite color is blue"


# ---------------------------------------------------------------------------
# Memory categories
# ---------------------------------------------------------------------------

def test_normalize_category_known():
    assert normalize_category("preferences") == "preferences"
    assert normalize_category("PROJECTS") == "projects"


def test_normalize_category_unknown_falls_back():
    assert normalize_category("unknown_category") == "general"
    assert normalize_category(None) == "general"


# ---------------------------------------------------------------------------
# MemoryManager integration
# ---------------------------------------------------------------------------

def test_remember_stores_memory(tmp_db):
    mem = tmp_db.remember("key1", "value1", category="preferences")
    assert mem["value"] == "value1"
    assert mem["category"] == "preferences"


def test_recall_returns_memories(tmp_db):
    tmp_db.remember("key1", "value1")
    results = tmp_db.recall("key1")
    assert len(results) == 1
    assert results[0]["value"] == "value1"


def test_forget_removes_memory(tmp_db):
    tmp_db.remember("key1", "value1")
    count = tmp_db.forget("key1")
    assert count == 1
    assert tmp_db.recall("key1") == []


def test_remember_refuses_secrets(tmp_db):
    with pytest.raises(SecretMemoryError):
        tmp_db.remember("api_key", "sk-1234567890abcdefghij")


def test_remember_refuses_passwords(tmp_db):
    with pytest.raises(SecretMemoryError):
        tmp_db.remember("pwd", "password = secret123")


def test_remember_refuses_jwt(tmp_db):
    with pytest.raises(SecretMemoryError):
        tmp_db.remember("token", "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0In0.abcdef")


def test_get_all_memories(tmp_db):
    tmp_db.remember("a", "1")
    tmp_db.remember("b", "2")
    all_mem = tmp_db.get_all_memories()
    assert len(all_mem) == 2


def test_delete_memory_by_id(tmp_db):
    mem = tmp_db.remember("a", "1")
    assert tmp_db.delete_memory_by_id(mem["id"]) is True
    assert tmp_db.get_memory_by_id(mem["id"]) is None


def test_clear_all_memories(tmp_db):
    tmp_db.remember("a", "1")
    tmp_db.remember("b", "2")
    count = tmp_db.clear_all_memories()
    assert count == 2
    assert tmp_db.get_all_memories() == []


def test_retrieve_relevant_returns_limited(tmp_db):
    for i in range(20):
        tmp_db.remember(f"key{i}", f"value{i}")
    results = tmp_db.retrieve_relevant("value", limit=5)
    assert len(results) <= 5


# ---------------------------------------------------------------------------
# Phase 6: Advanced Memory
# ---------------------------------------------------------------------------


def test_memory_confidence_and_source(tmp_db):
    mem = tmp_db.remember("pref", "dark theme", category="preferences", confidence=0.96, source="explicit_user")
    assert mem["confidence"] == 0.96
    assert mem["source"] == "explicit_user"


def test_memory_profile(tmp_db):
    tmp_db.remember("voice", "male", category="preferences", profile="jarvis")
    tmp_db.remember("voice", "female", category="preferences", profile="alya")
    jarvis = tmp_db.store.recall("", category="preferences", profile="jarvis")
    alya = tmp_db.store.recall("", category="preferences", profile="alya")
    assert len(jarvis) == 1
    assert len(alya) == 1
    assert jarvis[0]["value"] == "male"
    assert alya[0]["value"] == "female"


def test_memory_project_filter(tmp_db):
    tmp_db.remember("proj1", "backend uses FastAPI", category="projects", project="Jarvis2.0")
    tmp_db.remember("proj2", "frontend uses React", category="projects", project="Jarvis2.0")
    tmp_db.remember("proj3", "ecommerce uses Django", category="projects", project="Ecommerce")
    results = tmp_db.store.recall(category="projects", project="Jarvis2.0")
    assert len(results) == 2


def test_memory_update_confidence(tmp_db):
    mem = tmp_db.remember("old", "old value", confidence=0.5)
    tmp_db.store.update_memory(mem["id"], "new value", confidence=0.9)
    updated = tmp_db.store.get_memory_by_id(mem["id"])
    assert updated["value"] == "new value"
    assert updated["confidence"] == 0.9


def test_memory_recall_with_filters(tmp_db):
    tmp_db.remember("a", "1", category="preferences", profile="jarvis")
    tmp_db.remember("b", "2", category="preferences", profile="alya")
    tmp_db.remember("c", "3", category="projects", profile="jarvis")
    results = tmp_db.store.recall(category="preferences", profile="jarvis")
    assert len(results) == 1
    assert results[0]["key"] == "a"


def test_conversation_summaries(tmp_db):
    conv_id = tmp_db.ensure_conversation(None)
    summary = tmp_db.store.add_conversation_summary(conv_id, "User discussed Phase 6", 10)
    assert summary["summary"] == "User discussed Phase 6"
    summaries = tmp_db.store.get_conversation_summaries(conv_id)
    assert len(summaries) == 1
    assert summaries[0]["message_count"] == 10


def test_reminders_crud(tmp_db):
    reminder = tmp_db.store.add_reminder("Test reminder", "Description", "2026-08-17T10:00:00", "once")
    assert reminder["title"] == "Test reminder"
    assert reminder["enabled"] is True
    all_reminders = tmp_db.store.get_reminders()
    assert len(all_reminders) == 1
    updated = tmp_db.store.update_reminder(reminder["id"], {"enabled": 0})
    assert updated is True
    deleted = tmp_db.store.delete_reminder(reminder["id"])
    assert deleted is True
    assert tmp_db.store.get_reminders() == []


def test_memory_feedback(tmp_db):
    mem = tmp_db.remember("fb", "test")
    feedback = tmp_db.store.add_memory_feedback(mem["id"], None, "up", "useful")
    assert feedback["feedback"] == "up"
    all_feedback = tmp_db.store.get_memory_feedback()
    assert len(all_feedback) == 1


def test_privacy_settings(tmp_db):
    tmp_db.store.set_privacy_setting("privacy_mode", "private")
    mode = tmp_db.store.get_privacy_setting("privacy_mode")
    assert mode == "private"
    all_settings = tmp_db.store.get_all_privacy_settings()
    assert all_settings["privacy_mode"] == "private"


def test_memory_cleanup_retention(tmp_db):
    for i in range(5):
        tmp_db.remember(f"expire{i}", f"value{i}", expires_at="2000-01-01T00:00:00")
    tmp_db.remember("keep", "keep")
    from memory.cleanup import MemoryCleanup
    cleanup = MemoryCleanup(tmp_db)
    count = cleanup.cleanup_expired_memories()
    assert count == 5
    remaining = tmp_db.store.recall("keep")
    assert len(remaining) == 1


def test_short_term_memory_ttl():
    from memory.short_term import ShortTermMemory
    stm = ShortTermMemory(ttl_seconds=0.1, max_items=10)
    stm.set("key", "value")
    assert stm.get("key") == "value"
    import time
    time.sleep(0.2)
    assert stm.get("key") is None


def test_long_term_memory_wrapper(tmp_db):
    from memory.long_term import LongTermMemory
    ltm = LongTermMemory(tmp_db)
    mem = ltm.remember("wrapped", "value", category="preferences")
    assert mem["category"] == "preferences"
    results = ltm.recall("wrapped")
    assert len(results) == 1


def test_preferences_memory(tmp_db):
    from memory.preferences import PreferencesMemory
    prefs = PreferencesMemory(tmp_db)
    prefs.set("theme", "dark", profile="jarvis")
    prefs.set("theme", "light", profile="alya")
    assert prefs.get("theme", profile="jarvis") == "dark"
    assert prefs.get("theme", profile="alya") == "light"
    all_prefs = prefs.get_all(profile="jarvis")
    assert len(all_prefs) == 1


def test_project_memory(tmp_db):
    from memory.projects import ProjectMemory
    proj_mem = ProjectMemory(tmp_db)
    proj_mem.remember("Jarvis2.0", "Backend uses FastAPI")
    proj_mem.remember("Jarvis2.0", "Frontend uses React")
    results = proj_mem.recall("Jarvis2.0")
    assert len(results) == 2
    projects = proj_mem.list_projects()
    assert "Jarvis2.0" in projects


def test_task_memory(tmp_db):
    from memory.tasks import TaskMemory
    task_mem = TaskMemory(tmp_db)
    task_mem.remember("task-1", "WebSocket failed", category="tasks")
    results = task_mem.recall("task-1")
    assert len(results) == 1


def test_semantic_memory(tmp_db):
    from memory.semantic import SemanticMemory
    sem = SemanticMemory(tmp_db, None)
    assert not sem.is_available()
    results = sem.search("test")
    assert isinstance(results, list)


def test_normalize_category_phase6():
    from memory.manager import normalize_category
    assert normalize_category("USER_PREFERENCE") == "user_preference"
    assert normalize_category("PROJECT") == "project"
    assert normalize_category("UNKNOWN") == "general"
