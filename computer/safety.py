"""Computer control safety for JARVIS Phase 3."""

from __future__ import annotations

from typing import Any


class ComputerSafety:
    DANGEROUS_ACTIONS = {"shutdown", "reboot", "format", "delete_user", "remove_user"}
    CONFIRMATION_ACTIONS = {"open_application", "type_text", "set_volume", "take_screenshot"}

    def is_allowed(self, action: str) -> bool:
        return action not in self.DANGEROUS_ACTIONS

    def requires_confirmation(self, action: str) -> bool:
        return action in self.CONFIRMATION_ACTIONS
