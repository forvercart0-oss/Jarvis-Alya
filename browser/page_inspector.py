"""Page inspector for JARVIS Phase 25.

Extracts structured page representation:
title, URL, headings, paragraphs, links, buttons, inputs,
forms, images, tables, navigation, dialogs, ARIA roles.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.browser.page_inspector")


@dataclass
class PageSection:
    type: str = "unknown"
    text: str = ""
    elements: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "text": self.text,
            "elements": self.elements,
            "metadata": self.metadata,
        }


@dataclass
class InspectedPage:
    url: str = ""
    title: str = ""
    headings: list[dict[str, Any]] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    links: list[dict[str, Any]] = field(default_factory=list)
    buttons: list[dict[str, Any]] = field(default_factory=list)
    inputs: list[dict[str, Any]] = field(default_factory=list)
    forms: list[dict[str, Any]] = field(default_factory=list)
    images: list[dict[str, Any]] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)
    navigation: list[dict[str, Any]] = field(default_factory=list)
    dialogs: list[dict[str, Any]] = field(default_factory=list)
    aria_roles: list[dict[str, Any]] = field(default_factory=list)
    sections: list[PageSection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "headings": self.headings,
            "paragraphs": self.paragraphs,
            "links": self.links,
            "buttons": self.buttons,
            "inputs": self.inputs,
            "forms": self.forms,
            "images": self.images,
            "tables": self.tables,
            "navigation": self.navigation,
            "dialogs": self.dialogs,
            "aria_roles": self.aria_roles,
            "sections": [s.to_dict() for s in self.sections],
            "metadata": self.metadata,
        }


class PageInspector:
    def __init__(self):
        self._playwright_available = False
        try:
            import importlib.util
            self._playwright_available = importlib.util.find_spec("playwright") is not None
        except Exception:
            logger.debug("Playwright not available for page inspection")

    @property
    def available(self) -> bool:
        return self._playwright_available

    async def inspect(self, page: Any) -> InspectedPage:
        if not self._playwright_available or page is None:
            return InspectedPage()
        try:
            url = page.url
            title = await page.title()
            headings = await self._extract_headings(page)
            paragraphs = await self._extract_paragraphs(page)
            links = await self._extract_links(page)
            buttons = await self._extract_buttons(page)
            inputs = await self._extract_inputs(page)
            forms = await self._extract_forms(page)
            images = await self._extract_images(page)
            tables = await self._extract_tables(page)
            navigation = await self._extract_navigation(page)
            dialogs = await self._extract_dialogs(page)
            aria_roles = await self._extract_aria_roles(page)
            sections = await self._extract_sections(page)
            return InspectedPage(
                url=url,
                title=title,
                headings=headings,
                paragraphs=paragraphs,
                links=links,
                buttons=buttons,
                inputs=inputs,
                forms=forms,
                images=images,
                tables=tables,
                navigation=navigation,
                dialogs=dialogs,
                aria_roles=aria_roles,
                sections=sections,
            )
        except Exception as exc:
            logger.debug("Page inspection failed: %s", exc)
            return InspectedPage()

    async def _extract_headings(self, page: Any) -> list[dict[str, Any]]:
        try:
            return await page.evaluate("""
                () => Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6')).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    text: (el.innerText || '').trim(),
                    level: parseInt(el.tagName[1])
                })).slice(0, 20)
            """)
        except Exception:
            return []

    async def _extract_paragraphs(self, page: Any) -> list[str]:
        try:
            texts = await page.evaluate("""
                () => Array.from(document.querySelectorAll('p')).map(el => (el.innerText || '').trim())
            """)
            return [t for t in texts if t][:20]
        except Exception:
            return []

    async def _extract_links(self, page: Any) -> list[dict[str, Any]]:
        try:
            return await page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
                    text: (a.innerText || '').trim(),
                    href: a.href,
                    role: a.getAttribute('role') || ''
                })).filter(l => l.text && l.href).slice(0, 50)
            """)
        except Exception:
            return []

    async def _extract_buttons(self, page: Any) -> list[dict[str, Any]]:
        try:
            return await page.evaluate("""
                () => Array.from(document.querySelectorAll('button, [role="button"]')).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    text: (el.innerText || '').trim(),
                    aria_label: el.getAttribute('aria-label') || '',
                    type: el.getAttribute('type') || '',
                    enabled: !el.disabled,
                    visible: el.offsetParent !== null
                })).slice(0, 30)
            """)
        except Exception:
            return []

    async def _extract_inputs(self, page: Any) -> list[dict[str, Any]]:
        try:
            return await page.evaluate("""
                () => Array.from(document.querySelectorAll('input, textarea, select')).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    type: el.type || '',
                    name: el.name || '',
                    placeholder: el.placeholder || '',
                    aria_label: el.getAttribute('aria-label') || '',
                    value: el.value || '',
                    required: el.required,
                    enabled: !el.disabled,
                    visible: el.offsetParent !== null
                })).slice(0, 50)
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

    async def _extract_tables(self, page: Any) -> list[dict[str, Any]]:
        try:
            return await page.evaluate("""
                () => Array.from(document.querySelectorAll('table')).map(table => ({
                    headers: Array.from(table.querySelectorAll('th')).map(th => (th.innerText || '').trim()),
                    rows: Array.from(table.querySelectorAll('tbody tr, tr')).map(row => 
                        Array.from(row.querySelectorAll('td')).map(td => (td.innerText || '').trim())
                    )
                })).slice(0, 10)
            """)
        except Exception:
            return []

    async def _extract_navigation(self, page: Any) -> list[dict[str, Any]]:
        try:
            return await page.evaluate("""
                () => Array.from(document.querySelectorAll('nav, [role="navigation"], header nav')).map(nav => ({
                    text: (nav.innerText || '').trim(),
                    links: Array.from(nav.querySelectorAll('a[href]')).map(a => ({
                        text: (a.innerText || '').trim(),
                        href: a.href
                    })).slice(0, 10)
                })).slice(0, 5)
            """)
        except Exception:
            return []

    async def _extract_dialogs(self, page: Any) -> list[dict[str, Any]]:
        try:
            return await page.evaluate("""
                () => Array.from(document.querySelectorAll(
                    '[role="dialog"], dialog, .modal, [role="alertdialog"]'
                )).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    role: el.getAttribute('role') || '',
                    text: (el.innerText || '').trim(),
                    aria_label: el.getAttribute('aria-label') || ''
                })).slice(0, 10)
            """)
        except Exception:
            return []

    async def _extract_aria_roles(self, page: Any) -> list[dict[str, Any]]:
        try:
            return await page.evaluate("""
                () => Array.from(document.querySelectorAll('[role]')).map(el => ({
                    role: el.getAttribute('role'),
                    name: el.getAttribute('aria-label') || (el.innerText || '').trim() || '',
                    aria_describedby: el.getAttribute('aria-describedby') || '',
                    aria_live: el.getAttribute('aria-live') || ''
                })).slice(0, 30)
            """)
        except Exception:
            return []

    async def _extract_sections(self, page: Any) -> list[PageSection]:
        sections = []
        try:
            section_data = await page.evaluate("""
                () => Array.from(document.querySelectorAll('header, nav, main, aside, footer, section')).map(el => ({
                    type: el.tagName.toLowerCase(),
                    text: (el.innerText || '').trim(),
                    role: el.getAttribute('role') || ''
                }))
            """)
            for data in section_data:
                sections.append(PageSection(
                    type=data.get("type", "unknown"),
                    text=data.get("text", "")[:500],
                    metadata={"role": data.get("role", "")},
                ))
        except Exception:
            logger.debug("Failed to extract sections")
            return []


page_inspector = PageInspector()
