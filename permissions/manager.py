"""PermissionManager: persistence and enforcement of granted permissions.

Granted decisions persist to a JSON file (default `data/permissions.json`).
The file contains NO secrets - only permission booleans.

Invariants enforced here:
  * Default deny: any permission not explicitly granted is denied.
  * A skill cannot grant permissions to itself; only the manager grants.
  * Unknown permission ids are ignored at load time (never granted).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from permissions.models import ALL_PERMISSIONS, LEGACY_PERMISSION_MAP
from permissions.policy import required_permissions_for_tool
from permissions.registry import requested_permissions

logger = logging.getLogger("jarvis.permissions")

_STORE_VERSION = 1


def _canonicalize(permissions: dict[str, bool] | set[str] | list[str]) -> dict[str, bool]:
    """Convert user-supplied permission selections into a canonical bool map."""
    out: dict[str, bool] = {}
    if isinstance(permissions, dict):
        items = permissions.items()
    else:
        items = [(p, True) for p in permissions]
    for key, value in items:
        key = str(key).strip().lower()
        if key in ALL_PERMISSIONS:
            out[key] = bool(value)
        elif key in LEGACY_PERMISSION_MAP:
            for mapped in LEGACY_PERMISSION_MAP[key]:
                out[mapped] = bool(value)
    return out


class PermissionManager:
    """Tracks per-skill granted permissions with a default-deny policy."""

    def __init__(self, path: Path | str | None = None):
        self._path = Path(path) if path else Path("data/permissions.json")
        self._grants: dict[str, dict[str, bool]] = {}
        self.load()

    # ------------------------------------------------------------- io
    def load(self) -> None:
        self._grants = {}
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            skills = raw.get("skills", {})
            for skill_id, perms in skills.items():
                if not isinstance(perms, dict):
                    continue
                canonical = _canonicalize(perms)
                # Unknown permission ids are dropped (default deny).
                self._grants[str(skill_id)] = {
                    perm: True for perm, granted in canonical.items() if granted
                }
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load permissions file %s: %s", self._path, exc)

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "version": _STORE_VERSION,
            "default_policy": "deny",
            "skills": {sid: dict(perms) for sid, perms in self._grants.items()},
        }
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    # ------------------------------------------------------------- read
    @property
    def path(self) -> Path:
        return self._path

    def get_granted(self, skill_id: str) -> dict[str, bool]:
        """Return granted permissions (True only) for a skill. Default deny."""
        grants = self._grants.get(str(skill_id), {})
        return {perm: True for perm in ALL_PERMISSIONS if grants.get(perm)}

    def is_allowed(self, skill_id: str, permission: str) -> bool:
        """Whether a skill has been granted a single permission (default deny)."""
        if permission not in ALL_PERMISSIONS:
            return False
        return bool(self._grants.get(str(skill_id), {}).get(permission))

    def effective(self, skill_id: str, skill: dict[str, Any]) -> dict[str, bool]:
        """Requested AND granted permissions for a skill."""
        requested = requested_permissions(skill)
        granted = self.get_granted(skill_id)
        return {perm: perm in requested and granted.get(perm) for perm in ALL_PERMISSIONS}

    def is_tool_allowed(self, skill_id: str, tool_name: str, skill: dict[str, Any] | None = None) -> bool:
        """Whether a skill is allowed to execute a tool under its grants.

        An empty requirement means the tool is observation-only and always
        allowed for enabled skills. If the skill requests a permission but it
        was not granted, the tool is denied.
        """
        required = required_permissions_for_tool(tool_name)
        if not required:
            return True
        if skill is not None:
            requested = requested_permissions(skill)
            # Only enforce grants for permissions the skill actually requested.
            enforced = {perm for perm in required if perm in requested}
            if not enforced:
                return True
            required = tuple(enforced)
        grants = self._grants.get(str(skill_id), {})
        return all(grants.get(perm) for perm in required)

    def pending(self, skill_id: str, skill: dict[str, Any]) -> dict[str, bool]:
        """Requested but not yet granted permissions (for review prompts)."""
        requested = requested_permissions(skill)
        granted = self.get_granted(skill_id)
        return {perm: True for perm in requested if not granted.get(perm)}

    # ------------------------------------------------------------- write
    def grant(self, skill_id: str, permissions: dict[str, bool] | set[str] | list[str]) -> dict[str, bool]:
        """Grant/revoke permissions for a skill. Returns the effective grants."""
        canonical = _canonicalize(permissions)
        sid = str(skill_id)
        current = self._grants.setdefault(sid, {})
        for perm, granted in canonical.items():
            if granted:
                current[perm] = True
            else:
                current.pop(perm, None)
        self.save()
        logger.info("Updated permissions for skill %s: %d granted.", sid, len(current))
        return self.get_granted(sid)

    def revoke(self, skill_id: str, permission: str) -> bool:
        perm = str(permission).strip().lower()
        if perm not in ALL_PERMISSIONS:
            return False
        current = self._grants.get(str(skill_id), {})
        changed = current.pop(perm, None) is not None
        if changed:
            self.save()
        return changed

    def reset(self) -> int:
        """Revoke every granted permission. Returns number of skills cleared."""
        count = len(self._grants)
        self._grants = {}
        self.save()
        logger.info("Reset all skill permissions (%d skills).", count)
        return count

    def reset_skill(self, skill_id: str) -> bool:
        sid = str(skill_id)
        existed = sid in self._grants
        self._grants.pop(sid, None)
        if existed:
            self.save()
        return existed

    # ------------------------------------------------------------- summary
    def summary(self, skills: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Serialize a reviewable overview of requested/granted permissions."""
        overview: dict[str, dict[str, bool]] = {}
        for skill in skills or []:
            sid = skill.get("id")
            if not sid:
                continue
            overview[str(sid)] = self.effective(sid, skill)
        return {
            "version": _STORE_VERSION,
            "default_policy": "deny",
            "permissions": overview,
        }
