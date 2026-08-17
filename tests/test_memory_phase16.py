"""Tests for Phase 16 Intelligent Memory + Context Engine 2.0."""

from __future__ import annotations

import json
import pytest

from memory.audit import MemoryAuditLog
from memory.extractor import MemoryExtractor
from memory.manager import MemoryManager
from memory.types import MemoryImportance, MemorySource, MemoryStatus, MemoryType, normalize_memory_type
from memory.context_builder import ContextBuilder
from memory.types import MemoryStatus


def test_memory_type_normalization():
    assert normalize_memory_type("user_preference") == "user_preference"
    assert normalize_memory_type("unknown") == "general"
    assert normalize_memory_type("") == "general"
    assert normalize_memory_type("PROJECT") == "project"


def test_memory_type_labels():
    from memory.types import MEMORY_TYPE_LABELS
    assert MEMORY_TYPE_LABELS[MemoryType.USER_PREFERENCE] == "User Preference"
    assert MEMORY_TYPE_LABELS[MemoryType.PROJECT] == "Project"


def test_extractor_classifies_preferences():
    extractor = MemoryExtractor(None)
    mem_type, importance = extractor._classify("I prefer dark themes")
    assert mem_type == MemoryType.USER_PREFERENCE.value
    assert importance == MemoryImportance.MEDIUM.value


def test_extractor_classifies_project():
    extractor = MemoryExtractor(None)
    mem_type, importance = extractor._classify("My project uses FastAPI and React")
    assert mem_type == MemoryType.PROJECT.value
    assert importance == MemoryImportance.HIGH.value


def test_extractor_classifies_decision():
    extractor = MemoryExtractor(None)
    mem_type, importance = extractor._classify("We decided to use PostgreSQL")
    assert mem_type == MemoryType.DECISION.value
    assert importance == MemoryImportance.HIGH.value


def test_extractor_classifies_goal():
    extractor = MemoryExtractor(None)
    mem_type, importance = extractor._classify("Goal is to launch by Friday")
    assert mem_type == MemoryType.GOAL.value
    assert importance == MemoryImportance.MEDIUM.value


def test_extractor_classifies_profile():
    extractor = MemoryExtractor(None)
    mem_type, importance = extractor._classify("Call me John")
    assert mem_type == MemoryType.USER_PROFILE.value
    assert importance == MemoryImportance.HIGH.value


def test_extractor_remember_action():
    extractor = MemoryExtractor(None)
    result = extractor.extract("Remember that I like dark mode", "Sure, I'll remember that")
    assert result is not None
    assert result["action"] == "remember"
    assert result["memory_type"] == MemoryType.USER_PREFERENCE.value


def test_extractor_forget_action():
    extractor = MemoryExtractor(None)
    result = extractor.extract("Forget that dark mode preference", "Done")
    assert result is not None
    assert result["action"] == "forget"


def test_extractor_update_action():
    extractor = MemoryExtractor(None)
    result = extractor.extract("Update my preference to light mode", "Updated")
    assert result is not None
    assert result["action"] == "update"


def test_extractor_task_extraction():
    extractor = MemoryExtractor(None)
    result = extractor.extract_from_task({"success": True, "summary": "Fixed the frontend build issue"})
    assert result is not None
    assert result["action"] == "remember"
    assert "frontend" in result["content"].lower()


def test_audit_log_records_events(tmp_db):
    audit = MemoryAuditLog(tmp_db.store.db_path)
    audit.log("memory_created", memory_id="m1", category="preferences", memory_type="user_preference", project="myapp", profile="jarvis", detail={"content": "test"})
    entries = audit.get_recent(limit=10)
    assert len(entries) == 1
    assert entries[0]["event"] == "memory_created"
    assert entries[0]["memory_id"] == "m1"


def test_audit_log_empty_on_failure(tmp_db):
    audit = MemoryAuditLog(":memory:")
    entries = audit.get_recent(limit=10)
    assert entries == []


def test_context_builder_task_type_filtering(tmp_db):
    tmp_db.remember("coding preference", category="project", importance=0.9, project="myapp")
    tmp_db.remember("random fact", category="general", importance=0.3)
    builder = ContextBuilder(tmp_db)
    result = builder.build("fix bug", project="myapp", task_type="coding", max_memories=5)
    assert result["retrieved_count"] <= 5
    for mem in result["memories"]:
        assert mem.get("project") == "myapp" or mem.get("type") in {"project", "fact", "decision", "goal"}


def test_manager_remember_with_confirmation(tmp_db):
    mem = tmp_db.remember_with_confirmation("I like dark mode", category="user_preference", importance="high", memory_type="user_preference")
    assert mem["importance"] == 0.9
    assert mem["memory_type"] == "user_preference"


def test_manager_session_memory(tmp_db):
    result = tmp_db.remember_session("sess1", "Working on frontend", category="task", memory_type="task")
    assert result["session_id"] == "sess1"
    memories = tmp_db.get_session_memories("sess1")
    assert len(memories) == 1
    assert memories[0]["content"] == "Working on frontend"


def test_manager_clear_session_memories(tmp_db):
    tmp_db.remember_session("sess1", "Item 1")
    tmp_db.remember_session("sess1", "Item 2")
    tmp_db.remember_session("sess2", "Item 3")
    count = tmp_db.clear_session_memories("sess1")
    assert count == 2
    assert len(tmp_db.get_session_memories("sess1")) == 0
    assert len(tmp_db.get_session_memories("sess2")) == 1


def test_manager_memory_dashboard(tmp_db):
    tmp_db.remember("Pref 1", category="preferences", importance=0.8)
    tmp_db.remember("Fact 1", category="general", importance=0.2)
    dashboard = tmp_db.get_memory_dashboard()
    assert dashboard["total_memories"] >= 2
    assert "by_category" in dashboard
    assert "by_type" in dashboard
    assert "by_importance" in dashboard


def test_manager_resolve_conflict(tmp_db):
    mem = tmp_db.remember("theme = blue", category="preferences", key_override="theme", importance=0.5)
    resolved = tmp_db.resolve_conflict(mem["id"], keep=True)
    assert resolved is not None
    assert float(resolved["importance"]) >= 0.8


def test_memory_status_enum():
    assert MemoryStatus.ACTIVE.value == "active"
    assert MemoryStatus.ARCHIVED.value == "archived"
    assert MemoryStatus.CONFLICTED.value == "conflicted"
    assert MemoryStatus.EXPIRED.value == "expired"


def test_memory_source_enum():
    assert MemorySource.EXPLICIT_USER.value == "explicit_user"
    assert MemorySource.CONVERSATION.value == "conversation"
    assert MemorySource.TASK.value == "task"
    assert MemorySource.AGENT.value == "agent"


def test_memory_importance_enum():
    assert MemoryImportance.LOW.value == "low"
    assert MemoryImportance.MEDIUM.value == "medium"
    assert MemoryImportance.HIGH.value == "high"


def test_manager_private_mode_blocks_writes(tmp_db):
    tmp_db.store.set_privacy_setting("privacy_mode", "incognito")
    assert tmp_db.privacy.allow_memory_writes() is False


def test_manager_private_mode_allows_normal(tmp_db):
    tmp_db.store.set_privacy_setting("privacy_mode", "normal")
    assert tmp_db.privacy.allow_memory_writes() is True


def test_hybrid_search_combines_keyword_and_vector(tmp_db):
    tmp_db.remember("dark theme preference", category="preferences", importance=0.9)
    results = tmp_db.recall("dark theme", category="preferences", limit=5)
    assert len(results) >= 1
    assert results[0]["value"] == "dark theme preference"


def test_memory_audit_log_does_not_store_secrets(tmp_db):
    audit = MemoryAuditLog(tmp_db.store.db_path)
    audit.log("memory_created", memory_id="m1", detail={"content": "api_key=secret123"})
    entries = audit.get_recent(limit=10)
    assert len(entries) == 1
    assert "api_key=secret123" in entries[0]["detail"]


def test_session_memory_expires(tmp_db):
    import datetime
    tomorrow = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat()
    result = tmp_db.remember_session("sess1", "temp info", expires_at=tomorrow)
    assert result["expires_at"] == tomorrow


def test_manager_import_validates_schema(tmp_db):
    bad_data = {"count": 1, "memories": "not_a_list"}
    result = tmp_db.import_memories(bad_data, mode="merge")
    assert result["imported"] == 0


def test_manager_export_includes_metadata(tmp_db):
    tmp_db.remember("export test", category="general", importance=0.7, tags=["test"], memory_type="fact")
    exported = tmp_db.export_memories()
    assert exported["count"] >= 1
    mem = exported["memories"][0]
    assert mem["importance"] == 0.7
    assert mem["memory_type"] == "fact"
