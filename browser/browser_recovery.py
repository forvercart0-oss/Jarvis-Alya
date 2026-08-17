"""Browser recovery engine for JARVIS Phase 25.

If selector fails: try semantic locator, accessibility, vision,
re-evaluate page. Never blindly retry same action indefinitely.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.browser.browser_recovery")


class BrowserRecoveryEngine:
    def __init__(self):
        self._fallback_chain = ["semantic", "accessibility", "vision", "re_evaluate"]

    async def recover(self, failed_action: dict[str, Any], context: Any, page: Any = None) -> dict[str, Any]:
        action_type = failed_action.get("action_type", "")
        target = failed_action.get("target", "")
        error = failed_action.get("error", "")

        logger.info("Recovering failed browser action: %s %s -> %s", action_type, target, error)

        if action_type == "click":
            return await self._recover_click(target, context, page)
        if action_type == "type":
            return await self._recover_type(target, context, page)
        if action_type == "navigate":
            return await self._recover_navigate(target, page)

        return {"success": False, "error": "No recovery strategy for action", "action_type": action_type}

    async def _recover_click(self, target: str, context: Any, page: Any = None) -> dict[str, Any]:
        try:
            from browser.element_resolver import element_resolver
            resolved = await element_resolver.resolve(target, context, page)
            if resolved and resolved.selector:
                return {
                    "success": True,
                    "recovery": "semantic",
                    "selector": resolved.selector,
                    "element": resolved.to_dict(),
                }
            return {"success": False, "error": f"Cannot recover click for '{target}'", "recovery": "failed"}
        except Exception as exc:
            return {"success": False, "error": str(exc), "recovery": "error"}

    async def _recover_type(self, target: str, context: Any, page: Any = None) -> dict[str, Any]:
        try:
            from browser.element_resolver import element_resolver
            resolved = await element_resolver.resolve(target, context, page)
            if resolved and resolved.selector:
                return {
                    "success": True,
                    "recovery": "semantic",
                    "selector": resolved.selector,
                    "element": resolved.to_dict(),
                }
            return {"success": False, "error": f"Cannot recover type for '{target}'", "recovery": "failed"}
        except Exception as exc:
            return {"success": False, "error": str(exc), "recovery": "error"}

    async def _recover_navigate(self, target: str, page: Any = None) -> dict[str, Any]:
        if page and hasattr(page, "goto"):
            try:
                await page.goto(target, wait_until="domcontentloaded", timeout=30000)
                return {"success": True, "recovery": "retry_navigate", "url": target}
            except Exception as exc:
                return {"success": False, "error": str(exc), "recovery": "failed"}
        return {"success": False, "error": "Page not available for navigation recovery", "recovery": "failed"}


browser_recovery_engine = BrowserRecoveryEngine()
