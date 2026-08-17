"""Application understanding for JARVIS Phase 30.

Provides application-specific screen understanding for common apps:
Firefox, Chrome, VS Code, Neovim, Terminal, Dolphin, Discord, etc.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("jarvis.vision.application_understanding")


class ApplicationUnderstanding:
    """Application-specific screen understanding."""

    def __init__(self):
        self._patterns: dict[str, dict[str, Any]] = {
            "firefox": {
                "keywords": ["firefox", "mozilla", "firefox-esr"],
                "ui_elements": ["tab bar", "address bar", "bookmarks", "menu"],
                "url_pattern": re.compile(r"https?://[^\s]+"),
            },
            "chrome": {
                "keywords": ["chrome", "chromium", "google chrome"],
                "ui_elements": ["tab bar", "address bar", "bookmarks", "extensions"],
                "url_pattern": re.compile(r"https?://[^\s]+"),
            },
            "vscode": {
                "keywords": ["visual studio code", "code", "vscode"],
                "ui_elements": ["activity bar", "editor", "sidebar", "panel", "status bar", "terminal"],
                "file_pattern": re.compile(r"[A-Za-z0-9_./-]+\.[A-Za-z0-9]+"),
            },
            "neovim": {
                "keywords": ["neovim", "nvim", "vim"],
                "ui_elements": ["editor", "command line", "status line"],
                "file_pattern": re.compile(r"[A-Za-z0-9_./-]+\.[A-Za-z0-9]+"),
            },
            "terminal": {
                "keywords": ["terminal", "gnome-terminal", "konsole", "xterm", "kitty", "alacritty", "wezterm"],
                "ui_elements": ["prompt", "command line", "output"],
                "prompt_pattern": re.compile(r"[$#%>]\s"),
            },
            "dolphin": {
                "keywords": ["dolphin", "file manager"],
                "ui_elements": ["navigation bar", "file list", "sidebar"],
            },
            "discord": {
                "keywords": ["discord"],
                "ui_elements": ["channel list", "chat", "members", "voice"],
            },
        }

    def detect_application(self, window_title: str, ocr_text: str) -> dict[str, Any]:
        combined = f"{window_title} {ocr_text}".lower()
        best_match = None
        best_score = 0.0

        for app_name, app_info in self._patterns.items():
            score = 0.0
            for keyword in app_info["keywords"]:
                if keyword in combined:
                    score += 0.3
            if score > best_score:
                best_score = score
                best_match = app_name

        if best_match and best_score >= 0.3:
            return {
                "application": best_match,
                "confidence": min(best_score, 1.0),
                "ui_elements": self._patterns[best_match].get("ui_elements", []),
            }
        return {"application": "unknown", "confidence": 0.0, "ui_elements": []}

    def get_application_context(self, app_name: str, ocr_text: str) -> dict[str, Any]:
        context: dict[str, Any] = {"application": app_name, "elements": [], "state": "unknown"}

        if app_name == "terminal":
            context.update(self._analyze_terminal(ocr_text))
        elif app_name in ("vscode", "neovim"):
            context.update(self._analyze_editor(ocr_text, app_name))
        elif app_name in ("dolphin",):
            context.update(self._analyze_file_manager(ocr_text))
        elif app_name in ("firefox", "chrome"):
            context.update(self._analyze_browser(ocr_text))
        elif app_name == "discord":
            context.update(self._analyze_discord(ocr_text))

        return context

    def _analyze_terminal(self, ocr_text: str) -> dict[str, Any]:
        lines = ocr_text.splitlines()
        errors = []
        prompts = 0
        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["error", "exception", "traceback", "failed", "fatal"]):
                errors.append(line.strip())
            if re.search(r"[$#%>]\s", line):
                prompts += 1

        return {
            "elements": ["terminal", "prompt", "output"],
            "state": "terminal",
            "errors": errors[:5],
            "has_prompt": prompts > 0,
            "line_count": len(lines),
        }

    def _analyze_editor(self, ocr_text: str, app_name: str) -> dict[str, Any]:
        lines = ocr_text.splitlines()
        file_pattern = re.compile(r"[A-Za-z0-9_./-]+\.[A-Za-z0-9]+")
        files = list(set(file_pattern.findall(ocr_text)))

        return {
            "elements": ["editor", "file tree", "terminal", "status bar"],
            "state": "editor",
            "detected_files": files[:10],
            "line_count": len(lines),
        }

    def _analyze_file_manager(self, ocr_text: str) -> dict[str, Any]:
        lines = ocr_text.splitlines()
        folders = [l.strip() for l in lines if l.strip().endswith("/") or l.strip().startswith("📁")]
        files = [l.strip() for l in lines if "." in l and not l.strip().endswith("/")]

        return {
            "elements": ["navigation bar", "file list", "sidebar"],
            "state": "file_manager",
            "folders": folders[:10],
            "files": files[:10],
        }

    def _analyze_browser(self, ocr_text: str) -> dict[str, Any]:
        url_pattern = re.compile(r"https?://[^\s]+")
        urls = url_pattern.findall(ocr_text)

        return {
            "elements": ["tab bar", "address bar", "content"],
            "state": "browser",
            "urls": urls[:5],
        }

    def _analyze_discord(self, ocr_text: str) -> dict[str, Any]:
        return {
            "elements": ["channel list", "chat", "members"],
            "state": "discord",
        }


application_understanding = ApplicationUnderstanding()
