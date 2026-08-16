"""Memory service for JARVIS Phase 6."""

from __future__ import annotations

from memory.manager import MemoryManager


class MemoryService:
    def __init__(self, memory: MemoryManager):
        self.memory = memory

    def get_conversations(self, limit: int = 50):
        return self.memory.get_conversations(limit)

    def get_messages(self, conv_id: str, limit: int = 100):
        return self.memory.get_messages(conv_id, limit)

    def delete_conversation(self, conv_id: str):
        self.memory.delete_conversation(conv_id)

    def get_all_memories(self, category: str | None = None, project: str | None = None, profile: str | None = None):
        return self.memory.get_all_memories(category=category, project=project, profile=profile)

    def get_memory_by_id(self, memory_id: str):
        return self.memory.get_memory_by_id(memory_id)

    def remember(self, content: str, category: str = "general"):
        return self.memory.remember(content, category=category)

    def forget(self, key: str):
        self.memory.forget(key)

    def delete_by_id(self, memory_id: str) -> bool:
        return self.memory.delete_memory_by_id(memory_id)

    def clear_all(self) -> int:
        return self.memory.clear_all_memories()

    def get_stats(self) -> dict:
        return self.memory.get_memory_stats()

    def categories(self):
        from memory.manager import MEMORY_CATEGORIES
        return list(MEMORY_CATEGORIES)

    def retrieve_relevant(self, query: str, limit: int = 5):
        return self.memory.retrieve_relevant(query, limit)

    def search(self, query: str, category: str | None = None, project: str | None = None, profile: str | None = None, min_confidence: float = 0.0, limit: int = 20):
        return self.memory.store.recall(query=query, category=category, project=project, profile=profile, min_confidence=min_confidence, limit=limit)

    def get_preferences(self, profile: str = "jarvis"):
        return self.memory.preferences.get_all(profile=profile)

    def set_preference(self, key: str, value: str, profile: str = "jarvis"):
        return self.memory.preferences.set(key, value, profile=profile)

    def get_projects(self):
        return self.memory.projects.list_projects()

    def get_project_memory(self, project: str, query: str = "", limit: int = 50):
        return self.memory.projects.recall(project, query=query, limit=limit)

    def get_summaries(self, conversation_id: str | None = None, limit: int = 50):
        return self.memory.summaries.get(conversation_id, limit)

    def create_summary(self, conversation_id: str, summary: str, message_count: int = 0):
        return self.memory.summaries.create(conversation_id, summary, message_count)

    def get_reminders(self, enabled: bool | None = None):
        return self.memory.reminders.get(enabled)

    def create_reminder(self, title: str, description: str = "", due_at: str = "", repeat: str = "once"):
        return self.memory.reminders.create(title, description, due_at, repeat)

    def update_reminder(self, reminder_id: str, updates: dict):
        return self.memory.reminders.update(reminder_id, updates)

    def delete_reminder(self, reminder_id: str):
        return self.memory.reminders.delete(reminder_id)

    def get_privacy_mode(self):
        return self.memory.privacy.get_mode()

    def set_privacy_mode(self, mode: str):
        self.memory.privacy.set_mode(mode)

    def get_privacy_settings(self):
        return self.memory.privacy.get_all_settings()

    def cleanup_expired(self):
        return self.memory.store._now()
