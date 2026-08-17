"""Browser Agent module for JARVIS Phase 18 / Phase 25."""

from __future__ import annotations

from browser.browser_anti_loop import browser_anti_loop
from browser.browser_intelligence import browser_intelligence
from browser.browser_memory import browser_memory_store
from browser.browser_recovery import browser_recovery_engine
from browser.browser_verification import browser_verifier
from browser.dom_analyzer import dom_analyzer
from browser.download_manager import BrowserDownloadManager, browser_download_manager
from browser.element import find_best_element, semantic_match
from browser.element_resolver import ResolvedElement, element_resolver
from browser.manager import BrowserManager
from browser.page_context import PageContext, PageElement, page_context_extractor
from browser.page_diff import PageDiffEngine, page_diff_engine
from browser.page_inspector import PageInspector, page_inspector
from browser.page_reader import WebPageReader, web_page_reader
from browser.page_summarizer import page_summarizer
from browser.permissions import BrowserPermissionManager, browser_permission_manager
from browser.planner import BrowserActionPlanner, BrowserTask, BrowserTaskState, browser_planner
from browser.provider import BrowserProvider, PlaywrightBrowserProvider, get_browser_provider
from browser.safety import BrowserSafety
from browser.sessions import BrowserSession, get_browser_session_manager
from browser.table_extractor import table_extractor
from browser.takeover import BrowserTakeover, browser_takeover
from browser.upload_manager import BrowserUploadManager, browser_upload_manager

__all__ = [
    "BrowserActionPlanner",
    "BrowserDownloadManager",
    "BrowserIntelligenceOrchestrator",
    "BrowserManager",
    "BrowserPermissionManager",
    "BrowserProvider",
    "BrowserSafety",
    "BrowserSession",
    "BrowserTakeover",
    "BrowserTask",
    "BrowserTaskState",
    "BrowserUploadManager",
    "PageContext",
    "PageDiffEngine",
    "PageElement",
    "PageInspector",
    "PlaywrightBrowserProvider",
    "ResolvedElement",
    "WebPageReader",
    "browser_anti_loop",
    "browser_download_manager",
    "browser_intelligence",
    "browser_memory_store",
    "browser_permission_manager",
    "browser_planner",
    "browser_recovery_engine",
    "browser_takeover",
    "browser_upload_manager",
    "browser_verifier",
    "dom_analyzer",
    "element_resolver",
    "find_best_element",
    "get_browser_provider",
    "get_browser_session_manager",
    "page_context_extractor",
    "page_diff_engine",
    "page_inspector",
    "page_summarizer",
    "semantic_match",
    "table_extractor",
    "web_page_reader",
]
