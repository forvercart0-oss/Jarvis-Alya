"""Page diff detection for JARVIS Phase 25.

Detects navigation, SPA route changes, modal, dropdown, toast,
notification, content update.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.browser.page_diff")


@dataclass
class PageDiff:
    url_changed: bool = False
    title_changed: bool = False
    content_changed: bool = False
    new_elements: list[str] = field(default_factory=list)
    removed_elements: list[str] = field(default_factory=list)
    modals_opened: list[str] = field(default_factory=list)
    modals_closed: list[str] = field(default_factory=list)
    toasts: list[str] = field(default_factory=list)
    has_changes: bool = False
    change_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "url_changed": self.url_changed,
            "title_changed": self.title_changed,
            "content_changed": self.content_changed,
            "new_elements": self.new_elements,
            "removed_elements": self.removed_elements,
            "modals_opened": self.modals_opened,
            "modals_closed": self.modals_closed,
            "toasts": self.toasts,
            "has_changes": self.has_changes,
            "change_summary": self.change_summary,
        }


class PageDiffEngine:
    def __init__(self):
        self._last_url: str = ""
        self._last_title: str = ""
        self._last_text: str = ""
        self._last_elements: list[str] = []
    def diff(
        self,
        current_url: str,
        current_title: str,
        current_text: str,
        current_elements: list[dict[str, Any]],
    ) -> PageDiff:
        diff = PageDiff()

        if not self._last_url and not self._last_title:
            self._last_url = current_url
            self._last_title = current_title
            self._last_text = current_text
            self._last_elements = [
                (e.get("text", "") or e.get("label", "")) for e in current_elements if isinstance(e, dict)
            ]
            return diff

        if self._last_url != current_url:
            diff.url_changed = True
            diff.has_changes = True
        if self._last_title != current_title:
            diff.title_changed = True
            diff.has_changes = True
        if self._last_text != current_text:
            diff.content_changed = True
            diff.has_changes = True

        current_labels = [e.get("text", "") or e.get("label", "") for e in current_elements if isinstance(e, dict)]
        old_set = set(self._last_elements)
        new_set = set(current_labels)
        for label in new_set - old_set:
            if label.strip():
                diff.new_elements.append(label)
        for label in old_set - new_set:
            if label.strip():
                diff.removed_elements.append(label)
        if diff.new_elements or diff.removed_elements:
            diff.has_changes = True

        modal_keywords = ["modal", "dialog", "popup", "overlay"]
        for label in current_labels:
            if any(k in label.lower() for k in modal_keywords):
                diff.modals_opened.append(label)
        for label in self._last_elements:
            if any(k in label.lower() for k in modal_keywords) and label not in current_labels:
                diff.modals_closed.append(label)
        if diff.modals_opened or diff.modals_closed:
            diff.has_changes = True

        toast_keywords = ["toast", "notification", "alert", "snackbar"]
        for label in current_labels:
            if any(k in label.lower() for k in toast_keywords):
                diff.toasts.append(label)
        if diff.toasts:
            diff.has_changes = True

        parts = []
        if diff.url_changed:
            parts.append("URL changed")
        if diff.title_changed:
            parts.append("title changed")
        if diff.content_changed:
            parts.append("content changed")
        if diff.new_elements:
            parts.append(f"{len(diff.new_elements)} new elements")
        if diff.removed_elements:
            parts.append(f"{len(diff.removed_elements)} removed elements")
        if diff.modals_opened:
            parts.append(f"{len(diff.modals_opened)} modals opened")
        if diff.toasts:
            parts.append(f"{len(diff.toasts)} toasts")
        diff.change_summary = ", ".join(parts) if parts else "No significant changes detected"

        self._last_url = current_url
        self._last_title = current_title
        self._last_text = current_text
        self._last_elements = current_labels
        return diff

    def reset(self) -> None:
        self._last_url = ""
        self._last_title = ""
        self._last_text = ""
        self._last_elements = []


page_diff_engine = PageDiffEngine()
