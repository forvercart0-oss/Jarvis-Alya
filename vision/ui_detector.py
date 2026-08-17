"""UI element detection for JARVIS Phase 17."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("jarvis.vision.ui_detector")

_ELEMENT_PATTERNS = [
    ("button", re.compile(r"\b(button|btn|submit|ok|cancel|yes|no|close|save|delete|login|sign in|signup|register)\b", re.I)),
    ("input", re.compile(r"\b(input|textbox|field|search|email|password|username)\b", re.I)),
    ("link", re.compile(r"\b(link|href|anchor|navigate|here|click here)\b", re.I)),
    ("menu", re.compile(r"\b(menu|dropdown|select|option|list|navigation|nav)\b", re.I)),
    ("tab", re.compile(r"\b(tab|tablist|tabpanel)\b", re.I)),
    ("checkbox", re.compile(r"\b(checkbox|check|toggle|switch)\b", re.I)),
    ("radio", re.compile(r"\b(radio|radiogroup)\b", re.I)),
    ("dialog", re.compile(r"\b(dialog|modal|popup|alert|confirm|prompt)\b", re.I)),
    ("navigation", re.compile(r"\b(nav|navbar|sidebar|header|footer|breadcrumb|pagination)\b", re.I)),
    ("icon", re.compile(r"\b(icon|svg|image|img|logo|avatar|badge)\b", re.I)),
]


def detect_ui_elements(ocr_text: str, elements: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    detected: list[dict[str, Any]] = []
    for element_type, pattern in _ELEMENT_PATTERNS:
        matches = list(pattern.finditer(ocr_text or ""))
        for match in matches:
            detected.append({
                "type": element_type,
                "label": match.group(0),
                "confidence": 0.7,
                "source": "pattern",
            })
    if elements:
        for el in elements:
            if el.get("type") and el.get("label"):
                detected.append({
                    "type": el["type"],
                    "label": el["label"],
                    "confidence": float(el.get("confidence", 0.7)),
                    "source": "vision",
                })
    return detected


def classify_command(text: str) -> str | None:
    lower = text.lower().strip()
    if any(k in lower for k in ["read", "what is", "what does", "explain", "describe", "look at"]):
        return "read"
    if any(k in lower for k in ["click", "press", "select", "choose", "tap"]):
        return "click"
    if any(k in lower for k in ["type", "enter", "fill", "input"]):
        return "type"
    if any(k in lower for k in ["scroll", "move down", "move up"]):
        return "scroll"
    if any(k in lower for k in ["find", "search", "locate", "where is"]):
        return "find"
    if any(k in lower for k in ["open", "launch", "start"]):
        return "open"
    return None
