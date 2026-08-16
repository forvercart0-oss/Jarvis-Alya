"""Skill schema validator.

Skills are JSON configuration, never code. Invalid skills are rejected and
never loaded. Both the JSON Schema and targeted semantic checks run here.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import jsonschema

from skills.models import CANONICAL_PERMISSION_IDS, LEGACY_PERMISSION_KEYS
from skills.schema import skill_schema

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
VALID_PERMISSION_KEYS: set[str] = set(CANONICAL_PERMISSION_IDS) | set(LEGACY_PERMISSION_KEYS)


class SkillValidationError(Exception):
    """Raised when a skill JSON fails schema validation."""


def _strip_error_prefix(message: str) -> str:
    """Trim jsonschema's 'Failed validating ...' / instance-path noise."""
    return re.sub(r"^.*? -> ", "", message)


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

    try:
        jsonschema.validate(instance=data, schema=skill_schema())
    except jsonschema.ValidationError as exc:
        path = "/".join(str(p) for p in exc.absolute_path)
        location = f" at '{path}'" if path else ""
        raise SkillValidationError(
            f"Skill {skill_id!r} is invalid{location}: {_strip_error_prefix(exc.message)}"
        ) from exc

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

    _validate_permissions(data.get("permissions", {}), skill_id)

    version = data.get("version", "")
    if not _is_valid_version(version):
        raise SkillValidationError(
            f"Skill {skill_id!r} version {version!r} is not a valid semver."
        )

    logger.debug("Skill %s passed validation.", skill_id)


def _validate_permissions(permissions: dict[str, Any], skill_id: str) -> None:
    for key in permissions:
        if key not in VALID_PERMISSION_KEYS:
            raise SkillValidationError(
                f"Skill {skill_id!r} has unknown permission key {key!r}. "
                f"Supported: {', '.join(sorted(VALID_PERMISSION_KEYS))}."
            )


def _is_valid_version(version: str) -> bool:
    parts = version.split(".")
    if len(parts) != 3:
        return False
    major, minor, patch = parts
    return major.isdigit() and minor.isdigit() and patch.isdigit()
