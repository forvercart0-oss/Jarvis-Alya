"""Browser Agent safety for JARVIS Phase 9."""

from __future__ import annotations

import re

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
_SENSITIVE_ACTIONS = {
    "submit", "send_message", "post", "purchase", "buy",
    "delete_account", "close_account", "transfer",
    "login", "signin", "authenticate",
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
        if any(word in action.lower() for word in _SENSITIVE_ACTIONS):
            return True
        return BrowserSafety.is_dangerous_action(action, url)

    @staticmethod
    def is_safe_read(action: str) -> bool:
        safe = {
            "navigate", "read", "screenshot", "list_tabs", "get_url",
            "back", "forward", "reload", "extract_links",
            "open_tab", "switch_tab", "close_tab",
        }
        return any(word in action.lower() for word in safe)

    @staticmethod
    def is_prompt_injection(text: str) -> bool:
        patterns = [
            r"ignore previous instructions",
            r"ignore all instructions",
            r"disregard.*rules",
            r"act as.*admin",
            r"you are now",
            r"new instructions",
            r"system override",
            r"developer mode",
            r"jailbreak",
        ]
        lower = text.lower()
        return any(re.search(p, lower) for p in patterns)

    @staticmethod
    def sanitize_page_content(text: str) -> str:
        if BrowserSafety.is_prompt_injection(text):
            return "[Content blocked: potential prompt injection detected]"
        return text

    @staticmethod
    def detect_captcha(text: str) -> bool:
        lower = text.lower()
        captcha_indicators = ["captcha", "recaptcha", "hcaptcha", "verify you are human", "prove you are not a robot"]
        return any(indicator in lower for indicator in captcha_indicators)

    @staticmethod
    def detect_mfa(text: str) -> bool:
        lower = text.lower()
        mfa_indicators = ["two-factor", "2fa", "verification code", "authenticator", "otp", "one-time password"]
        return any(indicator in lower for indicator in mfa_indicators)

    @staticmethod
    def detect_purchase(text: str, url: str = "") -> bool:
        combined = f"{text} {url}".lower()
        purchase_indicators = ["checkout", "payment", "purchase", "buy now", "place order", "cart", "billing"]
        return any(indicator in combined for indicator in purchase_indicators)

    @staticmethod
    def is_sensitive_field(field_type: str, field_name: str = "") -> bool:
        sensitive_types = {"password", "email", "tel", "creditcard"}
        sensitive_names = {"password", "passwd", "pwd", "secret", "api_key", "token", "ssn", "credit"}
        lower_type = field_type.lower()
        lower_name = field_name.lower()
        return lower_type in sensitive_types or any(name in lower_name for name in sensitive_names)
