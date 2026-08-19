"""Tests for Phase 12 advanced memory features."""

from __future__ import annotations


from memory.extractor import MemoryExtractor


def test_memory_ranker_scores_by_relevance(tmp_db):
    tmp_db.remember("User prefers dark theme", category="preferences", confidence=1.0, importance=0.9)
    tmp_db.remember("User likes pizza", category="preferences", confidence=0.5, importance=0.3)
    results = tmp_db.search_with_ranking("dark theme", category="preferences", limit=2)
    assert len(results) > 0
    assert results[0]["_score"] >= results[-1]["_score"]


def test_memory_decay_reduces_factor(tmp_db):
    mem = tmp_db.remember("Test decay", category="general", confidence=1.0, importance=0.5)
    updated = tmp_db.apply_decay(decay_rate=0.5)
    assert updated >= 0
    row = tmp_db.get_memory_by_id(mem["id"])
    assert row["decay_factor"] <= 1.0


def test_duplicate_detection(tmp_db):
    tmp_db.remember("User likes dark mode", category="preferences")
    tmp_db.remember("User likes dark mode", category="preferences")
    dups = tmp_db.detect_duplicates(threshold=0.8)
    assert len(dups) >= 1


def test_contradiction_detection(tmp_db):
    tmp_db.remember("groq", category="preferences", key_override="ai_provider")
    tmp_db.remember("local llm", category="preferences", key_override="ai_provider")
    contradictions = tmp_db.detect_contradictions()
    assert len(contradictions) >= 1


def test_context_builder_budget(tmp_db):
    for i in range(20):
        tmp_db.remember(f"Context item {i}" * 10, category="general", importance=0.5)
    ctx = tmp_db.build_context("context", max_memories=5, max_tokens=100)
    assert len(ctx["memories"]) <= 5
    assert ctx["token_budget_used"] <= 100


def test_knowledge_graph_link(tmp_db):
    mem1 = tmp_db.remember("Node A", category="general")
    mem2 = tmp_db.remember("Node B", category="general")
    result = tmp_db.knowledge_graph.link(mem1["id"], mem2["id"], "depends_on")
    assert result is True
    related = tmp_db.get_related_memories(mem1["id"], limit=5)
    assert any(r["id"] == mem2["id"] for r in related)


def test_backup_export_import(tmp_db):
    tmp_db.remember("Backup test", category="general", importance=0.8)
    exported = tmp_db.export_memories()
    assert "memories" in exported
    assert exported["count"] >= 1
    tmp_db.forget("Backup test")
    imported = tmp_db.import_memories(exported, mode="merge")
    assert imported["imported"] >= 1


def test_health_check(tmp_db):
    health = tmp_db.get_health()
    assert "total_memories" in health
    assert "duplicates" in health
    assert "contradictions" in health


def test_memory_extractor_remember_action(tmp_db):
    extractor = MemoryExtractor(tmp_db)
    action = extractor.should_remember("Remember that I use Groq", "Noted.")
    assert action == "remember"


def test_memory_extractor_ignore_action(tmp_db):
    extractor = MemoryExtractor(tmp_db)
    action = extractor.should_remember("What is 2+2?", "4")
    assert action == "ignore"


def test_memory_extractor_forget_action(tmp_db):
    extractor = MemoryExtractor(tmp_db)
    action = extractor.should_remember("Forget that I use Groq", "Done.")
    assert action == "forget"


def test_memory_ranker_prefers_high_confidence(tmp_db):
    tmp_db.remember("Important fact", category="fact", confidence=1.0, importance=1.0)
    tmp_db.remember("Trivial fact", category="fact", confidence=0.1, importance=0.1)
    results = tmp_db.search_with_ranking("fact", category="fact", limit=2)
    assert results[0]["value"] == "Important fact"


def test_memory_import_overwrite_mode(tmp_db):
    tmp_db.remember("Original", category="general")
    data = tmp_db.export_memories(category="general")
    data["memories"][0]["value"] = "Overwritten"
    result = tmp_db.import_memories(data, mode="overwrite")
    assert result["imported"] >= 1
    rows = tmp_db.recall("Overwritten", category="general")
    assert len(rows) >= 1


def test_memory_access_count_increments(tmp_db):
    mem = tmp_db.remember("Access test", category="general")
    tmp_db.increment_access(mem["id"])
    row = tmp_db.get_memory_by_id(mem["id"])
    assert row["access_count"] >= 1


def test_memory_update_fields(tmp_db):
    mem = tmp_db.remember("Update test", category="general", importance=0.5)
    updated = tmp_db.update_memory_fields(mem["id"], {"importance": 0.9, "tags": ["tag1"]})
    assert updated["importance"] == 0.9
    assert updated["tags"] == ["tag1"]
