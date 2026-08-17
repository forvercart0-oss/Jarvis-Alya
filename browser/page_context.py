"""Page context extraction for JARVIS Phase 18."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.browser.page_context")


@dataclass
class PageElement:
    type: str = "unknown"
    role: str = ""
    text: str = ""
    label: str = ""
    placeholder: str = ""
    href: str = ""
    bounding_box: dict[str, int] = field(default_factory=dict)
    visible: bool = True
    enabled: bool = True
    confidence: float = 1.0
    selector: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "role": self.role,
            "text": self.text,
            "label": self.label,
            "placeholder": self.placeholder,
            "href": self.href,
            "bounding_box": self.bounding_box,
            "visible": self.visible,
            "enabled": self.enabled,
            "confidence": self.confidence,
            "selector": self.selector,
            "metadata": self.metadata,
        }


@dataclass
class PageContext:
    url: str = ""
    title: str = ""
    dom_summary: str = ""
    accessibility_tree: str = ""
    visible_text: str = ""
    interactive_elements: list[PageElement] = field(default_factory=list)
    forms: list[dict[str, Any]] = field(default_factory=list)
    links: list[dict[str, Any]] = field(default_factory=list)
    buttons: list[PageElement] = field(default_factory=list)
    inputs: list[PageElement] = field(default_factory=list)
    images: list[dict[str, Any]] = field(default_factory=list)
    loading: bool = False
    backend: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "dom_summary": self.dom_summary,
            "accessibility_tree": self.accessibility_tree,
            "visible_text": self.visible_text,
            "interactive_elements": [e.to_dict() for e in self.interactive_elements],
            "forms": self.forms,
            "links": self.links,
            "buttons": [e.to_dict() for e in self.buttons],
            "inputs": [e.to_dict() for e in self.inputs],
            "images": self.images,
            "loading": self.loading,
            "backend": self.backend,
            "metadata": self.metadata,
        }


class PageContextExtractor:
    """Extracts structured page context from browser pages."""

    def __init__(self):
        self._playwright_available = False
        try:
            import importlib.util
            self._playwright_available = importlib.util.find_spec("playwright") is not None
        except Exception:
            logger.debug("Playwright not available for page context extraction")

    @property
    def available(self) -> bool:
        return self._playwright_available

    async def extract(self, page: Any) -> PageContext:
        if not self._playwright_available or page is None:
            return PageContext()
        try:
            url = page.url
            title = await page.title()
            text = await page.evaluate("() => document.body.innerText") if hasattr(page, 'evaluate') else ""
            elements = await self._extract_elements(page)
            return PageContext(
                url=url,
                title=title,
                visible_text=text[:4000] if text else "",
                interactive_elements=elements,
                buttons=[e for e in elements if e.type == "button"],
                inputs=[e for e in elements if e.type in ("input", "textarea", "select")],
                links=await self._extract_links(page),
                forms=await self._extract_forms(page),
                images=await self._extract_images(page),
                backend="playwright",
            )
        except Exception as exc:
            logger.debug("Page context extraction failed: %s", exc)
            return PageContext()

    async def _extract_elements(self, page: Any) -> list[PageElement]:
        try:
            elements = await page.evaluate("""
                () => Array.from(document.querySelectorAll(
                    'button, input, select, textarea, a[href], [role="button"], [role="link"], [role="textbox"]'
                )).map(el => ({
                    type: el.tagName.toLowerCase(),
                    role: el.getAttribute('role') || '',
                    text: (el.innerText || el.textContent || '').trim(),
                    label: el.getAttribute('aria-label') || '',
                    placeholder: el.getAttribute('placeholder') || '',
                    href: el.href || '',
                     visible: el.offsetParent !== null,
                     enabled: !el.disabled,
                     selector: el.tagName.toLowerCase()
                     + (el.id ? '#' + el.id : '')
                     + (el.className ? '.' + el.className.split(' ').join('.') : '')
                 })).slice(0, 100)
            """)
            return [PageElement(**e) for e in elements]
        except Exception:
            return []

    async def _extract_links(self, page: Any) -> list[dict[str, Any]]:
        try:
            return await page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
                    text: (a.innerText || '').trim(),
                    href: a.href
                })).filter(l => l.text && l.href).slice(0, 50)
            """)
        except Exception:
            return []

    async def _extract_forms(self, page: Any) -> list[dict[str, Any]]:
        try:
            return await page.evaluate("""
                () => Array.from(document.querySelectorAll('form')).map(f => ({
                    action: f.action || '',
                    method: f.method || 'get',
                    inputs: Array.from(f.querySelectorAll('input, select, textarea')).map(i => ({
                        type: i.type || i.tagName.toLowerCase(),
                        name: i.name || '',
                        placeholder: i.placeholder || '',
                        required: i.required
                    }))
                })).slice(0, 20)
            """)
        except Exception:
            return []

    async def _extract_images(self, page: Any) -> list[dict[str, Any]]:
        try:
            return await page.evaluate("""
                () => Array.from(document.querySelectorAll('img')).map(img => ({
                    src: img.src,
                    alt: img.alt || '',
                    visible: img.offsetParent !== null
                })).filter(i => i.src).slice(0, 30)
            """)
        except Exception:
            return []

    def detect_login_page(self, context: PageContext) -> bool:
        combined = f"{context.title} {context.visible_text} {context.dom_summary}".lower()
        login_indicators = ["login", "sign in", "signin", "log in", "authenticate", "password", "enter your email"]
        return any(indicator in combined for indicator in login_indicators)

    def detect_captcha(self, context: PageContext) -> bool:
        combined = f"{context.visible_text} {context.dom_summary}".lower()
        captcha_indicators = ["captcha", "recaptcha", "hcaptcha", "verify you are human", "prove you are not a robot"]
        return any(indicator in combined for indicator in captcha_indicators)

    def detect_mfa(self, context: PageContext) -> bool:
        combined = f"{context.visible_text} {context.dom_summary}".lower()
        mfa_indicators = ["two-factor", "2fa", "verification code", "authenticator", "otp", "one-time password"]
        return any(indicator in combined for indicator in mfa_indicators)

    def detect_purchase_page(self, context: PageContext) -> bool:
        combined = f"{context.title} {context.visible_text} {context.url}".lower()
        purchase_indicators = ["checkout", "payment", "purchase", "buy now", "place order", "cart", "billing"]
        return any(indicator in combined for indicator in purchase_indicators)

    def detect_destructive_action(self, context: PageContext, action: str) -> bool:
        destructive = ["delete", "remove", "close account", "unpublish", "deactivate", "permanently delete"]
        lower_action = action.lower()
        return any(d in lower_action for d in destructive)


page_context_extractor = PageContextExtractor()
