"""Visual skills for JARVIS Phase 30.

Provides application-specific visual automation skills.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.vision.visual_skills")


@dataclass
class VisualSkill:
    name: str
    trigger: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    verification: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "trigger": self.trigger,
            "steps": self.steps,
            "verification": self.verification,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VisualSkill:
        return cls(
            name=data.get("name", ""),
            trigger=data.get("trigger", ""),
            steps=data.get("steps", []),
            verification=data.get("verification", []),
            metadata=data.get("metadata", {}),
        )


class VisualSkillManager:
    def __init__(self, skills_dir: str = "skills"):
        self._skills_dir = skills_dir
        self._skills: dict[str, VisualSkill] = {}

    def load_skills(self) -> None:
        if not os.path.isdir(self._skills_dir):
            return
        for filename in os.listdir(self._skills_dir):
            if filename.endswith(".json"):
                path = os.path.join(self._skills_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    skill = VisualSkill.from_dict(data)
                    self._skills[skill.name.lower()] = skill
                except Exception as exc:
                    logger.debug("Failed to load visual skill %s: %s", filename, exc)

    def get_skill(self, name: str) -> VisualSkill | None:
        return self._skills.get(name.lower())

    def find_by_trigger(self, text: str) -> VisualSkill | None:
        lower = text.lower()
        for skill in self._skills.values():
            if skill.trigger.lower() in lower:
                return skill
        return None

    def list_skills(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self._skills.values()]


visual_skill_manager = VisualSkillManager()
