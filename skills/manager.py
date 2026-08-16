"""Skill manager: CRUD operations, import/export, activity log."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from skills.registry import SkillRegistry

logger = logging.getLogger("jarvis.skills.manager")


class SkillManager:
    """Higher-level skill management facade over the registry."""

    def __init__(self, registry: SkillRegistry):
        self._registry = registry

    # ---------------------------------------------------------------- CRUD
    def create_skill(self, skill_data: dict[str, Any]) -> str:
        """Create and register a new skill."""
        self._registry.register(skill_data)
        return skill_data["id"]

    def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        return self._registry.get(skill_id)

    def list_skills(self) -> list[dict[str, Any]]:
        return self._registry.list_all()

    def update_skill(self, skill_id: str, updates: dict[str, Any]) -> bool:
        skill = self._registry.get(skill_id)
        if skill is None:
            return False
        for key, value in updates.items():
            if key in ("id",):
                continue
            skill[key] = value
        self._registry._log_activity(skill_id, "update", {"updated_fields": list(updates.keys())})
        logger.info("Updated skill %s.", skill_id)
        return True

    def delete_skill(self, skill_id: str) -> bool:
        return self._registry.delete_skill(skill_id)

    def enable_skill(self, skill_id: str) -> bool:
        return self._registry.enable(skill_id)

    def disable_skill(self, skill_id: str) -> bool:
        return self._registry.disable(skill_id)

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
        with path.open("w", encoding="utf-8") as fh:
            json.dump(skill, fh, indent=2)
        logger.info("Saved skill %s to %s.", skill_id, path)
        return path
