"""DOM analyzer for JARVIS Phase 25.

Analyzes DOM elements with:
id, tag, role, text, aria-label, placeholder, name, value,
href, visible, enabled, bounding_box, selector candidates
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.browser.dom_analyzer")


@dataclass
class AnalyzedElement:
    id: str = ""
    tag: str = ""
    role: str = ""
    text: str = ""
    aria_label: str = ""
    placeholder: str = ""
    name: str = ""
    value: str = ""
    href: str = ""
    visible: bool = True
    enabled: bool = True
    bounding_box: dict[str, int] = field(default_factory=dict)
    selectors: list[str] = field(default_factory=list)
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tag": self.tag,
            "role": self.role,
            "text": self.text,
            "aria_label": self.aria_label,
            "placeholder": self.placeholder,
            "name": self.name,
            "value": self.value,
            "href": self.href,
            "visible": self.visible,
            "enabled": self.enabled,
            "bounding_box": self.bounding_box,
            "selectors": self.selectors,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class DOMAnalyzer:
    def __init__(self):
        self._playwright_available = False
        try:
            import importlib.util

            self._playwright_available = importlib.util.find_spec("playwright") is not None
        except Exception:
            logger.debug("Playwright not available for DOM analysis")

    @property
    def available(self) -> bool:
        return self._playwright_available

    async def analyze(self, page: Any) -> list[AnalyzedElement]:
        if not self._playwright_available or page is None:
            return []
        try:
            elements = await page.evaluate("""
                () => {
                    const results = [];
                    const selectors = document.querySelectorAll(
                        'button, input, select, textarea, a[href], [role="button"], '
                    '[role="link"], [role="textbox"], [role="combobox"], '
                    '[role="checkbox"], [role="radio"], [role="tab"], '
                    '[role="menu"], [role="menuitem"]'
                    );
                    for (const el of selectors) {
                        const rect = el.getBoundingClientRect();
                        const candidates = [];
                        if (el.id) candidates.push('#' + CSS.escape(el.id));
                        if (el.tagName) candidates.push(el.tagName.toLowerCase());
                        if el.getAttribute("role"):
                            candidates.push('[role="' + el.getAttribute("role") + '"]')
                        if el.name:
                            candidates.push('[name="' + el.name + '"]')
                        if el.getAttribute("aria-label"):
                            candidates.push(
                                '[aria-label="' + el.getAttribute("aria-label") + '"]'
                            )
                        results.push({
                            id: el.id || '',
                            tag: el.tagName.toLowerCase(),
                            role: el.getAttribute('role') || '',
                            text: (el.innerText || el.textContent || '').trim(),
                            aria_label: el.getAttribute('aria-label') || '',
                            placeholder: el.placeholder || '',
                            name: el.name || '',
                            value: el.value || '',
                            href: el.href || '',
                            visible: el.offsetParent !== null,
                            enabled: !el.disabled,
                            bounding_box: {
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                            },
                            selectors: candidates
                        });
                    }
                    return results.slice(0, 200);
                }
            """)
            return [AnalyzedElement(**e) for e in elements]
        except Exception as exc:
            logger.debug("DOM analysis failed: %s", exc)
            return []

    def find_by_selector(self, elements: list[AnalyzedElement], selector: str) -> AnalyzedElement | None:
        for el in elements:
            if selector in el.selectors:
                return el
        return None

    def find_by_text(self, elements: list[AnalyzedElement], text: str) -> AnalyzedElement | None:
        lower = text.lower()
        best = None
        best_score = 0.0
        for el in elements:
            score = 0.0
            if lower in el.text.lower():
                score = 0.9
            elif lower in el.aria_label.lower():
                score = 0.8
            elif lower in el.placeholder.lower():
                score = 0.6
            elif lower in el.name.lower():
                score = 0.5
            if score > best_score:
                best = el
                best_score = score
        return best if best_score >= 0.3 else None


dom_analyzer = DOMAnalyzer()
