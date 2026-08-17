"""Sensitive screen detection and secret redaction for JARVIS Phase 17."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("jarvis.vision.sensitive")

_SENSITIVE_PATTERNS = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "email"),
    (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "credit_card"),
    (re.compile(r"\b\d{3}[\s-]?\d{2}[\s-]?\d{4}\b"), "ssn"),
    (re.compile(r"\b(api[_-]?key|apikey|token|secret|password|passwd|pwd|private[_-]?key)\b", re.I), "secret_keyword"),
    (re.compile(r"\b(GROQ|OPENAI|ANTHROPIC|GEMINI|OPENROUTER|BEARER|AUTH|AUTHORIZATION)[\s:]+[A-Za-z0-9\-_.]+", re.I), "auth_header"),
]

_SENSITIVE_UI_KEYWORDS = [
    "password", "credit card", "cvv", "pin", "bank", "login", "sign in",
    "2fa", "totp", "backup codes", "private key", "api key", "secret",
]


class SensitiveScreenDetector:
    """Detects potentially sensitive content in screenshots/OCR."""

    def is_sensitive_text(self, text: str) -> tuple[bool, list[str]]:
        hits = []
        for pattern, label in _SENSITIVE_PATTERNS:
            if pattern.search(text):
                hits.append(label)
        return bool(hits), hits

    def is_sensitive_screen(self, ocr_text: str, window_title: str = "") -> tuple[bool, str]:
        combined = f"{window_title} {ocr_text}".lower()
        for keyword in _SENSITIVE_UI_KEYWORDS:
            if keyword in combined:
                return True, keyword
        hits, _ = self.is_sensitive_text(ocr_text)
        if hits:
            return True, ",".join(hits)
        return False, ""

    def redact(self, text: str) -> str:
        redacted = text
        for pattern, _ in _SENSITIVE_PATTERNS:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted


sensitive_detector = SensitiveScreenDetector()
