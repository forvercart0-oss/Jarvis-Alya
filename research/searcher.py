"""Multi-source web search for Deep Research.

Uses the existing web search tool and browser automation to gather
sources from reputable sites. Prefers official documentation, government
sources, academic papers, research organizations, reputable news, and
technical documentation.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from tools.web import WebSearchTool

logger = logging.getLogger("jarvis.research.searcher")


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def _classify_source(url: str, title: str = "") -> str:
    url_lower = url.lower()
    if any(d in url_lower for d in (".gov", ".edu", "arxiv.org", "scholar.google")):
        return "official"
    if any(d in url_lower for d in ("github.com", "docs.", "developer.", "api.")):
        return "technical"
    if any(d in url_lower for d in ("wikipedia.org", "britannica.com")):
        return "reference"
    if any(d in url_lower for d in ("ieee.org", "acm.org", "springer.com", "nature.com", "science.org")):
        return "academic"
    if any(d in url_lower for d in ("reuters.com", "apnews.com", "bbc.com", "npr.org")):
        return "news"
    return "web"


class ResearchSearcher:
    def __init__(self, max_sources: int = 20, timeout: float = 15.0):
        self.max_sources = max_sources
        self.timeout = timeout
        self._tool = WebSearchTool()
        self._seen_urls: set[str] = set()

    async def search(self, query: str, on_found: Any = None) -> list[dict[str, Any]]:
        """Run multiple search queries and collect unique sources."""
        queries = self._expand_query(query)
        tasks = [self._run_search(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        sources: list[dict[str, Any]] = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning("Search failed: %s", result)
                continue
            for item in result:
                url = item.get("url", "")
                if url and url not in self._seen_urls:
                    self._seen_urls.add(url)
                    sources.append(item)
                    if on_found:
                        on_found(item)
                    if len(sources) >= self.max_sources:
                        break
            if len(sources) >= self.max_sources:
                break
        return sources

    def _expand_query(self, query: str) -> list[str]:
        q = query.strip()
        return [
            q,
            f"{q} overview",
            f"{q} latest research",
            f"{q} official documentation",
        ]

    async def _run_search(self, query: str) -> list[dict[str, Any]]:
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self._search_blocking, query),
                timeout=self.timeout,
            )
            return result
        except TimeoutError:
            logger.warning("Search timeout for query: %s", query)
            return []
        except Exception as exc:
            logger.warning("Search error for query '%s': %s", query, exc)
            return []

    def _search_blocking(self, query: str) -> list[dict[str, Any]]:
        try:
            import re as _re

            import httpx
            url = "https://html.duckduckgo.com/html/"
            headers = {"User-Agent": "Mozilla/5.0"}
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, data={"q": query}, headers=headers)
                if response.status_code != 200:
                    return []
                text = response.text
                titles = _re.findall(r'<a[^>]+class="result__a"[^>]*>(.*?)</a>', text, _re.DOTALL)
                snippets = _re.findall(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', text, _re.DOTALL)
                urls = _re.findall(r'<a[^>]+class="result__a"[^>]*href="([^"]+)"', text)
                items = []
                for i, title in enumerate(titles):
                    clean_title = _re.sub(r"<.*?>", "", title).strip()
                    clean_snippet = _re.sub(r"<.*?>", "", snippets[i]).strip() if i < len(snippets) else ""
                    raw_url = urls[i] if i < len(urls) else ""
                    if raw_url.startswith("//duckduckgo.com/l/?uddg="):
                        import urllib.parse
                        encoded = raw_url.split("uddg=")[-1].split("&")[0]
                        raw_url = urllib.parse.unquote(encoded)
                    if clean_title and raw_url:
                        items.append({
                            "title": clean_title,
                            "url": raw_url,
                            "snippet": clean_snippet,
                            "source_type": _classify_source(raw_url, clean_title),
                            "publisher": self._extract_publisher(raw_url),
                        })
                return items
        except Exception as exc:
            logger.warning("Blocking search error: %s", exc)
            return []

    def _extract_publisher(self, url: str) -> str:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""
