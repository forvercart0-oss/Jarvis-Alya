"""Optional semantic index backed by ChromaDB.

The chromadb import is lazy and every operation is defensive: if the library
is missing (or the environment can't host a persistent client) the index is
simply unavailable and MemoryManager falls back to keyword recall.

Embeddings are computed locally (no model download) and passed to chromadb
explicitly as `embeddings`/`query_embeddings`, so vector recall works fully
offline. Document text is stored in metadata and reconstructed on search.
"""

from __future__ import annotations

import logging
from typing import Optional

from memory.store import SemanticIndex

logger = logging.getLogger("jarvis")

_COLLECTION = "jarvis_memory"
_EMBED_DIM = 256


class LocalHashEmbeddingFunction:
    """Deterministic, offline-safe bag-of-words embedder.

    Avoids chromadb's default embedder (which downloads an ONNX model on first
    use). Weaker than a learned model but adequate for short memories layered
    on top of keyword recall.
    """

    @staticmethod
    def embed(texts: list[str]) -> list[list[float]]:
        import hashlib

        vectors: list[list[float]] = []
        for text in texts:
            vec = [0.0] * _EMBED_DIM
            for token in text.lower().split():
                digest = hashlib.md5(token.encode("utf-8")).digest()
                vec[int.from_bytes(digest[:4], "big") % _EMBED_DIM] += 1.0
            norm = sum(v * v for v in vec) ** 0.5
            vectors.append([v / norm if norm else 0.0 for v in vec])
        return vectors


class VectorMemory(SemanticIndex):
    def __init__(self, persist_directory: str = "data/vector_store"):
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None
        try:
            import chromadb

            from chromadb.config import Settings as ChromaSettings

            self._client = chromadb.PersistentClient(path=persist_directory, settings=ChromaSettings(anonymized_telemetry=False))
            self._collection = self._client.get_or_create_collection(
                name=_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("Vector memory unavailable (%s); falling back to keyword recall", exc)

    def available(self) -> bool:
        return self._client is not None and self._collection is not None

    def _add_embeddings(self, doc_id: str, text: str, metadata: Optional[dict]) -> None:
        embedding = LocalHashEmbeddingFunction.embed([text])[0]
        meta = dict(metadata or {})
        meta["_text"] = text
        self._collection.add(embeddings=[embedding], metadatas=[meta], ids=[doc_id])

    def _update_embeddings(self, doc_id: str, text: str, metadata: Optional[dict]) -> None:
        embedding = LocalHashEmbeddingFunction.embed([text])[0]
        meta = dict(metadata or {})
        meta["_text"] = text
        self._collection.update(embeddings=[embedding], metadatas=[meta], ids=[doc_id])

    def add(self, doc_id: str, text: str, metadata: Optional[dict] = None) -> None:
        if not self.available():
            return
        try:
            self._add_embeddings(doc_id, text, metadata)
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("Vector add failed for %s: %s", doc_id, exc)

    def update(self, doc_id: str, text: str, metadata: Optional[dict] = None) -> None:
        if not self.available():
            return
        try:
            self._update_embeddings(doc_id, text, metadata)
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("Vector update failed for %s: %s", doc_id, exc)

    def search(self, query: str, limit: int = 5) -> list[dict]:
        if not self.available():
            return []
        try:
            query_embedding = LocalHashEmbeddingFunction.embed([query])[0]
            results = self._collection.query(query_embeddings=[query_embedding], n_results=limit)
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("Vector search failed: %s", exc)
            return []
        docs = []
        if results and results.get("ids") and results["ids"][0]:
            metas = results.get("metadatas")
            meta_row = metas[0] if metas and metas[0] else None
            for i, doc_id in enumerate(results["ids"][0]):
                meta = dict(meta_row[i]) if meta_row and meta_row[i] else {}
                docs.append({
                    "id": doc_id,
                    "text": meta.pop("_text", ""),
                    "score": results["distances"][0][i] if results.get("distances") else None,
                    "metadata": meta,
                })
        return docs

    def remove(self, doc_id: str) -> None:
        if not self.available():
            return
        try:
            self._collection.delete(ids=[doc_id])
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("Vector delete failed for %s: %s", doc_id, exc)

    def clear(self) -> None:
        if not self.available():
            return
        try:
            self._client.delete_collection(_COLLECTION)
            self._collection = self._client.get_or_create_collection(
                name=_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("Vector clear failed: %s", exc)
