"""Memory manager: unified interface for all memory subsystems."""

from __future__ import annotations

import logging
from typing import Any

from memory.adaptive import AdaptiveMemory
from memory.audit import MemoryAuditLog
from memory.backup import MemoryBackup
from memory.cache import MemoryCache
from memory.context_builder import ContextBuilder
from memory.contradictions import ContradictionDetector
from memory.decay import MemoryDecay
from memory.duplicates import DuplicateDetector
from memory.environment import EnvironmentProfiler, environment_profiler
from memory.errors import ErrorMemory
from memory.extractor import MemoryExtractor
from memory.health import MemoryHealth
from memory.ideas import IdeasSystem
from memory.knowledge_graph import KnowledgeGraph
from memory.long_term import LongTermMemory
from memory.preferences import PreferencesMemory
from memory.privacy import PrivacyController
from memory.projects import ProjectMemory
from memory.ranker import MemoryRanker
from memory.reminders import ReminderManager
from memory.short_term import ShortTermMemory
from memory.summaries import ConversationSummaries
from memory.tasks import TaskMemory
from memory.types import ErrorCategory, IdeaStatus, MemoryImportance, MemorySource, PrivacyLevel, TrustLevel, normalize_memory_type
from memory.workflows import WorkflowDetector, SuggestionEngine, workflow_detector, suggestion_engine

logger = logging.getLogger("jarvis.memory.manager")

MEMORY_CATEGORIES: tuple[str, ...] = (
    "preferences",
    "projects",
    "instructions",
    "conversation_context",
    "general",
    "tasks",
    "workflow",
    "skill",
    "device",
    "non_sensitive_context",
    "conversation_summary",
    "user_preference",
    "project",
    "task",
    "device",
    "non_sensitive_context",
    "profile",
    "decision",
    "fact",
    "context",
    "research",
    "document",
    "episodic",
    "procedural",
    "coding",
    "technical",
    "ui",
    "voice",
    "assistant",
    "knowledge",
    "task_history",
    "error",
    "idea",
)


def normalize_category(category: str | None) -> str:
    """Coerce a category to a known one, falling back to 'general'."""
    cat = (category or "general").strip().lower()
    return cat if cat in MEMORY_CATEGORIES else "general"



class SecretMemoryError(Exception):
    pass


class MemoryManager:
    def __init__(self, db_path: str = "data/jarvis.db", vector_dir: str | None = None):
        self.store = __import__("memory.sqlite_memory", fromlist=["SQLiteMemory"]).SQLiteMemory(db_path)
        self._vector = None
        if vector_dir:
            index = __import__("memory.vector_memory", fromlist=["VectorMemory"]).VectorMemory(persist_directory=vector_dir)
            if index.available():
                self._vector = index
        self._current_conv: str | None = None

        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(self)
        self.preferences = PreferencesMemory(self)
        self.projects = ProjectMemory(self)
        self.tasks = TaskMemory(self)
        self.summaries = ConversationSummaries(self)
        self.privacy = PrivacyController(self)
        self.reminders = ReminderManager(self)
        self.semantic = __import__("memory.semantic", fromlist=["SemanticMemory"]).SemanticMemory(self, self._vector)
        self.ranker = MemoryRanker(self.store)
        self.decay = MemoryDecay(self.store)
        self.duplicates = DuplicateDetector(self.store)
        self.contradictions = ContradictionDetector(self.store)
        self.context_builder = ContextBuilder(self)
        self.knowledge_graph = KnowledgeGraph(self.store)
        self.extractor = MemoryExtractor(self, None)
        self.health = MemoryHealth(self.store)
        self.backup = MemoryBackup(self.store)
        self.audit = MemoryAuditLog(self.store.db_path)
        self.adaptive = AdaptiveMemory(self)
        self.ideas = IdeasSystem(self)
        self.errors = ErrorMemory(self)
        self.cache = MemoryCache()
        self.migrator = __import__("memory.migrator", fromlist=["MemoryMigrator"]).MemoryMigrator(self.store)

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

    def remember(self, key: str, value: str = "", category: str | None = None, confidence: float = 1.0, source: str = "explicit_user", project: str = "", profile: str = "jarvis", expires_at: str | None = None, importance: float = 0.5, tags: list[str] | None = None, memory_type: str = "fact", related_ids: list[str] | None = None, key_override: str = "", privacy_level: str = "normal", is_pinned: bool = False, trust_level: str = "normal", quality_score: float = 0.5) -> dict:
        from memory.secret_filter import contains_secret
        content = value if value else key
        if contains_secret(key) or contains_secret(content):
            raise SecretMemoryError("Refusing to store secret material in memory.")
        mem = self.store.remember(
            content,
            category=normalize_category(category),
            key_override=key_override if key_override else (key if value else ""),
            confidence=confidence,
            source=source,
            project=project,
            profile=profile,
            expires_at=expires_at,
            importance=importance,
            tags=tags,
            memory_type=memory_type,
            related_ids=related_ids,
            privacy_level=privacy_level,
            is_pinned=is_pinned,
            trust_level=trust_level,
            quality_score=quality_score,
        )
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

    def recall(self, query: str = "", category: str | None = None, project: str | None = None, profile: str | None = None, min_confidence: float = 0.0, limit: int = 50) -> list[dict]:
        rows = self.store.recall(query=query, category=category, project=project, profile=profile, min_confidence=min_confidence, limit=limit)
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


    def get_all_memories(self, category: str | None = None, project: str | None = None, profile: str | None = None, limit: int = 100) -> list[dict]:
        return self.store.recall(category=category, project=project, profile=profile, limit=limit)

    def get_memory_by_id(self, memory_id: str) -> dict | None:
        return self.store.get_memory_by_id(memory_id)

    def delete_memory_by_id(self, memory_id: str) -> bool:
        removed = self.store.delete_memory_by_id(memory_id)
        if removed and self._vector is not None:
            import contextlib
            with contextlib.suppress(Exception):
                self._vector.remove(memory_id)
        return removed

    def get_memory_stats(self) -> dict:
        return self.store.get_memory_stats()

    def retrieve_relevant(self, query: str, limit: int = 5) -> list[dict]:
        if not query:
            return []
        return self.recall(query)[:limit]

    def get_memories_for_context(self, query: str, project: str | None = None, profile: str = "jarvis", limit: int = 8) -> list[dict]:
        return self.store.get_memories_for_context(query, project=project, profile=profile, limit=limit)

    def search_with_ranking(self, query: str = "", category: str | None = None, project: str | None = None, profile: str | None = None, min_confidence: float = 0.0, limit: int = 50) -> list[dict]:
        return self.store.search_with_ranking(query=query, category=category, project=project, profile=profile, min_confidence=min_confidence, limit=limit)

    def increment_access(self, memory_id: str) -> None:
        self.store.increment_access(memory_id)

    def update_memory_fields(self, memory_id: str, updates: dict) -> dict | None:
        return self.store.update_memory_fields(memory_id, updates)

    def detect_duplicates(self, threshold: float = 0.85) -> list[dict]:
        return self.store.detect_duplicates(threshold=threshold)

    def merge_duplicates(self, primary_id: str, secondary_id: str) -> dict | None:
        return self.store.duplicates.merge(primary_id, secondary_id)

    def detect_contradictions(self) -> list[dict]:
        return self.store.detect_contradictions()

    def apply_decay(self, decay_rate: float = 0.01) -> int:
        return self.store.apply_decay(decay_rate=decay_rate)

    def get_health(self) -> dict:
        return self.health.check()

    def export_memories(self, category: str | None = None, project: str | None = None, profile: str | None = None) -> dict:
        return self.backup.export(category=category, project=project, profile=profile)

    def import_memories(self, data: dict, mode: str = "merge") -> dict:
        return self.backup.import_(data, mode=mode)

    def get_related_memories(self, memory_id: str, limit: int = 10) -> list[dict]:
        return self.store.get_related_memories(memory_id, limit=limit)

    def build_context(self, user_message: str, project: str | None = None, profile: str = "jarvis", max_memories: int = 8, max_tokens: int = 2000, task_type: str | None = None) -> dict:
        return self.context_builder.build(user_message, project=project, profile=profile, max_memories=max_memories, max_tokens=max_tokens, task_type=task_type)

    def remember_with_confirmation(self, content: str, category: str | None = None, importance: str = MemoryImportance.MEDIUM.value, memory_type: str | None = None, **kwargs) -> dict:
        normalized_type = normalize_memory_type(memory_type or category)
        return self.remember(
            content,
            category=normalized_type,
            memory_type=normalized_type,
            importance=self._importance_to_float(importance),
            source=kwargs.get("source", MemorySource.EXPLICIT_USER.value),
            project=kwargs.get("project", ""),
            profile=kwargs.get("profile", "jarvis"),
            expires_at=kwargs.get("expires_at"),
            tags=kwargs.get("tags"),
            related_ids=kwargs.get("related_ids"),
        )

    def remember_session(self, session_id: str, content: str, category: str = "general", memory_type: str = "fact", importance: float = 0.5, expires_at: str | None = None) -> dict:
        return self.store.remember_session(session_id, content, category=category, memory_type=memory_type, importance=importance, expires_at=expires_at)

    def get_session_memories(self, session_id: str, limit: int = 50) -> list[dict]:
        return self.store.get_session_memories(session_id, limit=limit)

    def clear_session_memories(self, session_id: str) -> int:
        return self.store.clear_session_memories(session_id)

    def get_memory_dashboard(self) -> dict:
        stats = self.get_memory_stats()
        rows = self.store.recall(limit=500)
        by_category: dict[str, int] = {}
        by_type: dict[str, int] = {}
        by_importance: dict[str, int] = {}
        recent = []
        for row in rows:
            cat = row.get("category") or "general"
            mem_type = row.get("memory_type") or "fact"
            imp = row.get("importance") or 0.5
            by_category[cat] = by_category.get(cat, 0) + 1
            by_type[mem_type] = by_type.get(mem_type, 0) + 1
            if imp >= 0.8:
                by_importance["high"] = by_importance.get("high", 0) + 1
            elif imp >= 0.4:
                by_importance["medium"] = by_importance.get("medium", 0) + 1
            else:
                by_importance["low"] = by_importance.get("low", 0) + 1
            if len(recent) < 10:
                recent.append({
                    "id": row.get("id"),
                    "content": (row.get("value") or row.get("key") or "")[:80],
                    "category": cat,
                    "memory_type": mem_type,
                    "importance": imp,
                    "created_at": row.get("created_at"),
                })
        health = self.health.check() if hasattr(self, "health") else {}
        return {
            "total_memories": stats.get("count", 0),
            "storage_bytes": stats.get("size_bytes", 0),
            "by_category": by_category,
            "by_type": by_type,
            "by_importance": by_importance,
            "recent": recent,
            "health": health,
        }

    def resolve_conflict(self, memory_id: str, keep: bool = True) -> dict | None:
        memory = self.get_memory_by_id(memory_id)
        if not memory:
            return None
        if keep:
            self.update_memory_fields(memory_id, {"importance": max(float(memory.get("importance") or 0.5), 0.8)})
        return self.get_memory_by_id(memory_id)

    def _importance_to_float(self, importance: str) -> float:
        mapping = {MemoryImportance.LOW.value: 0.2, MemoryImportance.MEDIUM.value: 0.5, MemoryImportance.HIGH.value: 0.9}
        return mapping.get(importance, 0.5)

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
        return self.adaptive.remember_preference(
            key=key,
            value=value,
            source=source,
            confidence=confidence,
            profile=profile,
            project=project,
            session_id=session_id,
            metadata=metadata,
        ).to_dict()

    def get_adaptive_preferences(self, profile: str = "jarvis", project: str = "", session_id: str = "") -> list[dict]:
        return self.adaptive.get_all_preferences(profile=profile, project=project, session_id=session_id)

    def forget_adaptive_preference(self, preference_id: str) -> bool:
        return self.adaptive.forget_preference(preference_id)

    def forget_adaptive_key(self, key: str, profile: str = "jarvis") -> int:
        return self.adaptive.forget_key(key, profile=profile)

    def get_personalization_context(self, profile: str = "jarvis", project: str = "", session_id: str = "") -> dict:
        return self.adaptive.get_personalization_context(profile=profile, project=project, session_id=session_id)

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
        self.adaptive.record_task_outcome(
            task_type=task_type,
            agents_used=agents_used,
            tools_used=tools_used,
            duration_ms=duration_ms,
            success=success,
            user_feedback=user_feedback,
            retry_count=retry_count,
            provider=provider,
        )

    def get_provider_preference(self, task_type: str) -> str | None:
        return self.adaptive.get_provider_preference(task_type)

    def get_latency_preference(self, task_type: str) -> dict | None:
        return self.adaptive.get_latency_preference(task_type)

    def get_suggestions(self, profile: str = "jarvis") -> list[dict]:
        return suggestion_engine.generate_suggestions(profile=profile)

    def export_personalization(self, profile: str = "jarvis") -> dict:
        return self.adaptive.export_preferences(profile=profile)

    def import_personalization(self, data: dict, profile: str = "jarvis") -> int:
        return self.adaptive.import_preferences(data, profile=profile)

    # ---------------------------------------------------------------- ideas (Phase 29)
    def create_idea(self, title: str, description: str = "", tags: list[str] | None = None, status: str = "idea", project: str = "", profile: str = "jarvis") -> dict:
        return self.ideas.create_idea(title=title, description=description, tags=tags, status=status, project=project, profile=profile)

    def get_ideas(self, status: str | None = None, project: str | None = None, profile: str | None = None, limit: int = 50) -> list[dict]:
        return self.ideas.get_ideas(status=status, project=project, profile=profile, limit=limit)

    def update_idea(self, idea_id: str, updates: dict) -> dict | None:
        return self.ideas.update_idea(idea_id, updates)

    def delete_idea(self, idea_id: str) -> bool:
        return self.ideas.delete_idea(idea_id)

    def get_idea_by_id(self, idea_id: str) -> dict | None:
        return self.ideas.get_idea_by_id(idea_id)

    # ---------------------------------------------------------------- error memory (Phase 29)
    def record_error(self, error_signature: str, resolution: str, category: str = "other", project: str = "", profile: str = "jarvis", confidence: float = 1.0) -> dict:
        return self.errors.record_error(error_signature=error_signature, resolution=resolution, category=category, project=project, profile=profile, confidence=confidence)

    def find_error_resolution(self, error_signature: str, limit: int = 5) -> list[dict]:
        return self.errors.find_resolution(error_signature, limit=limit)

    def get_errors(self, project: str | None = None, category: str | None = None, profile: str | None = None, limit: int = 50) -> list[dict]:
        return self.errors.get_errors(project=project, category=category, profile=profile, limit=limit)

    def delete_error(self, error_id: str) -> bool:
        return self.errors.delete_error(error_id)

    # ---------------------------------------------------------------- cache (Phase 29)
    def cache_get(self, key: str) -> dict | None:
        return self.cache.get(key)

    def cache_set(self, key: str, value: Any, ttl: float | None = None) -> None:
        self.cache.set(key, value, ttl=ttl)

    def cache_invalidate(self, key: str | None = None) -> None:
        self.cache.invalidate(key)

    # ---------------------------------------------------------------- migration (Phase 29)
    def run_migration(self) -> dict:
        return self.migrator.migrate()

    # ---------------------------------------------------------------- pin / trust / privacy (Phase 29)
    def pin_memory(self, memory_id: str) -> dict | None:
        return self.update_memory_fields(memory_id, {"is_pinned": True})

    def unpin_memory(self, memory_id: str) -> dict | None:
        return self.update_memory_fields(memory_id, {"is_pinned": False})

    def set_trust_level(self, memory_id: str, trust_level: str) -> dict | None:
        return self.update_memory_fields(memory_id, {"trust_level": trust_level})

    def set_privacy_level(self, memory_id: str, privacy_level: str) -> dict | None:
        return self.update_memory_fields(memory_id, {"privacy_level": privacy_level})

    def set_quality_score(self, memory_id: str, quality_score: float) -> dict | None:
        return self.update_memory_fields(memory_id, {"quality_score": quality_score})
