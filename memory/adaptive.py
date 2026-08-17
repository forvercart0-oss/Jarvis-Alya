"""Adaptive memory system for JARVIS Phase 21."""

from __future__ import annotations

import contextlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger("jarvis.memory.adaptive")


class PreferenceSource(StrEnum):
    EXPLICIT_USER = "explicit_user"
    INFERRED = "inferred"
    CORRECTION = "correction"
    WORKFLOW = "workflow"
    SYSTEM = "system"


class ConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AdaptivePreference:
    preference_id: str = ""
    key: str = ""
    value: str = ""
    source: str = PreferenceSource.EXPLICIT_USER.value
    confidence: str = ConfidenceLevel.HIGH.value
    profile: str = "jarvis"
    project: str = ""
    session_id: str = ""
    usage_count: int = 0
    last_used: float = 0.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.preference_id:
            self.preference_id = str(uuid.uuid4())[:8]
        if not self.last_used:
            self.last_used = self.created_at

    def touch(self) -> None:
        self.usage_count += 1
        self.last_used = time.time()
        self.updated_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "preference_id": self.preference_id,
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "confidence": self.confidence,
            "profile": self.profile,
            "project": self.project,
            "session_id": self.session_id,
            "usage_count": self.usage_count,
            "last_used": self.last_used,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }


class AdaptiveMemory:
    """Learns and manages user preferences with confidence and source tracking."""

    def __init__(self, memory_manager: Any | None = None):
        self._memory = memory_manager
        self._preferences: dict[str, AdaptivePreference] = {}
        self._workflows: list[dict[str, Any]] = []
        self._task_outcomes: list[dict[str, Any]] = []
        self._max_task_outcomes = 100

    def remember_preference(
        self,
        key: str,
        value: str,
        source: str = PreferenceSource.EXPLICIT_USER.value,
        confidence: str = ConfidenceLevel.HIGH.value,
        profile: str = "jarvis",
        project: str = "",
        session_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> AdaptivePreference:
        existing = None
        for pref in self._preferences.values():
            if (
                pref.key == key
                and pref.profile == profile
                and pref.project == project
                and pref.session_id == session_id
            ):
                existing = pref
                break

        if existing:
            existing.value = value
            existing.source = source
            existing.confidence = confidence
            existing.updated_at = time.time()
            if metadata:
                existing.metadata.update(metadata)
            existing.touch()
            pref = existing
        else:
            pref = AdaptivePreference(
                key=key,
                value=value,
                source=source,
                confidence=confidence,
                profile=profile,
                project=project,
                session_id=session_id,
                metadata=metadata or {},
            )
            self._preferences[pref.preference_id] = pref

        if self._memory:
            with contextlib.suppress(Exception):
                self._memory.store.remember(
                    value,
                    category="user_preference",
                    key_override=key,
                    confidence=1.0 if confidence == ConfidenceLevel.HIGH.value else 0.5,
                    source=source,
                    profile=profile,
                )

        logger.debug("Learned preference: %s=%s (%s)", key, value, confidence)
        return pref

    def get_preference(
        self, key: str, profile: str = "jarvis", project: str = "", session_id: str = ""
    ) -> AdaptivePreference | None:
        candidates = []
        for pref in self._preferences.values():
            if pref.key == key and pref.profile == profile:
                if session_id and pref.session_id == session_id:
                    candidates.append(pref)
                elif project and pref.project == project:
                    candidates.append(pref)
                elif not pref.session_id and not pref.project:
                    candidates.append(pref)
        if not candidates:
            return None
        candidates.sort(key=lambda p: {"high": 3, "medium": 2, "low": 1}.get(p.confidence, 0), reverse=True)
        return candidates[0]

    def forget_preference(self, preference_id: str) -> bool:
        pref = self._preferences.pop(preference_id, None)
        if pref:
            logger.debug("Forgot preference: %s=%s", pref.key, pref.value)
            return True
        return False

    def forget_key(self, key: str, profile: str = "jarvis") -> int:
        to_remove = [pid for pid, pref in self._preferences.items() if pref.key == key and pref.profile == profile]
        for pid in to_remove:
            self._preferences.pop(pid, None)
        return len(to_remove)

    def get_all_preferences(
        self, profile: str = "jarvis", project: str = "", session_id: str = ""
    ) -> list[dict[str, Any]]:
        prefs = []
        for pref in self._preferences.values():
            if pref.profile != profile:
                continue
            if session_id and pref.session_id == session_id:
                prefs.append(pref)
            elif project and pref.project == project:
                prefs.append(pref)
            elif not pref.session_id and not pref.project:
                prefs.append(pref)
        prefs.sort(key=lambda p: p.updated_at, reverse=True)
        return [p.to_dict() for p in prefs]

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
        outcome = {
            "task_type": task_type,
            "agents_used": agents_used,
            "tools_used": tools_used,
            "duration_ms": duration_ms,
            "success": success,
            "user_feedback": user_feedback,
            "retry_count": retry_count,
            "provider": provider,
            "timestamp": time.time(),
        }
        self._task_outcomes.append(outcome)
        if len(self._task_outcomes) > self._max_task_outcomes:
            self._task_outcomes = self._task_outcomes[-self._max_task_outcomes:]

    def get_provider_preference(self, task_type: str) -> str | None:
        if not self._task_outcomes:
            return None
        task_outcomes = [o for o in self._task_outcomes if o.get("task_type") == task_type and o.get("provider")]
        if not task_outcomes:
            return None
        successes = [o for o in task_outcomes if o.get("success")]
        if not successes:
            return None
        providers: dict[str, int] = {}
        for o in successes:
            p = o.get("provider", "")
            if p:
                providers[p] = providers.get(p, 0) + 1
        if not providers:
            return None
        return max(providers, key=providers.get)

    def get_latency_preference(self, task_type: str) -> dict[str, Any] | None:
        task_outcomes = [o for o in self._task_outcomes if o.get("task_type") == task_type and o.get("success")]
        if not task_outcomes:
            return None
        avg_duration = sum(o.get("duration_ms", 0) for o in task_outcomes) / len(task_outcomes)
        return {"task_type": task_type, "avg_duration_ms": avg_duration, "sample_size": len(task_outcomes)}

    def detect_workflow(self, task_sequence: list[str], min_repetitions: int = 3) -> dict[str, Any] | None:
        if not self._workflows:
            self._workflows = []
        workflow = {
            "id": str(uuid.uuid4())[:8],
            "steps": task_sequence,
            "repetitions": 1,
            "detected_at": time.time(),
        }
        for existing in self._workflows:
            if existing.get("steps") == task_sequence:
                existing["repetitions"] += 1
                existing["detected_at"] = time.time()
                if existing["repetitions"] >= min_repetitions:
                    return existing
                return None
        self._workflows.append(workflow)
        return None

    def get_workflows(self) -> list[dict[str, Any]]:
        return [w for w in self._workflows if w.get("repetitions", 0) >= 3]

    def forget_workflow(self, workflow_id: str) -> bool:
        for i, w in enumerate(self._workflows):
            if w.get("id") == workflow_id:
                self._workflows.pop(i)
                return True
        return False

    def get_personalization_context(
        self, profile: str = "jarvis", project: str = "", session_id: str = ""
    ) -> dict[str, Any]:
        prefs = self.get_all_preferences(profile=profile, project=project, session_id=session_id)
        context = {
            "preferences": {
                p["key"]: p["value"]
                for p in prefs
                if p.get("confidence") in ("medium", "high")
            },
            "explicit_preferences": {
                p["key"]: p["value"]
                for p in prefs
                if p.get("source") == PreferenceSource.EXPLICIT_USER.value
            },
            "workflows": self.get_workflows(),
            "provider_preferences": {},
        }
        for task_type in ["coding", "research", "summarization", "vision", "simple_chat", "classification"]:
            provider = self.get_provider_preference(task_type)
            if provider:
                context["provider_preferences"][task_type] = provider
        return context

    def export_preferences(self, profile: str = "jarvis") -> dict[str, Any]:
        return {
            "version": 1,
            "profile": profile,
            "preferences": self.get_all_preferences(profile=profile),
            "workflows": self.get_workflows(),
            "exported_at": time.time(),
        }

    def import_preferences(self, data: dict[str, Any], profile: str = "jarvis") -> int:
        count = 0
        for pref in data.get("preferences", []):
            try:
                key = pref.get("key", "")
                value = pref.get("value", "")
                if not key or not value:
                    continue
                self.remember_preference(
                    key=key,
                    value=value,
                    source=pref.get("source", PreferenceSource.EXPLICIT_USER.value),
                    confidence=pref.get("confidence", ConfidenceLevel.MEDIUM.value),
                    profile=profile,
                )
                count += 1
            except Exception:
                continue
        return count


adaptive_memory = AdaptiveMemory()
