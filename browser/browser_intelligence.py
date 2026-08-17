"""Browser intelligence orchestrator for JARVIS Phase 25.

Orchestrates the browser intelligence pipeline:
BrowserController -> BrowserSession -> PageInspector -> DOMAnalyzer
-> AccessibilityAnalyzer -> VisionFallback -> ElementResolver
-> ActionPlanner -> BrowserAction -> Verification -> Recovery
"""

from __future__ import annotations

import contextlib
import logging
from typing import Any

from browser.browser_memory import browser_memory_store
from browser.dom_analyzer import dom_analyzer
from browser.element_resolver import element_resolver
from browser.page_inspector import page_inspector
from browser.page_reader import web_page_reader
from browser.page_summarizer import page_summarizer
from browser.planner import browser_planner
from browser.table_extractor import table_extractor

logger = logging.getLogger("jarvis.browser.browser_intelligence")


class BrowserIntelligenceOrchestrator:
    def __init__(self):
        self._enabled = False
        self._broadcast = None
        self._action_planner = browser_planner
        self._max_actions = 20
        self._max_retries = 3
        self._confidence_threshold = 0.5

    def set_broadcast(self, broadcast: Any) -> None:
        self._broadcast = broadcast

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    async def _broadcast(self, event: str, data: dict[str, Any]) -> None:
        if self._broadcast:
            with contextlib.suppress(Exception):
                await self._broadcast(event, data)

    async def execute_task(self, goal: str, session_id: str = "default") -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "error": "Browser intelligence is disabled"}

        task = self._action_planner.create_task(goal, session_id=session_id, max_actions=self._max_actions)
        memory = browser_memory_store.get(session_id)

        await self._broadcast("browser_task_started", {"goal": goal, "session_id": session_id})

        try:
            from backend.main import browser_manager as global_mgr
            from browser.manager import BrowserManager
            mgr = global_mgr if global_mgr else BrowserManager()

            if not mgr.available:
                return {"success": False, "error": "Browser not available", "task": task.to_dict()}

            page = await mgr._get_page(session_id)
            if not page:
                return {"success": False, "error": "No active page", "task": task.to_dict()}

            inspected = await page_inspector.inspect(page)
            memory.current_url = inspected.url
            memory.current_title = inspected.title

            context = {
                "url": inspected.url,
                "title": inspected.title,
                "headings": inspected.headings,
                "paragraphs": inspected.paragraphs,
                "links": inspected.links,
                "buttons": inspected.buttons,
                "inputs": inspected.inputs,
                "forms": inspected.forms,
                "images": inspected.images,
                "tables": inspected.tables,
                "navigation": inspected.navigation,
                "dialogs": inspected.dialogs,
                "aria_roles": inspected.aria_roles,
                "interactive_elements": [],
                "analyzed_elements": [],
                "accessibility_elements": inspected.aria_roles,
            }

            analyzed = await dom_analyzer.analyze(page)
            context["analyzed_elements"] = [e.to_dict() for e in analyzed]
            context["interactive_elements"] = context["analyzed_elements"]

            from browser.page_context import page_context_extractor
            page_context = await page_context_extractor.extract(page)
            context["page_context"] = page_context.to_dict()

            lower_goal = goal.lower()
            if any(k in lower_goal for k in ["read", "what does", "summarize", "tell me about"]):
                result = await web_page_reader.read(page, mode="normal")
                summary = await page_summarizer.summarize(page_context)
                return {"success": True, "task": task.to_dict(), "read": result, "summary": summary}

            if any(k in lower_goal for k in ["extract table", "get table", "show table"]):
                tables = await table_extractor.extract_tables(page)
                return {"success": True, "task": task.to_dict(), "tables": tables}

            resolved = await element_resolver.resolve(goal, page_context, page)
            if resolved:
                return {"success": True, "task": task.to_dict(), "resolved_element": resolved.to_dict()}

            return {"success": True, "task": task.to_dict(), "context": context}
        except Exception as exc:
            logger.error("Browser intelligence task failed: %s", exc)
            return {"success": False, "error": str(exc), "task": task.to_dict()}


browser_intelligence = BrowserIntelligenceOrchestrator()
