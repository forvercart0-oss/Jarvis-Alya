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
