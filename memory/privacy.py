"""Memory privacy controls."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.memory.privacy")


class PrivacyController:
    """Manage memory privacy settings."""

    def __init__(self, memory_manager: Any):
        self._memory = memory_manager

    def set_mode(self, mode: str) -> None:
        allowed = {"normal", "private", "incognito"}
        if mode not in allowed:
            raise ValueError(f"Privacy mode must be one of {allowed}")
        self._memory.store.set_privacy_setting("privacy_mode", mode)

    def get_mode(self) -> str:
        return self._memory.store.get_privacy_setting("privacy_mode", "normal")

    def is_private(self) -> bool:
        return self.get_mode() in ("private", "incognito")

    def is_incognito(self) -> bool:
        return self.get_mode() == "incognito"

    def allow_memory_writes(self) -> bool:
        return not self.is_incognito()

    def allow_cloud_sharing(self) -> bool:
        mode = self.get_mode()
        if mode == "incognito":
            return False
        sharing = self._memory.store.get_privacy_setting("cloud_sharing", "ask")
        return sharing != "never"

    def set_cloud_sharing(self, value: str) -> None:
        allowed = {"never", "ask", "allow"}
        if value not in allowed:
            raise ValueError(f"cloud_sharing must be one of {allowed}")
        self._memory.store.set_privacy_setting("cloud_sharing", value)

    def get_all_settings(self) -> dict:
        return self._memory.store.get_all_privacy_settings()
