"""Trust levels and permissions for JARVIS Phase 19."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import Any

logger = logging.getLogger("jarvis.computer.trust")


class TrustLevel(StrEnum):
    ASK_ALWAYS = "ask_always"
    ASK_SENSITIVE = "ask_sensitive"
    TRUSTED = "trusted"
    DISABLED = "disabled"


_COMPUTER_PERMISSIONS = {
    "SCREEN_READ": {"trusted": True, "description": "Read screen content"},
    "MOUSE_CONTROL": {"trusted": True, "description": "Control mouse"},
    "KEYBOARD_CONTROL": {"trusted": True, "description": "Control keyboard"},
    "WINDOW_CONTROL": {"trusted": True, "description": "Control windows"},
    "FILE_READ": {"trusted": True, "description": "Read files"},
    "FILE_WRITE": {"trusted": False, "description": "Write files"},
    "FILE_DELETE": {"trusted": False, "description": "Delete files"},
    "TERMINAL_READ": {"trusted": True, "description": "Read terminal output"},
    "TERMINAL_EXECUTE": {"trusted": False, "description": "Execute terminal commands"},
    "PROCESS_CONTROL": {"trusted": False, "description": "Control processes"},
    "SYSTEM_SETTINGS": {"trusted": False, "description": "Change system settings"},
}


class ComputerPermissionManager:
    def __init__(self, trust_level: TrustLevel = TrustLevel.ASK_SENSITIVE):
        self._trust_level = trust_level
        self._overrides: dict[str, TrustLevel] = {}

    def set_trust_level(self, level: TrustLevel) -> None:
        self._trust_level = level

    def get_trust_level(self) -> TrustLevel:
        return self._trust_level

    def override(self, permission: str, level: TrustLevel) -> None:
        self._overrides[permission] = level

    def is_allowed(self, permission: str) -> bool:
        level = self._overrides.get(permission, self._trust_level)
        if level == TrustLevel.DISABLED:
            return False
        return True

    def requires_confirmation(self, permission: str) -> bool:
        level = self._overrides.get(permission, self._trust_level)
        perm = _COMPUTER_PERMISSIONS.get(permission.upper())
        if level == TrustLevel.ASK_ALWAYS:
            return True
        if level == TrustLevel.ASK_SENSITIVE:
            if perm:
                return not perm["trusted"]
            return True
        if level == TrustLevel.TRUSTED:
            return False
        return True

    def list_permissions(self) -> dict[str, dict[str, Any]]:
        return dict(_COMPUTER_PERMISSIONS)


computer_permission_manager = ComputerPermissionManager()
