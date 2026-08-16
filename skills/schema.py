"""JSON Schema for skill definitions (configuration only - never executed)."""

from __future__ import annotations

import json
from typing import Any

from skills.models import CANONICAL_PERMISSION_IDS, LEGACY_PERMISSION_KEYS

SKILL_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://jarvis.local/schemas/skill.schema.json",
    "title": "JARVIS Skill",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "id",
        "name",
        "version",
        "description",
        "author",
        "enabled",
        "priority",
        "triggers",
        "capabilities",
        "instructions",
        "permissions",
    ],
    "properties": {
        "id": {
            "type": "string",
            "pattern": "^[a-z0-9][a-z0-9-]*$",
            "maxLength": 64,
        },
        "name": {"type": "string", "minLength": 1, "maxLength": 128},
        "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
        "description": {"type": "string", "maxLength": 500},
        "author": {"type": "string", "maxLength": 128},
        "category": {"type": "string", "maxLength": 64},
        "icon": {"type": "string", "maxLength": 256},
        "enabled": {"type": "boolean"},
        "priority": {"enum": ["high", "normal", "low"]},
        "uses_memory": {"type": "boolean"},
        "triggers": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1, "maxLength": 64},
        },
        "capabilities": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1, "maxLength": 128},
        },
        "instructions": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
        "permissions": {
            "type": "object",
            "additionalProperties": {"type": "boolean"},
            "properties": {
                **{perm: {"type": "boolean"} for perm in CANONICAL_PERMISSION_IDS},
                **{perm: {"type": "boolean"} for perm in LEGACY_PERMISSION_KEYS},
            },
        },
    },
}


def skill_schema() -> dict[str, Any]:
    """Return a fresh copy of the skill JSON schema."""
    return json.loads(json.dumps(SKILL_JSON_SCHEMA))
