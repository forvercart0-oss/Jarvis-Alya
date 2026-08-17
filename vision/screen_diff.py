"""Screen diff engine for JARVIS Phase 24.

Detects changes between screen captures: new elements, removed elements,
changed text, changed windows, notifications, dialogs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.vision.screen_diff")


@dataclass
class ScreenDiff:
    new_elements: list[dict[str, Any]] = field(default_factory=list)
    removed_elements: list[dict[str, Any]] = field(default_factory=list)
    changed_text: list[dict[str, Any]] = field(default_factory=list)
    new_windows: list[str] = field(default_factory=list)
    removed_windows: list[str] = field(default_factory=list)
    notifications: list[str] = field(default_factory=list)
    dialogs: list[str] = field(default_factory=list)
    has_changes: bool = False
    change_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "new_elements": self.new_elements,
            "removed_elements": self.removed_elements,
            "changed_text": self.changed_text,
            "new_windows": self.new_windows,
            "removed_windows": self.removed_windows,
            "notifications": self.notifications,
            "dialogs": self.dialogs,
            "has_changes": self.has_changes,
            "change_summary": self.change_summary,
        }


class ScreenDiffEngine:
    def __init__(self):
        self._last_screen_hash: str | None = None
        self._last_ocr_text: str = ""
        self._last_window: str = ""
        self._last_elements: list[dict[str, Any]] = []

    def diff(
        self,
        current_ocr: str,
        current_window: str,
        current_elements: list[dict[str, Any]],
        current_image_hash: str,
    ) -> ScreenDiff:
        diff = ScreenDiff()

        if self._last_screen_hash and self._last_screen_hash != current_image_hash:
            diff.has_changes = True

        if self._last_ocr_text and self._last_ocr_text != current_ocr:
            old_lines = set(self._last_ocr_text.splitlines())
            new_lines = set(current_ocr.splitlines())
            added = new_lines - old_lines
            removed = old_lines - new_lines
            for line in added:
                if line.strip():
                    diff.changed_text.append({"type": "added", "text": line.strip()})
            for line in removed:
                if line.strip():
                    diff.changed_text.append({"type": "removed", "text": line.strip()})
            if added or removed:
                diff.has_changes = True

        if self._last_window and self._last_window != current_window:
            diff.new_windows.append(current_window)
            diff.removed_windows.append(self._last_window)
            diff.has_changes = True

        old_labels = {e.get("label", "") for e in self._last_elements}
        new_labels = {e.get("label", "") for e in current_elements}
        for label in new_labels - old_labels:
            diff.new_elements.append({"label": label})
        for label in old_labels - new_labels:
            diff.removed_elements.append({"label": label})
        if new_labels - old_labels or old_labels - new_labels:
            diff.has_changes = True

        notification_keywords = ["notification", "alert", "popup", "dialog", "message"]
        for line in current_ocr.splitlines():
            if any(k in line.lower() for k in notification_keywords):
                diff.notifications.append(line.strip())
                diff.has_changes = True

        parts = []
        if diff.new_elements:
            parts.append(f"{len(diff.new_elements)} new elements")
        if diff.removed_elements:
            parts.append(f"{len(diff.removed_elements)} removed elements")
        if diff.changed_text:
            parts.append(f"{len(diff.changed_text)} text changes")
        if diff.new_windows:
            parts.append(f"window changed to {diff.new_windows[0]}")
        if diff.notifications:
            parts.append(f"{len(diff.notifications)} notifications")
        diff.change_summary = ", ".join(parts) if parts else "No significant changes detected"

        self._last_screen_hash = current_image_hash
        self._last_ocr_text = current_ocr
        self._last_window = current_window
        self._last_elements = current_elements
        return diff

    def reset(self) -> None:
        self._last_screen_hash = None
        self._last_ocr_text = ""
        self._last_window = ""
        self._last_elements = []


screen_diff_engine = ScreenDiffEngine()
