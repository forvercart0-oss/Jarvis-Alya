"""Source extraction for Deep Research.

Extracts content from web pages using Playwright browser tools.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.research.extractor")


class SourceExtractor:
    async def extract(self, url: str, max_chars: int = 8000) -> dict[str, Any]:
        try:
            from browser.manager import browser_manager
            page = await browser_manager.get_page()
            if page is None:
                return {"success": False, "error": "No browser page available"}
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            title = await page.title()
            content = await page.evaluate("document.body.innerText")
            content = content[:max_chars]
            return {"success": True, "title": title, "content": content, "url": url}
        except Exception as exc:
            logger.warning("Extraction failed for %s: %s", url, exc)
            return {"success": False, "error": str(exc), "url": url}
