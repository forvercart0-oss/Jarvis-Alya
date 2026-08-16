"""Browser Agent safety for JARVIS Phase 3."""

from __future__ import annotations

import re
from typing import Any

from safety.classifier import SafetyCategory, classify_request

_BROWSER_DANGEROUS = re.compile(
    r"(?:transfer|wire|send).*(?:money|payment|bank|crypto|bitcoin)",
    re.IGNORECASE,
)
_SENSITIVE_DOMAINS = {
    "bank",
    "paypal",
    "stripe",
    "coinbase",
    "binance",
    "github.com/settings",
    "accounts.google.com",
}


class BrowserSafety:
    @staticmethod
    def is_dangerous_action(action: str, url: str = "") -> bool:
        if _BROWSER_DANGEROUS.search(action):
            return True
        lower_url = url.lower()
        return any(domain in lower_url for domain in _SENSITIVE_DOMAINS)

    @staticmethod
    def requires_confirmation(action: str, url: str = "") -> bool:
        dangerous = {
            "submit", "send_message", "post", "purchase", "buy",
            "delete_account", "close_account", "transfer",
        }
        if any(word in action.lower() for word in dangerous):
            return True
        return BrowserSafety.is_dangerous_action(action, url)

    @staticmethod
    def is_safe_read(action: str) -> bool:
        safe = {"navigate", "read", "screenshot", "list_tabs", "get_url", "back", "forward", "reload"}
        return any(word in action.lower() for word in safe)
