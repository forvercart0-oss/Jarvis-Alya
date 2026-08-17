"""Browser Agent module for JARVIS Phase 18."""

from __future__ import annotations

from browser.element import find_best_element, semantic_match
from browser.manager import BrowserManager
from browser.page_context import PageContext, PageElement, page_context_extractor
from browser.permissions import BrowserPermissionManager, browser_permission_manager
from browser.planner import BrowserActionPlanner, BrowserTask, BrowserTaskState, browser_planner
from browser.provider import BrowserProvider, PlaywrightBrowserProvider, get_browser_provider
from browser.safety import BrowserSafety
from browser.sessions import BrowserSession, get_browser_session_manager
from browser.takeover import BrowserTakeover, browser_takeover

__all__ = [
    "BrowserActionPlanner",
    "BrowserManager",
    "BrowserPermissionManager",
    "BrowserProvider",
    "BrowserSafety",
    "BrowserSession",
    "BrowserTakeover",
    "BrowserTask",
    "BrowserTaskState",
    "PageContext",
    "PageElement",
    "PlaywrightBrowserProvider",
    "browser_permission_manager",
    "browser_planner",
    "browser_takeover",
    "find_best_element",
    "get_browser_provider",
    "get_browser_session_manager",
    "page_context_extractor",
    "semantic_match",
]
