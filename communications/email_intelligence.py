"""Email intelligence for JARVIS Phase 26."""

from __future__ import annotations

import logging
import re
from typing import Any

from communications.models import MessageImportance

logger = logging.getLogger("jarvis.communications.email_intelligence")


class EmailIntelligence:
    def __init__(self):
        self._important_senders = {"github", "gitlab", "jira", "slack", "notion", "linear"}
        self._spam_keywords = ["unsubscribe", "promo", "sale", "winner", "lottery", "free money", "act now"]
        self._notification_keywords = ["notification", "alert", "update", "reminder"]

    def classify(self, email: dict[str, Any]) -> str:
        sender = (email.get("sender") or "").lower()
        subject = (email.get("subject") or "").lower()
        text = (email.get("text") or "").lower()
        combined = f"{sender} {subject} {text}"

        for keyword in self._spam_keywords:
            if keyword in combined:
                return MessageImportance.SPAM
        for keyword in self._notification_keywords:
            if keyword in combined:
                return MessageImportance.NOTIFICATION
        for important in self._important_senders:
            if important in sender:
                return MessageImportance.IMPORTANT
        if re.search(r"\b(urgent|important|action required|please review)\b", combined):
            return MessageImportance.IMPORTANT
        return MessageImportance.NORMAL

    def summarize(self, email: dict[str, Any]) -> dict[str, Any]:
        return {
            "sender": email.get("sender", "Unknown"),
            "subject": email.get("subject", "No subject"),
            "summary": (email.get("text") or "")[:200],
            "importance": self.classify(email),
            "date": email.get("timestamp", ""),
        }


email_intelligence = EmailIntelligence()
