"""Web page reader for JARVIS Phase 25.

Modes: brief, normal, detailed
Extracts meaningful content instead of navigation/footer noise.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("jarvis.browser.page_reader")


class WebPageReader:
    def __init__(self):
        self._noise_patterns = [
            re.compile(r"\s*[-]\s*$"),
            re.compile(r"^\s*(skip to|skip navigation|menu|close|search|submit)\b", re.I),
            re.compile(r"^\s*(cookie|privacy|terms|copyright|all rights reserved)\b", re.I),
        ]

    def _clean_text(self, text: str) -> str:
        lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if any(p.match(stripped) for p in self._noise_patterns):
                continue
            lines.append(stripped)
        return "\n".join(lines)

    async def read(self, page: Any, mode: str = "normal") -> dict[str, Any]:
        if page is None:
            return {"success": False, "error": "No page available"}
        try:
            title = await page.title()
            url = page.url
            full_text = await page.evaluate("() => document.body.innerText") if hasattr(page, "evaluate") else ""
            cleaned = self._clean_text(full_text)
            if mode == "brief":
                text = cleaned[:500]
            elif mode == "detailed":
                text = cleaned[:8000]
            else:
                text = cleaned[:3000]
            return {
                "success": True,
                "url": url,
                "title": title,
                "mode": mode,
                "text": text,
                "length": len(cleaned),
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}


web_page_reader = WebPageReader()
