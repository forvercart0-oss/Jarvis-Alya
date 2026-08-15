"""Semantic memory boundary: vector index merge, dedupe and sync."""

import pytest

from memory.manager import MemoryManager
from memory.store import SemanticIndex
from memory.vector_memory import VectorMemory


class FakeSemanticIndex(SemanticIndex):
    """Deterministic in-memory index: token overlap scored by recency."""

    def __init__(self):
        self._docs: dict[str, dict] = {}
        self._order: list[str] = []

    def available(self) -> bool:
        return True

    def add(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        self._docs[doc_id] = {"text": text, "metadata": metadata or {}}
        self._order.append(doc_id)

    def update(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        self._docs[doc_id] = {"text": text, "metadata": metadata or {}}

    def search(self, query: str, limit: int = 5) -> list[dict]:
        tokens = {t.lower() for t in query.split()}
        scored = []
        for doc_id in self._order:
            text = self._docs[doc_id]["text"].lower()
            overlap = len(tokens & set(text.split()))
            if overlap > 0:
                scored.append((overlap, doc_id))
        scored.sort(key=lambda x: (-x[0], -self._order.index(x[1])))
        out = []
        for _, doc_id in scored[:limit]:
            out.append({
                "id": doc_id,
                "text": self._docs[doc_id]["text"],
                "score": 0.5,
                "metadata": self._docs[doc_id]["metadata"],
            })
        return out

    def remove(self, doc_id: str) -> None:
        self._docs.pop(doc_id, None)
        if doc_id in self._order:
            self._order.remove(doc_id)

    def clear(self) -> None:
        self._docs.clear()
        self._order.clear()


def _manager_with_vector(tmp_path) -> MemoryManager:
    manager = MemoryManager(str(tmp_path / "jarvis.db"))
    manager._vector = FakeSemanticIndex()  # noqa: SLF001
    return manager


def test_vector_disabled_by_default(tmp_db):
    assert tmp_db.vector_enabled is False
    tmp_db.remember("alpha", "the quick brown fox")
    rows = tmp_db.recall("fox")
    assert len(rows) == 1
    assert "semantic_score" not in rows[0]


def test_remember_indexes_vector(tmp_path):
    manager = _manager_with_vector(tmp_path)
    assert manager.vector_enabled is True
    mem = manager.remember("alpha", "the quick brown fox")
    assert manager._vector._docs[mem["id"]]["text"] == "the quick brown fox"  # noqa: SLF001


def test_recall_merges_and_dedupes(tmp_path):
    manager = _manager_with_vector(tmp_path)
    mem_a = manager.remember("a", "the quick brown fox")
    manager.remember("b", "unrelated rainy day")
    rows = manager.recall("fox")
    ids = {row["id"] for row in rows}
    assert ids == {mem_a["id"]}
    assert rows[0]["semantic_score"] == 0.5


def test_recall_appends_semantic_only_hits(tmp_path):
    manager = _manager_with_vector(tmp_path)
    manager.remember("a", "the quick brown fox")
    mem_b = manager.remember("b", "the fox is on the roof")
    rows = manager.recall("fox")
    ids = {row["id"] for row in rows}
    assert mem_b["id"] in ids
    assert any("semantic_score" in row for row in rows)


def test_forget_syncs_vector(tmp_path):
    manager = _manager_with_vector(tmp_path)
    mem = manager.remember("a", "the quick brown fox")
    manager.remember("b", "unrelated rainy day")
    assert manager.forget("fox") == 1
    assert mem["id"] not in manager._vector._docs  # noqa: SLF001


def test_clear_all_memories_clears_vector(tmp_path):
    manager = _manager_with_vector(tmp_path)
    manager.remember("a", "the quick brown fox")
    manager.remember("b", "unrelated rainy day")
    manager.clear_all_memories()
    assert manager._vector._docs == {}  # noqa: SLF001
    assert manager.recall("") == []


def test_update_memory_reindexes(tmp_path):
    manager = _manager_with_vector(tmp_path)
    mem = manager.remember("a", "the quick brown fox")
    manager.update_memory(mem["id"], "totally different content now")
    assert manager._vector._docs[mem["id"]]["text"] == "totally different content now"  # noqa: SLF001


def test_chroma_smoke(tmp_path):
    index = VectorMemory(persist_directory=str(tmp_path / "vector_store"))
    if not index.available():
        pytest.skip("chromadb not available in this environment")
    index.add("doc-1", "jarvis system diagnostic ok")
    index.add("doc-2", "the weather is sunny today")
    hits = index.search("diagnostic", limit=5)
    assert any(h["id"] == "doc-1" for h in hits)
    assert all("id" in h and "text" in h for h in hits)
    index.update("doc-2", "completely unrelated content")
    index.remove("doc-1")
    index.clear()
