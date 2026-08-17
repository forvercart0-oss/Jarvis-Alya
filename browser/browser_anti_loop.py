"""Browser anti-loop for JARVIS Phase 25.

Prevents repeated blind actions. Tracks state repetitions.
Every browser task has max retries, max action count, timeout, loop detection.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.browser.browser_anti_loop")


@dataclass
class AntiLoopState:
    url: str = ""
    title: str = ""
    text_hash: str = ""
    action_sequence: list[str] = field(default_factory=list)
    repetition_count: int = 0
    last_action: str = ""

    def detect_loop(
        self, current_url: str, current_title: str, current_text: str, action: str
    ) -> bool:
        if self.url == current_url and self.title == current_title and self.text_hash == hash(current_text) and self.last_action == action:
            self.repetition_count += 1
            return self.repetition_count >= 3
        self.url = current_url
        self.title = current_title
        self.text_hash = hash(current_text)
        self.last_action = action
        self.repetition_count = 0
        self.action_sequence.append(action)
        return False


class BrowserAntiLoop:
    def __init__(self, max_actions: int = 20, max_retries: int = 3):
        self._max_actions = max_actions
        self._max_retries = max_retries
        self._states: dict[str, AntiLoopState] = {}

    def check(
        self, session_id: str, action: str, action_count: int, retry_count: int, page: Any = None
    ) -> dict[str, Any]:
        if action_count >= self._max_actions:
            return {"stop": True, "reason": "max_actions_exceeded"}
        if retry_count >= self._max_retries:
            return {"stop": True, "reason": "max_retries_exceeded"}

        state = self._states.setdefault(session_id, AntiLoopState())
        if page and hasattr(page, "url"):
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                url = page.url
                title = (
                    loop.run_until_complete(page.title())
                    if hasattr(page, "title")
                    else ""
                )
                text = (
                    loop.run_until_complete(
                        page.evaluate("() => document.body.innerText")
                    )
                    if hasattr(page, "evaluate")
                    else ""
                )
                if state.detect_loop(url, title, text or "", action):
                    return {
                        "stop": True,
                        "reason": "loop_detected",
                        "repetitions": state.repetition_count,
                    }
            except Exception:
                logger.debug("Anti-loop check failed")
        return {"stop": False}

    def reset(self, session_id: str) -> None:
        self._states.pop(session_id, None)

    def reset_all(self) -> None:
        self._states.clear()


browser_anti_loop = BrowserAntiLoop()
