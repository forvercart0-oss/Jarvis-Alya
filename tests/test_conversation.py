from brain.conversation import DEFAULT_MAX_CONTEXT_CHARS, ConversationManager


def test_ensure_conversation_creates_and_reuses(tmp_db):
    manager = ConversationManager(tmp_db)
    conv_id = manager.ensure_conversation(None)
    assert conv_id is not None
    assert manager.ensure_conversation(conv_id) == conv_id


def test_ensure_conversation_with_explicit_id(tmp_db):
    manager = ConversationManager(tmp_db)
    conv = tmp_db.store.create_conversation(title="Explicit")
    assert manager.ensure_conversation(conv["id"]) == conv["id"]


def test_ensure_conversation_with_missing_id_creates(tmp_db):
    manager = ConversationManager(tmp_db)
    new_id = manager.ensure_conversation(999999)
    assert new_id != 999999
    assert tmp_db.store.get_conversation(new_id) is not None


def test_build_messages_appends_user_input(tmp_db):
    manager = ConversationManager(tmp_db)
    conv_id = manager.ensure_conversation(None)
    manager.add_message(conv_id, "user", "previous question")
    manager.add_message(conv_id, "assistant", "previous answer")

    messages = manager.build_messages(conv_id, "new question")
    assert messages[-1] == {"role": "user", "content": "new question"}
    assert any(m["content"] == "previous answer" for m in messages)


def test_build_messages_trims_context(tmp_db):
    manager = ConversationManager(tmp_db)
    conv_id = manager.ensure_conversation(None)
    for i in range(30):
        manager.add_message(conv_id, "user", f"filler message {i} " + "y" * 400)

    messages = manager.build_messages(conv_id, "final", max_messages=100, max_chars=5000)
    total = sum(len(m["content"]) for m in messages if m["role"] != "user" or m["content"] != "final")
    assert total <= 5000 + 500
    assert messages[-1]["content"] == "final"


def test_clear_history(tmp_db):
    manager = ConversationManager(tmp_db)
    conv_id = manager.ensure_conversation(None)
    manager.add_message(conv_id, "user", "hello")
    assert manager.get_history(conv_id) != []
    manager.clear_history(conv_id)
    assert manager.get_history(conv_id) == []


def test_reset_conversation(tmp_db):
    manager = ConversationManager(tmp_db)
    first = manager.ensure_conversation(None)
    manager.reset_conversation()
    second = manager.ensure_conversation(None)
    assert second != first


def test_default_context_budget_is_reasonable():
    assert 8000 <= DEFAULT_MAX_CONTEXT_CHARS <= 20000
