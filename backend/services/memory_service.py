"""Memory service for JARVIS Phase 12."""

from __future__ import annotations

import logging
from typing import Any

from memory.manager import MemoryManager

logger = logging.getLogger("jarvis.services.memory")


class MemoryService:
    def __init__(self, memory: MemoryManager, ws_broadcast: Any | None = None):
        self.memory = memory
        self._ws = ws_broadcast

    def _broadcast(self, event: str, data: dict) -> None:
        if self._ws:
            try:
                import asyncio
                asyncio.get_event_loop().run_until_complete(self._ws(event, data))
            except Exception:
                pass

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

    def remember(self, content: str, category: str = "general", **kwargs):
        result = self.memory.remember(content, category=category, **kwargs)
        self._broadcast("memory_created", result)
        return result

    def forget(self, key: str):
        self.memory.forget(key)

    def delete_by_id(self, memory_id: str) -> bool:
        result = self.memory.delete_memory_by_id(memory_id)
        if result:
            self._broadcast("memory_deleted", {"memory_id": memory_id})
        return result

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

    def remember_adaptive_preference(
        self,
        key: str,
        value: str,
        source: str = "explicit_user",
        confidence: str = "high",
        profile: str = "jarvis",
        project: str = "",
        session_id: str = "",
        metadata: dict | None = None,
    ) -> dict:
        result = self.memory.remember_adaptive_preference(
            key=key,
            value=value,
            source=source,
            confidence=confidence,
            profile=profile,
            project=project,
            session_id=session_id,
            metadata=metadata,
        )
        self._broadcast("preference_learned", result)
        return result

    def get_adaptive_preferences(self, profile: str = "jarvis", project: str = "", session_id: str = "") -> list[dict]:
        return self.memory.get_adaptive_preferences(profile=profile, project=project, session_id=session_id)

    def forget_adaptive_preference(self, preference_id: str) -> bool:
        ok = self.memory.forget_adaptive_preference(preference_id)
        if ok:
            self._broadcast("preference_deleted", {"preference_id": preference_id})
        return ok

    def forget_adaptive_key(self, key: str, profile: str = "jarvis") -> int:
        count = self.memory.forget_adaptive_key(key, profile=profile)
        if count:
            self._broadcast("preference_deleted", {"key": key, "count": count})
        return count

    def get_personalization_context(self, profile: str = "jarvis", project: str = "", session_id: str = "") -> dict:
        return self.memory.get_personalization_context(profile=profile, project=project, session_id=session_id)

    def get_suggestions(self, profile: str = "jarvis") -> list[dict]:
        return self.memory.get_suggestions(profile=profile)

    def record_task_outcome(
        self,
        task_type: str,
        agents_used: list[str],
        tools_used: list[str],
        duration_ms: int,
        success: bool,
        user_feedback: str = "",
        retry_count: int = 0,
        provider: str = "",
    ) -> None:
        self.memory.record_task_outcome(
            task_type=task_type,
            agents_used=agents_used,
            tools_used=tools_used,
            duration_ms=duration_ms,
            success=success,
            user_feedback=user_feedback,
            retry_count=retry_count,
            provider=provider,
        )

    def export_personalization(self, profile: str = "jarvis") -> dict:
        return self.memory.export_personalization(profile=profile)

    def import_personalization(self, data: dict, profile: str = "jarvis") -> int:
        return self.memory.import_personalization(data, profile=profile)

    def get_provider_preference(self, task_type: str) -> str | None:
        return self.memory.get_provider_preference(task_type)

    def get_latency_preference(self, task_type: str) -> dict | None:
        return self.memory.get_latency_preference(task_type)

    def get_environment_profile(self) -> dict:
        from memory.environment import environment_profiler
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            profile = loop.run_until_complete(environment_profiler.get_profile())
            return profile.to_dict()
        except Exception:
            return environment_profiler.get_profile().to_dict()

    def get_analytics(self, profile: str = "jarvis") -> dict:
        outcomes = self.memory.adaptive._task_outcomes if hasattr(self.memory, 'adaptive') else []
        total = len(outcomes)
        successes = sum(1 for o in outcomes if o.get("success"))
        providers: dict[str, int] = {}
        tools: dict[str, int] = {}
        agents: dict[str, int] = {}
        for o in outcomes:
            p = o.get("provider")
            if p:
                providers[p] = providers.get(p, 0) + 1
            for t in o.get("tools_used", []):
                tools[t] = tools.get(t, 0) + 1
            for a in o.get("agents_used", []):
                agents[a] = agents.get(a, 0) + 1
        return {
            "tasks_completed": total,
            "tasks_failed": total - successes,
            "success_rate": successes / total if total else 0,
            "sample_size": total,
            "profile": profile,
            "providers": providers,
            "tools": tools,
            "agents": agents,
        }
