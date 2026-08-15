"""Text normalization for multilingual input."""

from __future__ import annotations

import re


def normalize_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def normalize_for_stt(text: str, lang: str) -> str:
    """Prepare STT output for AI processing."""
    text = normalize_whitespace(text)
    if lang == 'ur':
        return text
    if lang == 'roman_urdu':
        return text
    return text
