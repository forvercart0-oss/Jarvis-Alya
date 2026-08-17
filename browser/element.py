"""Element matching for JARVIS Phase 18."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("jarvis.browser.element")


def semantic_match(target: str, element: dict[str, Any]) -> float:
    score = 0.0
    lower_target = target.lower()
    text = (element.get("text") or "").lower()
    label = (element.get("label") or "").lower()
    placeholder = (element.get("placeholder") or "").lower()
    role = (element.get("role") or "").lower()
    href = (element.get("href") or "").lower()

    if lower_target in text:
        score += 0.8
    if lower_target in label:
        score += 0.7
    if lower_target in placeholder:
        score += 0.5
    if lower_target in role:
        score += 0.4
    if lower_target in href:
        score += 0.3

    words = re.findall(r"\w+", lower_target)
    for word in words:
        if word in text:
            score += 0.1
        if word in label:
            score += 0.08

    if element.get("visible") is False:
        score *= 0.5
    if element.get("enabled") is False:
        score *= 0.3

    return min(score, 1.0)


def find_best_element(target: str, elements: list[dict[str, Any]], threshold: float = 0.3) -> dict[str, Any] | None:
    best = None
    best_score = 0.0
    for el in elements:
        score = semantic_match(target, el)
        if score > best_score and score >= threshold:
            best = el
            best_score = score
    return best
