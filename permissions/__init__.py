"""Permission subsystem for JARVIS 2.0.

Every permission defaults to DENIED. A skill receives only permissions that
the user explicitly grants. Only the PermissionManager can grant permissions;
skills can never grant permissions to themselves.
"""

from __future__ import annotations

from permissions.manager import PermissionManager
from permissions.models import (
    ALL_PERMISSIONS,
    LEGACY_PERMISSION_MAP,
    PERMISSION_DESCRIPTIONS,
)
from permissions.policy import PERMISSION_RULES, TOOL_PERMISSION_REQUIREMENTS
from permissions.registry import (
    capability_permissions,
    requested_permissions,
    requested_permissions_full,
)

__all__ = [
    "ALL_PERMISSIONS",
    "LEGACY_PERMISSION_MAP",
    "PERMISSION_DESCRIPTIONS",
    "PERMISSION_RULES",
    "TOOL_PERMISSION_REQUIREMENTS",
    "PermissionManager",
    "capability_permissions",
    "requested_permissions",
    "requested_permissions_full",
]
