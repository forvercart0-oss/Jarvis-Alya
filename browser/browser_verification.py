"""Browser verification for JARVIS Phase 25.

Verifies browser action results.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.browser.browser_verification")


class BrowserVerifier:
    async def verify_navigation(self, page: Any, expected_url: str) -> dict[str, Any]:
        try:
            actual_url = page.url if hasattr(page, "url") else ""
            success = expected_url in actual_url if expected_url else True
            return {"success": success, "expected_url": expected_url, "actual_url": actual_url}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def verify_element_present(self, page: Any, selector: str) -> dict[str, Any]:
        try:
            if hasattr(page, "locator"):
                locator = page.locator(selector)
                count = await locator.count()
                return {"success": count > 0, "selector": selector, "count": count}
            return {"success": False, "error": "Page locator not available"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def verify_text_present(self, page: Any, text: str) -> dict[str, Any]:
        try:
            if hasattr(page, "locator"):
                locator = page.locator(f"text={text}")
                count = await locator.count()
                return {"success": count > 0, "text": text, "count": count}
            return {"success": False, "error": "Page locator not available"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def verify_state_changed(self, before_state: dict[str, Any], after_state: dict[str, Any]) -> dict[str, Any]:
        changes = []
        if before_state.get("url") != after_state.get("url"):
            changes.append("url")
        if before_state.get("title") != after_state.get("title"):
            changes.append("title")
        if before_state.get("text") != after_state.get("text"):
            changes.append("text")
        return {"success": bool(changes), "changes": changes, "has_changes": bool(changes)}


browser_verifier = BrowserVerifier()
