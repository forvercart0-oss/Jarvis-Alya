"""Skill manager: CRUD operations, import/export, persistence, activity log."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from skills.registry import SkillRegistry
from skills.validator import validate_skill

logger = logging.getLogger("jarvis.skills.manager")


class SkillManager:
    """Higher-level skill management facade over the registry."""

    def __init__(self, registry: SkillRegistry):
        self._registry = registry

    # ---------------------------------------------------------------- spec API
    def load_skills(self) -> list[dict[str, Any]]:
        """Load all skills from disk into the registry."""
        self._registry.load()
        return self.list_skills()

    def reload_skills(self) -> list[dict[str, Any]]:
        """Hot reload skills without restarting the application."""
        self._registry.reload()
        return self.list_skills()

    def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        return self._registry.get(skill_id)

    def list_skills(self) -> list[dict[str, Any]]:
        return self._registry.list_all()

    def enable_skill(self, skill_id: str) -> bool:
        return self._registry.enable(skill_id)

    def disable_skill(self, skill_id: str) -> bool:
        return self._registry.disable(skill_id)

    def install_skill(self, skill_data: dict[str, Any]) -> str:
        """Validate, persist, and register a skill. Returns its id."""
        validate_skill(skill_data)
        skill_id = self.create_skill(skill_data)
        self.save_skill_to_disk(skill_id, self._registry.custom_dir)
        return skill_id

    def remove_skill(self, skill_id: str) -> bool:
        """Remove a skill from the registry and delete its custom file."""
        source = self._registry.get_source(skill_id)
        ok = self._registry.delete_skill(skill_id)
        if not ok:
            return False
        if source == "custom":
            path = self._registry.custom_dir / f"{skill_id}.json"
            if path.exists():
                path.unlink()
                logger.info("Removed skill file %s.", path)
        return True

    def validate_skill(self, skill_data: dict[str, Any]) -> dict[str, Any]:
        """Validate skill data, returning the canonical public form."""
        validate_skill(skill_data)
        return dict(skill_data)

    # ---------------------------------------------------------------- CRUD
    def create_skill(self, skill_data: dict[str, Any]) -> str:
        """Create and register a new skill (in-memory)."""
        self._registry.register(skill_data)
        return skill_data["id"]

    def update_skill(self, skill_id: str, updates: dict[str, Any]) -> bool:
        skill = self._registry.get(skill_id)
        if skill is None:
            return False
        for key, value in updates.items():
            if key in ("id", "_source", "source"):
                continue
            skill[key] = value
        validate_skill(skill)
        self._registry._log_activity(skill_id, "update", {"updated_fields": list(updates.keys())})
        logger.info("Updated skill %s.", skill_id)
        return True

    def delete_skill(self, skill_id: str) -> bool:
        return self.remove_skill(skill_id)

    def set_priority(self, skill_id: str, priority: str) -> bool:
        return self._registry.set_priority(skill_id, priority)

    # ---------------------------------------------------------------- import / export
    def export_skill(self, skill_id: str) -> str:
        return self._registry.export_skill(skill_id)

    def export_all(self) -> str:
        return json.dumps(self._registry.list_all(), indent=2)

    def import_skill(self, json_string: str) -> str:
        return self._registry.import_skill(json_string)

    # ---------------------------------------------------------------- matching
    def match_skills(self, text: str) -> list[dict[str, Any]]:
        return self._registry.match(text)

    # ---------------------------------------------------------------- permissions
    def get_permissions(self, skill_id: str) -> dict[str, bool] | None:
        skill = self._registry.get(skill_id)
        if skill is None:
            return None
        return self._registry.map_permissions_to_capabilities(skill)

    # ---------------------------------------------------------------- activity
    def get_activity_log(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._registry.get_activity_log(limit)

    # ---------------------------------------------------------------- persistence
    def save_skill_to_disk(self, skill_id: str, directory: Path) -> Path:
        skill = self._registry.get(skill_id)
        if skill is None:
            raise KeyError(f"Skill not found: {skill_id}")
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{skill_id}.json"
        public = dict(skill)
        public.pop("_source", None)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(public, fh, indent=2)
        logger.info("Saved skill %s to %s.", skill_id, path)
        return path
