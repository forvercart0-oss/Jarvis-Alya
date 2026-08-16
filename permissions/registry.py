"""Extract requested permissions from a skill definition.

A skill *requests* permissions in its JSON (`permissions` field and/or
`capabilities`). These requests are just that: requests. They are only
effective once the user grants them through the PermissionManager.
"""

from __future__ import annotations

from typing import Any

from permissions.models import ALL_PERMISSIONS, LEGACY_PERMISSION_MAP

# Map a capability string to the canonical permission(s) it implies.
_CAPABILITY_PERMISSION_MAP: dict[str, tuple[str, ...]] = {
    "filesystem.read": ("filesystem.read",),
    "filesystem.write": ("filesystem.write",),
    "terminal.read": ("terminal.read",),
    "terminal.execute": ("terminal.execute",),
    "terminal": ("terminal.read", "terminal.execute"),
    "network.request": ("network.request",),
    "network.http": ("network.request",),
    "network": ("network.request",),
    "microphone": ("microphone",),
    "camera": ("camera",),
    "clipboard.read": ("clipboard.read",),
    "clipboard.write": ("clipboard.write",),
    "notifications": ("notifications",),
    "memory.read": ("memory.read",),
    "memory.write": ("memory.write",),
    "system.monitor": ("filesystem.read",),
    "system.info": (),
    "time.read": (),
    "calculator.execute": (),
}


def capability_permissions(capabilities: list[str]) -> set[str]:
    """Map a skill's capability strings to canonical permission ids."""
    result: set[str] = set()
    for capability in capabilities or []:
        cap = capability.strip().lower()
        direct = _CAPABILITY_PERMISSION_MAP.get(cap)
        if direct is not None:
            result.update(direct)
            continue
        if cap.startswith("terminal"):
            result.update(("terminal.read", "terminal.execute"))
        elif cap.startswith("network"):
            result.update(("network.request",))
        elif cap.startswith("filesystem.read"):
            result.add("filesystem.read")
        elif cap.startswith("filesystem.write"):
            result.add("filesystem.write")
        elif cap.startswith("memory.read"):
            result.add("memory.read")
        elif cap.startswith("memory.write"):
            result.add("memory.write")
    return {p for p in result if p in ALL_PERMISSIONS}


def requested_permissions(skill: dict[str, Any]) -> set[str]:
    """Return the canonical permissions a skill requests (union of fields).

    Only permissions explicitly requested by the skill are returned. Nothing
    is granted here - this is a request list for the user to review.
    """
    result: set[str] = set()

    permissions = skill.get("permissions") or {}
    for key, value in permissions.items():
        if not value:
            continue
        if key in ALL_PERMISSIONS:
            result.add(key)
            continue
        mapped = LEGACY_PERMISSION_MAP.get(key)
        if mapped:
            result.update(mapped)

    result.update(capability_permissions(skill.get("capabilities") or []))
    return result


def requested_permissions_full(skill: dict[str, Any]) -> dict[str, bool]:
    """Return every canonical permission with True/False request state.

    Useful for rendering a permission review dialog.
    """
    requested = requested_permissions(skill)
    return {perm: perm in requested for perm in ALL_PERMISSIONS}
