"""Memory boundaries: durable store and optional semantic index."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class MemoryStore(ABC):
    """Boundary for durable, queryable long-term memory records.

    Implemented by SQLiteMemory. Keyword recall is always available.
    """

    @abstractmethod
    def remember(self, content: str, category: str = "general", key_override: str = "") -> dict:
        """Persist a memory and return the stored record (includes its id)."""

    @abstractmethod
    def forget(self, query: str) -> int:
        """Delete memories whose key/value match the query; return count."""

    @abstractmethod
    def recall(self, query: str = "") -> list[dict]:
        """Return memory records, optionally filtered by keyword."""

    @abstractmethod
    def clear_all_memories(self) -> int:
        """Delete all memory records; return count."""


class SemanticIndex(ABC):
    """Optional vector index layered over durable memory records.

    Records are indexed by their durable memory id so writes/deletes stay in
    sync with the backing MemoryStore. May be unavailable (no chromadb).
    """

    @abstractmethod
    def available(self) -> bool:
        """Whether the underlying vector engine can be used."""

    @abstractmethod
    def add(self, doc_id: str, text: str, metadata: Optional[dict] = None) -> None:
        """Index a memory record by its durable id."""

    @abstractmethod
    def update(self, doc_id: str, text: str, metadata: Optional[dict] = None) -> None:
        """Replace the indexed text/metadata for an existing record."""

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Semantic search; returns [{"id", "text", "score", "metadata"}, ...]."""

    @abstractmethod
    def remove(self, doc_id: str) -> None:
        """Remove a single record from the index."""

    @abstractmethod
    def clear(self) -> None:
        """Remove every record from the index."""
