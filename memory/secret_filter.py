"""Memory privacy: secret detection and filtering.

JARVIS must never store API keys, passwords, tokens, private credentials,
authentication cookies, or sensitive secrets in long-term memory. If a secret
is detected, the memory is not saved.
"""

from __future__ import annotations

import re

# Strong signals: values that are almost certainly secrets.
_STRONG_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(sk|pk|ghp|gho|xox[baprs]|AKIA|wss?)[-_][A-Za-z0-9_-]{12,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),  # Google API key
    re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{5,}\b"),  # JWT
    re.compile(r"(password|passwd|pwd)\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"(api[_-]?key|secret|token)\s*[=:]\s*[A-Za-z0-9_\-./]{8,}", re.IGNORECASE),
    re.compile(r"authorization\s*[=:]\s*bearer\s+\S+", re.IGNORECASE),
    re.compile(r"(client.?secret|cookie)\s*[=:]\s*\S+", re.IGNORECASE),
]

# Weak hints: mention the word but may be in a benign sentence.
_WEAK_HINTS: tuple[str, ...] = (
    "password",
    "passwd",
    "api key",
    "apikey",
    "api_key",
    "secret",
    "token",
    "bearer",
    "private key",
    "credentials",
)

_BENIGN_PHRASES: tuple[str, ...] = (
    "change my password",
    "reset my password",
    "forgot my password",
    "remember to change my password",
    "password manager",
)


def scan_for_secrets(text: str) -> list[str]:
    """Return matched secret-hint descriptions, or [] when clean."""
    if not text:
        return []
    if any(phrase in text.lower() for phrase in _BENIGN_PHRASES):
        return []
    for pattern in _STRONG_PATTERNS:
        if pattern.search(text):
            return [f"matches {pattern.pattern[:40]}"]
    if any(hint in text.lower() for hint in _WEAK_HINTS):
        return ["contains secret-like wording"]
    return []


def contains_secret(text: str) -> bool:
    """True when the text should NOT be persisted to memory."""
    return bool(scan_for_secrets(text))


def filter_memory_text(text: str) -> tuple[str, bool]:
    """Return (safe_text, saved).

    When secrets are detected, returns ("", False) so callers refuse to save.
    """
    if contains_secret(text):
        return "", False
    return text, True
