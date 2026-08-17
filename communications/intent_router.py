"""Intent router for JARVIS Phase 26 communication."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("jarvis.communications.intent_router")


class CommunicationIntent:
    def __init__(self, intent: str, provider: str | None, target: str | None, confidence: float = 1.0):
        self.intent = intent
        self.provider = provider
        self.target = target
        self.confidence = confidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "provider": self.provider,
            "target": self.target,
            "confidence": self.confidence,
        }


class IntentRouter:
    def __init__(self):
        self._patterns = [
            (r"\b(check|read|show|any)\b.*\b(messages?|msgs?)\b", "read_messages", None),
            (r"\b(check|read|show|any)\b.*\b(email|emails|inbox)\b", "read_email", None),
            (r"\b(send|reply|respond)\b.*\b(message|msg)\b", "send_message", None),
            (r"\b(send|write|compose)\b.*\b(email)\b", "send_email", None),
            (r"\b(call|phone|dial)\b", "make_call", None),
            (r"\b(answer|accept)\b.*\b(call)\b", "answer_call", None),
            (r"\b(reject|decline|hang\s*up|end)\b.*\b(call)?\b", "hangup_call", None),
            (r"\b(search|find|look\s*for)\b.*\b(messages?|emails?)\b", "search_messages", None),
            (r"\b(summarize|summary|brief)\b.*\b(email|emails|messages?)\b", "summarize", None),
            (r"\b(unread|new)\b.*\b(messages?|emails?)\b", "read_unread", None),
            (r"\b(important|urgent)\b.*\b(email|emails|messages?)\b", "read_important", None),
            (r"\b(notify|alert|tell)\b.*\bwhen\b.*\b(message|email)\b", "set_notification", None),
        ]

    def route(self, text: str) -> CommunicationIntent:
        lower = text.lower()
        for pattern, intent, default_provider in self._patterns:
            if re.search(pattern, lower):
                provider = self._detect_provider(lower)
                target = self._extract_target(text)
                return CommunicationIntent(intent=intent, provider=provider, target=target, confidence=0.8)
        return CommunicationIntent(intent="unknown", provider=None, target=None, confidence=0.0)

    def _detect_provider(self, text: str) -> str | None:
        providers = {
            "whatsapp": "whatsapp",
            "telegram": "telegram",
            "discord": "discord",
            "slack": "slack",
            "email": "email",
            "gmail": "gmail",
            "outlook": "outlook",
            "call": "phone",
            "phone": "phone",
        }
        for keyword, provider in providers.items():
            if keyword in text:
                return provider
        return None

    def _extract_target(self, text: str) -> str | None:
        match = re.search(r"(?:to|from|about|for)\s+([A-Za-z0-9_\s]+?)(?:\s+(?:and|that|who|what|where|when|why|how|$))", text)
        if match:
            return match.group(1).strip()
        words = text.split()
        for word in words:
            if len(word) > 2 and word.lower() not in ("the", "and", "for", "with", "from", "about", "check", "read", "show", "any", "send", "reply", "call", "phone", "search", "find", "look", "message", "email", "inbox", "messages", "emails"):
                return word
        return None


intent_router = IntentRouter()
