"""Gesture-to-action controller."""

from __future__ import annotations

import logging
from typing import Callable, Optional

from vision.gesture.gestures import get_gesture

logger = logging.getLogger("jarvis.gesture.controller")


class GestureController:
    def __init__(self, settings):
        self.settings = settings
        self._actions: dict[str, str] = {}
        self._on_action: Optional[Callable] = None
        self._load_defaults()

    def _load_defaults(self):
        defaults = {
            "open_palm": "stop",
            "thumbs_up": "confirm",
            "thumbs_down": "cancel",
            "point": "select",
            "two_fingers": "scroll",
            "pinch": "click",
            "fist": "stop_action",
        }
        self._actions.update(defaults)

    def on_action(self, callback: Callable) -> None:
        self._on_action = callback

    def handle_gesture(self, gesture_id: str) -> Optional[str]:
        gesture = get_gesture(gesture_id)
        if not gesture:
            return None
        action = self._actions.get(gesture_id, gesture.default_action)
        if gesture.requires_confirmation:
            logger.info("Gesture %s requires confirmation for action %s", gesture_id, action)
        if self._on_action:
            try:
                self._on_action(gesture_id, action)
            except Exception:
                pass
        return action
