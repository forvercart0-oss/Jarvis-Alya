"""Short-term browser memory for JARVIS Phase 25.

Stores: current tab, current page, recent actions, last resolved elements.
Does NOT store full browsing history unless explicitly requested.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.browser.browser_memory")


@dataclass
class BrowserMemory:
    session_id: str = "default"
    current_url: str = ""
    current_title: str = ""
    recent_actions: list[dict[str, Any]] = field(default_factory=list)
    last_resolved_elements: dict[str, Any] = field(default_factory=dict)
    user_preferences: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def record_action(self, action: str, target: str = "", result: str = "") -> None:
        self.recent_actions.append({
            "action": action,
            "target": target,
            "result": result,
            "timestamp": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
        })
        if len(self.recent_actions) > 50:
            self.recent_actions = self.recent_actions[-50:]

    def remember_element(self, target: str, element: dict[str, Any]) -> None:
        self.last_resolved_elements[target] = element

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self.user_preferences.get(key, default)

    def set_preference(self, key: str, value: Any) -> None:
        self.user_preferences[key] = value


class BrowserMemoryStore:
    def __init__(self):
        self._memories: dict[str, BrowserMemory] = {}

    def get(self, session_id: str) -> BrowserMemory:
        if session_id not in self._memories:
            self._memories[session_id] = BrowserMemory(session_id=session_id)
        return self._memories[session_id]

    def clear(self, session_id: str) -> None:
        self._memories.pop(session_id, None)

    def clear_all(self) -> None:
        self._memories.clear()


browser_memory_store = BrowserMemoryStore()
