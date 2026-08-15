"""Memory subsystem for JARVIS 2.0 (SQLite + optional vector memory)."""

from __future__ import annotations

from pathlib import Path

from memory.manager import MemoryManager

_memory: MemoryManager | None = None


def get_memory(db_path: Path | None = None) -> MemoryManager:
    """Return the process-wide MemoryManager singleton."""
    global _memory
    if _memory is None:
        _memory = MemoryManager(db_path)
    return _memory


def reset_memory_singleton() -> None:
    """Reset the singleton (used in tests)."""
    global _memory
    _memory = None
