"""Call permissions."""

from __future__ import annotations

from enum import Enum


class CallPermissionLevel(str, Enum):
    DISABLED = "disabled"
    CONFIRMATION = "confirmation"
    ALLOWED = "allowed"


class CallPermissions:
    def __init__(self, settings):
        self.settings = settings
        self._outgoing = CallPermissionLevel.CONFIRMATION
        self._incoming = CallPermissionLevel.ALLOWED
        self._assist = CallPermissionLevel.DISABLED

    @property
    def outgoing(self) -> CallPermissionLevel:
        return self._outgoing

    @outgoing.setter
    def outgoing(self, value: CallPermissionLevel):
        self._outgoing = value

    @property
    def incoming(self) -> CallPermissionLevel:
        return self._incoming

    @incoming.setter
    def incoming(self, value: CallPermissionLevel):
        self._incoming = value

    @property
    def assist(self) -> CallPermissionLevel:
        return self._assist

    @assist.setter
    def assist(self, value: CallPermissionLevel):
        self._assist = value
