from __future__ import annotations

from typing import Optional

from memory.sqlite_memory import SQLiteMemory
from memory.store import SemanticIndex
from memory.vector_memory import VectorMemory


class MemoryManager:
    def __init__(self, db_path: str = "data/jarvis.db", vector_dir: Optional[str] = None):
        self.store = SQLiteMemory(db_path)
        self._vector: Optional[SemanticIndex] = None
        if vector_dir:
            index = VectorMemory(persist_directory=vector_dir)
            if index.available():
                self._vector = index
        self._current_conv: Optional[str] = None

    @property
    def vector_enabled(self) -> bool:
        return self._vector is not None

    def ensure_conversation(self, conv_id) -> str:
        if conv_id is None:
            if self._current_conv is not None:
                return self._current_conv
            self._current_conv = None
            conv = self.store.create_conversation()
            self._current_conv = conv["id"]
            return conv["id"]
        if isinstance(conv_id, int):
            conv_id = str(conv_id)
        existing = self.store.get_conversation(conv_id)
        if existing:
            self._current_conv = conv_id
            return conv_id
        conv = self.store.create_conversation()
        self._current_conv = conv["id"]
        return conv["id"]

    def add_message(self, conv_id: str, role: str, content: str) -> str:
        first_user = role == "user" and self.store.get_history(conv_id, limit=1) == []
        msg_id = self.store.add_message(conv_id, role, content)
        if first_user:
            self.store.auto_title_conversation(conv_id, content)
        return msg_id

    def build_messages(self, conv_id: str, user_message: str, max_messages: int = 100, max_chars: int = 20000) -> list[dict]:
        history = self.store.get_history(conv_id, limit=max_messages)
        messages: list[dict] = []
        total_chars = len(user_message)
        messages.append({"role": "user", "content": user_message})
        for msg in reversed(history):
            if len(messages) >= max_messages + 1:
                break
            content = msg["content"]
            if total_chars + len(content) > max_chars:
                continue
            total_chars += len(content)
            messages.insert(0, {"role": msg["role"], "content": content})
        return messages

    def get_history(self, conv_id: str) -> list[dict]:
        return self.store.get_history(conv_id)

    def get_conversations(self, limit: int = 50) -> list[dict]:
        return self.store.get_conversations(limit)

    def get_messages(self, conv_id: str, limit: int = 100) -> list[dict]:
        return self.store.get_history(conv_id, limit=limit)

    def delete_conversation(self, conv_id: str):
        self.store.delete_conversation(conv_id)

    def rename_conversation(self, conv_id: str, title: str):
        self.store.rename_conversation(conv_id, title)

    def clear_history(self, conv_id: str):
        self.store.clear_history(conv_id)

    def update_memory(self, memory_id: str, value: str) -> bool:
        updated = self.store.update_memory(memory_id, value)
        if updated and self._vector is not None:
            row = next((r for r in self.store.recall("") if r["id"] == memory_id), None)
            if row:
                self._vector.update(row["id"], row["value"], {"key": row["key"], "category": row["category"]})
        return updated

    def clear_all_memories(self) -> int:
        count = self.store.clear_all_memories()
        if self._vector is not None:
            self._vector.clear()
        return count

    def reset_conversation(self) -> str:
        self._current_conv = None
        return self.ensure_conversation(None)

    def remember(self, key: str, value: str = "") -> dict:
        if not value:
            content = key
            key = key[:64]
        else:
            content = value
        mem = self.store.remember(content, category="general", key_override=key)
        if self._vector is not None:
            self._vector.add(mem["id"], mem["value"], {"key": mem["key"], "category": mem["category"]})
        return mem

    def forget(self, query: str) -> int:
        return self._forget_synced(query)

    def forget_matching(self, query: str) -> int:
        return self._forget_synced(query)

    def _forget_synced(self, query: str) -> int:
        if self._vector is None:
            return self.store.forget(query)
        matched = self.store.recall(query)
        count = self.store.forget(query)
        for row in matched:
            self._vector.remove(row["id"])
        return count

    def recall(self, query: str = "") -> list[dict]:
        rows = self.store.recall(query)
        if not query or self._vector is None:
            return rows
        semantic = self._vector.search(query, limit=5)
        if not semantic:
            return rows
        seen = {row["id"] for row in rows}
        merged = list(rows)
        for hit in semantic:
            row = next((r for r in merged if r["id"] == hit["id"]), None)
            if row is None:
                continue
            if row["id"] not in seen:
                merged.append(row)
                seen.add(row["id"])
            row["semantic_score"] = hit.get("score")
        return merged

    def get_all_memories(self) -> list[dict]:
        return self.store.recall("")
