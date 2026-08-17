"""Contact manager for JARVIS Phase 26."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.communications.contacts")


class ContactManager:
    def __init__(self):
        self._contacts: dict[str, Any] = {}
        self._aliases: dict[str, str] = {}

    def add_contact(self, contact: Any) -> None:
        self._contacts[contact.contact_id] = contact
        self._aliases[contact.name.lower()] = contact.contact_id
        for alias in contact.aliases:
            self._aliases[alias.lower()] = contact.contact_id

    def remove_contact(self, contact_id: str) -> None:
        contact = self._contacts.pop(contact_id, None)
        if contact:
            self._aliases.pop(contact.name.lower(), None)
            for alias in contact.aliases:
                self._aliases.pop(alias.lower(), None)

    def resolve(self, query: str) -> list[Any]:
        lower = query.lower()
        matches = []
        for contact_id, contact in self._contacts.items():
            if lower in contact.name.lower():
                matches.append(contact)
                continue
            for alias in contact.aliases:
                if lower in alias.lower():
                    matches.append(contact)
                    break
        return matches

    def get(self, contact_id: str) -> Any | None:
        return self._contacts.get(contact_id)

    def list_all(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self._contacts.values()]

    def get_groups(self) -> dict[str, list[Any]]:
        groups: dict[str, list[Any]] = {}
        for contact in self._contacts.values():
            for tag in contact.tags:
                groups.setdefault(tag, []).append(contact)
        return groups


contact_manager = ContactManager()
