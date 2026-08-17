"""Page summarizer for JARVIS Phase 25.

Return: title, main topic, key points, important links, warnings
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.browser.page_summarizer")


class PageSummarizer:
    async def summarize(self, page_context: Any, page: Any = None) -> dict[str, Any]:
        title = getattr(page_context, "title", "") or ""
        url = getattr(page_context, "url", "") or ""
        headings = getattr(page_context, "headings", []) or []
        links = getattr(page_context, "links", []) or []

        key_points = []
        for h in headings[:5]:
            key_points.append(h.get("text", ""))
        paragraphs = getattr(page_context, "paragraphs", []) or []
        for p in paragraphs[:3]:
            if p.strip():
                key_points.append(p.strip()[:200])

        important_links = []
        for link in links[:10]:
            if link.get("text") and link.get("href"):
                important_links.append({"text": link["text"], "href": link["href"]})

        warnings = []
        if any("error" in (h.get("text", "").lower()) for h in headings):
            warnings.append("Page contains error-related headings")
        if any("captcha" in (link.get("text", "").lower() or "") for link in links):
            warnings.append("CAPTCHA detected")

        main_topic = headings[0].get("text", title) if headings else title

        return {
            "success": True,
            "title": title,
            "url": url,
            "main_topic": main_topic,
            "key_points": key_points[:10],
            "important_links": important_links[:10],
            "warnings": warnings,
        }


page_summarizer = PageSummarizer()
