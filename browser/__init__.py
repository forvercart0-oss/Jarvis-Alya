"""Browser Agent module for JARVIS Phase 3."""

from __future__ import annotations

from browser.manager import BrowserManager
from browser.sessions import BrowserSession, get_browser_session_manager
from browser.safety import BrowserSafety

__all__ = [
    "BrowserManager",
    "BrowserSession",
    "BrowserSafety",
    "get_browser_session_manager",
]
