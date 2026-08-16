"""Skill registry: load, register, retrieve, enable/disable, priority, hot reload."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from skills.loader import load_all_skills

logger = logging.getLogger("jarvis.skills.registry")


class SkillRegistry:
    """In-memory registry of skills with enable/disable state and priority ordering."""

    def __init__(self, base_dir: Path | None = None):
        self._base_dir = base_dir or Path(__file__).resolve().parent
        self._skills: dict[str, dict[str, Any]] = {}
        self._activity_log: list[dict[str, Any]] = []

    @property
    def base_dir(self) -> Path:
        """Directory skills are loaded from and persisted to."""
        return self._base_dir

    # ---------------------------------------------------------------- loading
    def load(self) -> dict[str, dict[str, Any]]:
        """Load all skills from disk, replacing current registry contents."""
        self._skills = load_all_skills(self._base_dir)
        logger.info("Loaded %d skills.", len(self._skills))
        return self._skills

    def reload(self) -> dict[str, dict[str, Any]]:
        """Hot reload skills from disk, preserving enable/disable state."""
        current_ids = {s["id"]: s.get("enabled", True) for s in self._skills.values()}
        self._skills = load_all_skills(self._base_dir)
        for skill_id, enabled in current_ids.items():
            if skill_id in self._skills:
                self._skills[skill_id]["enabled"] = enabled
        logger.info("Hot reloaded %d skills.", len(self._skills))
        return self._skills

    def register(self, skill_data: dict[str, Any]) -> None:
        """Register a single skill dict into the registry."""
        from skills.validator import validate_skill

        validate_skill(skill_data)
        skill_id = skill_data["id"]
        self._skills[skill_id] = skill_data
        logger.debug("Registered skill %s.", skill_id)

    # ---------------------------------------------------------------- retrieval
    def get(self, skill_id: str) -> dict[str, Any] | None:
        """Return a skill by id, or None."""
        return self._skills.get(skill_id)

    def list_all(self) -> list[dict[str, Any]]:
        """Return a shallow copy of all registered skills."""
        return list(self._skills.values())

    def list_enabled(self) -> list[dict[str, Any]]:
        """Return only enabled skills, sorted by priority (high first)."""
        enabled = [s for s in self._skills.values() if s.get("enabled", True)]
        priority_order = {"high": 0, "normal": 1, "low": 2}
        enabled.sort(key=lambda s: priority_order.get(s.get("priority", "normal"), 1))
        return enabled

    # ---------------------------------------------------------------- state
    def enable(self, skill_id: str) -> bool:
        """Enable a skill by id. Returns True if found."""
        skill = self._skills.get(skill_id)
        if skill:
            skill["enabled"] = True
            self._log_activity(skill_id, "enable")
            logger.info("Enabled skill %s.", skill_id)
            return True
        return False

    def disable(self, skill_id: str) -> bool:
        """Disable a skill by id. Returns True if found."""
        skill = self._skills.get(skill_id)
        if skill:
            skill["enabled"] = False
            self._log_activity(skill_id, "disable")
            logger.info("Disabled skill %s.", skill_id)
            return True
        return False

    def set_priority(self, skill_id: str, priority: str) -> bool:
        """Set skill priority. Returns True if found."""
        valid = {"high", "normal", "low"}
        if priority not in valid:
            raise ValueError(f"Priority must be one of {sorted(valid)}, got {priority!r}.")
        skill = self._skills.get(skill_id)
        if skill:
            skill["priority"] = priority
            self._log_activity(skill_id, "set_priority", {"priority": priority})
            logger.info("Set skill %s priority to %s.", skill_id, priority)
            return True
        return False

    # ---------------------------------------------------------------- matching
    def match(self, text: str) -> list[dict[str, Any]]:
        """Match enabled skills against text using trigger keywords.

        Returns matched skills sorted by priority (high first).
        """
        text_lower = text.lower()
        matched: list[dict[str, Any]] = []
        for skill in self.list_enabled():
            triggers = skill.get("triggers", [])
            if any(trigger.lower() in text_lower for trigger in triggers):
                matched.append(skill)
        priority_order = {"high": 0, "normal": 1, "low": 2}
        matched.sort(key=lambda s: priority_order.get(s.get("priority", "normal"), 1))
        return matched

    # ---------------------------------------------------------------- permissions
    @staticmethod
    def map_permissions_to_capabilities(skill: dict[str, Any]) -> dict[str, bool]:
        """Extract the permissions dict from a skill.

        This is a direct mapping - no execution of skill code occurs.
        """
        permissions = skill.get("permissions", {})
        return {key: bool(permissions.get(key, False)) for key in permissions}

    # ---------------------------------------------------------------- activity
    def _log_activity(self, skill_id: str, action: str, extra: dict[str, Any] | None = None) -> None:
        import datetime

        entry: dict[str, Any] = {
            "skill_id": skill_id,
            "action": action,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        if extra:
            entry.update(extra)
        self._activity_log.append(entry)

    def get_activity_log(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return recent activity log entries."""
        return self._activity_log[-limit:]

    # ---------------------------------------------------------------- import / export
    def export_skill(self, skill_id: str) -> str:
        """Export a skill as a JSON string."""
        skill = self._skills.get(skill_id)
        if skill is None:
            raise KeyError(f"Skill not found: {skill_id}")
        import json

        return json.dumps(skill, indent=2)

    def import_skill(self, json_string: str) -> str:
        """Import a skill from a JSON string and register it."""
        import json

        data = json.loads(json_string)
        self.register(data)
        return data["id"]

    def delete_skill(self, skill_id: str) -> bool:
        """Remove a skill from the registry. Returns True if found."""
        if skill_id in self._skills:
            del self._skills[skill_id]
            self._log_activity(skill_id, "delete")
            logger.info("Deleted skill %s.", skill_id)
            return True
        return False
