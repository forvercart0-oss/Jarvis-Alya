"""Skills subsystem for JARVIS 2.0.

Provides a modular, dynamically discoverable skill architecture:

- JSON-based skill definitions (configuration only, never executed)
- Built-in skills shipped with JARVIS
- Custom skills installed by the user
- Permission-aware skill execution sandbox
- Skill router for lightweight message-to-skill matching
"""

from __future__ import annotations

from skills.loader import load_all_skills, load_skill_file, load_skills_from_directory
from skills.manager import SkillManager
from skills.models import CANONICAL_PERMISSION_IDS, LEGACY_PERMISSION_KEYS, VALID_PRIORITIES
from skills.registry import SkillRegistry
from skills.router import SkillRouter
from skills.validator import SkillValidationError, validate_skill

__all__ = [
    "CANONICAL_PERMISSION_IDS",
    "LEGACY_PERMISSION_KEYS",
    "VALID_PRIORITIES",
    "SkillManager",
    "SkillRegistry",
    "SkillRouter",
    "SkillValidationError",
    "load_all_skills",
    "load_skill_file",
    "load_skills_from_directory",
    "validate_skill",
]
