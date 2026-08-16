"""Skill schema validator."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.skills.validator")

REQUIRED_FIELDS: dict[str, type] = {
    "id": str,
    "name": str,
    "version": str,
    "description": str,
    "author": str,
    "enabled": bool,
    "priority": str,
    "triggers": list,
    "capabilities": list,
    "instructions": list,
    "permissions": dict,
}

VALID_PRIORITIES: set[str] = {"high", "normal", "low"}
VALID_PERMISSION_KEYS: set[str] = {
    "network",
    "filesystem_read",
    "filesystem_write",
    "terminal",
    "camera",
    "microphone",
}


class SkillValidationError(Exception):
    """Raised when a skill JSON fails schema validation."""


def validate_skill(data: dict[str, Any], skill_id: str = "<unknown>") -> None:
    """Validate a skill dictionary against the schema.

    Args:
        data: Parsed JSON skill data.
        skill_id: Identifier for error messages.

    Raises:
        SkillValidationError: If the skill is invalid.
    """
    if not isinstance(data, dict):
        raise SkillValidationError(f"Skill {skill_id!r} must be a JSON object.")

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in data:
            raise SkillValidationError(
                f"Skill {skill_id!r} is missing required field {field!r}."
            )
        if not isinstance(data[field], expected_type):
            raise SkillValidationError(
                f"Skill {skill_id!r} field {field!r} must be {expected_type.__name__}, "
                f"got {type(data[field]).__name__}."
            )

    if not data["id"].strip():
        raise SkillValidationError(f"Skill {skill_id!r} id must not be empty.")

    if not data["name"].strip():
        raise SkillValidationError(f"Skill {skill_id!r} name must not be empty.")

    priority = data.get("priority", "").lower()
    if priority not in VALID_PRIORITIES:
        raise SkillValidationError(
            f"Skill {skill_id!r} priority must be one of {sorted(VALID_PRIORITIES)}, "
            f"got {data['priority']!r}."
        )

    if not data["triggers"]:
        raise SkillValidationError(f"Skill {skill_id!r} triggers list must not be empty.")

    if not data["capabilities"]:
        raise SkillValidationError(f"Skill {skill_id!r} capabilities list must not be empty.")

    if not isinstance(data["instructions"], list):
        raise SkillValidationError(f"Skill {skill_id!r} instructions must be a list.")

    for instruction in data["instructions"]:
        if not isinstance(instruction, str) or not instruction.strip():
            raise SkillValidationError(
                f"Skill {skill_id!r} has an empty instruction entry."
            )

    permissions = data.get("permissions", {})
    for key in permissions:
        if key not in VALID_PERMISSION_KEYS:
            logger.warning(
                "Skill %s has unknown permission key %r.", skill_id, key
            )
    for key in VALID_PERMISSION_KEYS:
        if key not in permissions:
            permissions[key] = False

    version = data.get("version", "")
    if not _is_valid_version(version):
        raise SkillValidationError(
            f"Skill {skill_id!r} version {version!r} is not a valid semver."
        )

    logger.debug("Skill %s passed validation.", skill_id)


def _is_valid_version(version: str) -> bool:
    parts = version.split(".")
    if len(parts) != 3:
        return False
    major, minor, patch = parts
    return major.isdigit() and minor.isdigit() and patch.isdigit()
