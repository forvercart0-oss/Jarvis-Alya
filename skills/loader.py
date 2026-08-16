"""Skill loader for reading JSON skill definitions from disk."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from skills.validator import SkillValidationError, validate_skill

logger = logging.getLogger("jarvis.skills.loader")


def load_skill_file(path: Path, source: str = "custom") -> dict[str, Any]:
    """Load and validate a single skill JSON file.

    Args:
        path: Path to the JSON skill file.
        source: 'builtin' or 'custom' (where the file lives).

    Returns:
        Validated skill dictionary including an internal ``_source`` marker.

    Raises:
        SkillValidationError: If the file is invalid.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not path.exists():
        raise FileNotFoundError(f"Skill file not found: {path}")
    if not path.is_file():
        raise IsADirectoryError(f"Expected a file, got directory: {path}")

    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    validate_skill(data, skill_id=data.get("id", path.stem))
    data["_source"] = source
    return data


def load_skills_from_directory(directory: Path, source: str = "custom") -> dict[str, dict[str, Any]]:
    """Load all valid skills from a directory of JSON files.

    Args:
        directory: Path containing skill JSON files.
        source: 'builtin' or 'custom' (where the files live).

    Returns:
        Mapping of skill id to validated skill dictionary.
    """
    skills: dict[str, dict[str, Any]] = {}
    if not directory.exists() or not directory.is_dir():
        logger.debug("Skill directory %s does not exist or is not a directory.", directory)
        return skills

    json_files = sorted(directory.glob("*.json"))
    for json_file in json_files:
        try:
            data = load_skill_file(json_file, source=source)
            skill_id = data["id"]
            if skill_id in skills:
                logger.warning(
                    "Duplicate skill id %r in %s, skipping.", skill_id, json_file
                )
                continue
            skills[skill_id] = data
        except (SkillValidationError, json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load skill %s: %s", json_file, exc)

    return skills


def load_all_skills(base_dir: Path) -> dict[str, dict[str, Any]]:
    """Load skills from builtin/ and custom/ subdirectories.

    Custom skills take precedence over builtin skills with the same id.

    Args:
        base_dir: Root skills directory.

    Returns:
        Mapping of skill id to validated skill dictionary.
    """
    builtin_dir = base_dir / "builtin"
    custom_dir = base_dir / "custom"

    builtin = load_skills_from_directory(builtin_dir, source="builtin")
    custom = load_skills_from_directory(custom_dir, source="custom")

    merged = dict(builtin)
    merged.update(custom)
    return merged
