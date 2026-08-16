"""Skill registry: load, register, retrieve, enable/disable, priority, hot reload."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from skills.loader import load_all_skills
from skills.validator import validate_skill

logger = logging.getLogger("jarvis.skills.registry")

_PRIORITY_RANK = {"high": 0, "normal": 1, "low": 2}
_META_KEYS = ("_source",)


def _public(skill: dict[str, Any]) -> dict[str, Any]:
    """Return a skill dict with internal metadata exposed as public fields."""
    out = dict(skill)
    out["source"] = out.pop("_source", "custom")
    return out


class SkillRegistry:
    """In-memory registry of skills with enable/disable state and priority ordering.

    Runtime state (enabled flag, priority) persists to a JSON states file so a
    reload does not lose user changes. Skills themselves load from disk via the
    loader (custom skills override builtin skills with the same id).
    """

    def __init__(self, base_dir: Path | None = None, states_file: Path | str | None = None):
        self._base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent
        self._states_file = Path(states_file) if states_file else Path("data/skill_states.json")
        self._skills: dict[str, dict[str, Any]] = {}
        self._states: dict[str, dict[str, Any]] = {}
        self._activity_log: list[dict[str, Any]] = []
        self._load_states()

    # ------------------------------------------------------------ states
    def _load_states(self) -> None:
        self._states = {}
        if self._states_file.exists():
            try:
                raw = json.loads(self._states_file.read_text(encoding="utf-8"))
                self._states = raw.get("skills", {}) if isinstance(raw, dict) else {}
            except (json.JSONDecodeError, OSError):
                logger.warning("Could not read skill states file %s.", self._states_file)

    def _save_states(self) -> None:
        try:
            self._states_file.parent.mkdir(parents=True, exist_ok=True)
            self._states_file.write_text(
                json.dumps({"version": 1, "skills": self._states}, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            logger.error("Could not persist skill states: %s", exc)

    def _apply_state(self, skill: dict[str, Any]) -> dict[str, Any]:
        state = self._states.get(skill["id"])
        if state:
            if "enabled" in state:
                skill["enabled"] = bool(state["enabled"])
            if "priority" in state:
                skill["priority"] = state["priority"]
        return skill

    @property
    def base_dir(self) -> Path:
        """Directory skills are loaded from and persisted to."""
        return self._base_dir

    @property
    def custom_dir(self) -> Path:
        return self._base_dir / "custom"

    @property
    def builtin_dir(self) -> Path:
        return self._base_dir / "builtin"

    # ---------------------------------------------------------------- loading
    def load(self) -> dict[str, dict[str, Any]]:
        """Load all skills from disk, replacing current registry contents."""
        self._skills = load_all_skills(self._base_dir)
        for skill in self._skills.values():
            self._apply_state(skill)
        logger.info("Loaded %d skills.", len(self._skills))
        return self._skills

    def reload(self) -> dict[str, dict[str, Any]]:
        """Hot reload skills from disk, preserving runtime state."""
        self._load_states()
        self._skills = load_all_skills(self._base_dir)
        for skill in self._skills.values():
            self._apply_state(skill)
        logger.info("Hot reloaded %d skills.", len(self._skills))
        return self._skills

    def register(self, skill_data: dict[str, Any]) -> None:
        """Register a single skill dict into the registry."""
        validate_skill(skill_data)
        skill_id = skill_data["id"]
        skill = dict(skill_data)
        skill.setdefault("_source", "custom")
        self._apply_state(skill)
        self._skills[skill_id] = skill
        logger.debug("Registered skill %s.", skill_id)

    # ---------------------------------------------------------------- retrieval
    def get(self, skill_id: str) -> dict[str, Any] | None:
        """Return a skill by id, or None."""
        return self._skills.get(skill_id)

    def get_source(self, skill_id: str) -> str:
        skill = self._skills.get(skill_id)
        return skill.get("_source", "custom") if skill else "custom"

    def list_all(self) -> list[dict[str, Any]]:
        """Return a public copy of all registered skills."""
        return [_public(s) for s in self._skills.values()]

    def list_enabled(self) -> list[dict[str, Any]]:
        """Return only enabled skills, sorted by priority (high first)."""
        enabled = [s for s in self._skills.values() if s.get("enabled", True)]
        enabled.sort(key=lambda s: _PRIORITY_RANK.get(s.get("priority", "normal"), 1))
        return enabled

    # ---------------------------------------------------------------- state
    def enable(self, skill_id: str) -> bool:
        """Enable a skill by id. Returns True if found."""
        skill = self._skills.get(skill_id)
        if skill:
            skill["enabled"] = True
            self._states.setdefault(skill_id, {})["enabled"] = True
            self._save_states()
            self._log_activity(skill_id, "enable")
            logger.info("Enabled skill %s.", skill_id)
            return True
        return False

    def disable(self, skill_id: str) -> bool:
        """Disable a skill by id. Returns True if found."""
        skill = self._skills.get(skill_id)
        if skill:
            skill["enabled"] = False
            self._states.setdefault(skill_id, {})["enabled"] = False
            self._save_states()
            self._log_activity(skill_id, "disable")
            logger.info("Disabled skill %s.", skill_id)
            return True
        return False

    def set_priority(self, skill_id: str, priority: str) -> bool:
        """Set skill priority. Returns True if found."""
        if priority not in _PRIORITY_RANK:
            raise ValueError(f"Priority must be one of {sorted(_PRIORITY_RANK)}, got {priority!r}.")
        skill = self._skills.get(skill_id)
        if skill:
            skill["priority"] = priority
            self._states.setdefault(skill_id, {})["priority"] = priority
            self._save_states()
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
        matched.sort(key=lambda s: _PRIORITY_RANK.get(s.get("priority", "normal"), 1))
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
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        }
        if extra:
            entry.update(extra)
        self._activity_log.append(entry)

    def get_activity_log(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return recent activity log entries."""
        return self._activity_log[-limit:]

    # ---------------------------------------------------------------- import / export
    def export_skill(self, skill_id: str) -> str:
        """Export a skill as a JSON string (internal metadata stripped)."""
        skill = self._skills.get(skill_id)
        if skill is None:
            raise KeyError(f"Skill not found: {skill_id}")
        public = _public(skill)
        for key in _META_KEYS:
            public.pop(key, None)
        return json.dumps(public, indent=2)

    def import_skill(self, json_string: str) -> str:
        """Import a skill from a JSON string and register it."""
        data = json.loads(json_string)
        self.register(data)
        return data["id"]

    def delete_skill(self, skill_id: str) -> bool:
        """Remove a skill from the registry. Returns True if found.

        Builtin skills cannot be deleted (only disabled) - they are restored on
        the next reload.
        """
        skill = self._skills.get(skill_id)
        if skill is None:
            return False
        if skill.get("_source") == "builtin":
            raise ValueError(f"Builtin skill {skill_id!r} cannot be deleted.")
        del self._skills[skill_id]
        self._states.pop(skill_id, None)
        self._save_states()
        self._log_activity(skill_id, "delete")
        logger.info("Deleted skill %s.", skill_id)
        return True

    def get_errors(self) -> list[str]:
        """Return human-readable loading errors (kept by the loader is not possible,
        so this is a stable no-op returning validation hints)."""
        return []
