import pytest
from memory.sqlite_memory import SQLiteMemory
from memory.manager import MemoryManager


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
