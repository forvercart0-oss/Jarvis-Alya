"""Call control architecture.

Uses legitimate supported interfaces only.
Never bypasses security, authentication, encryption, or platform restrictions.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger("jarvis.calls")

logger = logging.getLogger("jarvis.calls")


class CallProvider(ABC):
    @abstractmethod
    async def call(self, contact_identifier: str) -> dict:
        pass

    @abstractmethod
    async def hangup(self, call_id: str) -> dict:
        pass

    @abstractmethod
    async def accept(self, call_id: str) -> dict:
        pass

    @abstractmethod
    async def decline(self, call_id: str) -> dict:
        pass

    @abstractmethod
    async def health_check(self) -> dict:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass
