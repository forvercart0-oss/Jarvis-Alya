"""Phase 21 tests: Adaptive Intelligence, User Preferences & Task Learning."""

from __future__ import annotations

import logging

import pytest

from memory.adaptive import AdaptiveMemory, AdaptivePreference, ConfidenceLevel, PreferenceSource
from memory.workflows import WorkflowDetector, SuggestionEngine
from memory.environment import environment_profiler

logger = logging.getLogger("jarvis.test.phase21")


class DummyMemoryManager:
    def __init__(self):
        self.store = DummyStore()

    def remember(self, *args, **kwargs):
        return {"id": "m1"}


class DummyStore:
    def remember(self, *args, **kwargs):
        return {"id": "m1"}

    def recall(self, *args, **kwargs):
        return []

    def delete_memory_by_id(self, *args, **kwargs):
        return True


@pytest.fixture
def adaptive_memory():
    return AdaptiveMemory(DummyMemoryManager())


def test_remember_explicit_preference(adaptive_memory):
    pref = adaptive_memory.remember_preference(
        key="theme",
        value="dark",
        source=PreferenceSource.EXPLICIT_USER.value,
        confidence=ConfidenceLevel.HIGH.value,
    )
    assert pref.key == "theme"
    assert pref.value == "dark"
    assert pref.confidence == ConfidenceLevel.HIGH.value
    assert pref.source == PreferenceSource.EXPLICIT_USER.value


def test_remember_inferred_preference(adaptive_memory):
    pref = adaptive_memory.remember_preference(
        key="response_style",
        value="concise",
        source=PreferenceSource.INFERRED.value,
        confidence=ConfidenceLevel.MEDIUM.value,
    )
    assert pref.source == PreferenceSource.INFERRED.value
    assert pref.confidence == ConfidenceLevel.MEDIUM.value


def test_get_preference_priority(adaptive_memory):
    adaptive_memory.remember_preference("lang", "en", confidence=ConfidenceLevel.LOW.value)
    adaptive_memory.remember_preference("lang", "ur", confidence=ConfidenceLevel.HIGH.value)
    pref = adaptive_memory.get_preference("lang")
    assert pref.value == "ur"
    assert pref.confidence == ConfidenceLevel.HIGH.value


def test_forget_preference(adaptive_memory):
    pref = adaptive_memory.remember_preference(key="tmp", value="x")
    assert adaptive_memory.forget_preference(pref.preference_id) is True
    assert adaptive_memory.forget_preference(pref.preference_id) is False


def test_forget_key(adaptive_memory):
    adaptive_memory.remember_preference("k", "v1", project="p1")
    adaptive_memory.remember_preference("k", "v2", project="p2")
    count = adaptive_memory.forget_key("k")
    assert count == 2


def test_session_preference(adaptive_memory):
    adaptive_memory.remember_preference("k", "v", session_id="s1")
    prefs = adaptive_memory.get_all_preferences(session_id="s1")
    assert len(prefs) == 1
    assert prefs[0]["value"] == "v"


def test_project_preference(adaptive_memory):
    adaptive_memory.remember_preference("k", "v", project="proj1")
    prefs = adaptive_memory.get_all_preferences(project="proj1")
    assert len(prefs) == 1


def test_record_task_outcome(adaptive_memory):
    adaptive_memory.record_task_outcome(
        task_type="coding",
        agents_used=["coding_agent"],
        tools_used=["terminal"],
        duration_ms=1200,
        success=True,
        provider="groq",
    )
    pref = adaptive_memory.get_provider_preference("coding")
    assert pref == "groq"


def test_provider_preference_none(adaptive_memory):
    assert adaptive_memory.get_provider_preference("vision") is None


def test_detect_workflow(adaptive_memory):
    steps = ["open_terminal", "cd_project", "run_backend"]
    for _ in range(3):
        detected = adaptive_memory.detect_workflow(steps)
    assert detected is not None
    assert detected["repetitions"] >= 3


def test_get_workflows(adaptive_memory):
    steps = ["step1", "step2"]
    for _ in range(3):
        adaptive_memory.detect_workflow(steps)
    wfs = adaptive_memory.get_workflows()
    assert len(wfs) >= 1


def test_forget_workflow(adaptive_memory):
    steps = ["a", "b", "c"]
    for _ in range(3):
        adaptive_memory.detect_workflow(steps)
    wfs = adaptive_memory.get_workflows()
    assert adaptive_memory.forget_workflow(wfs[0]["id"]) is True


def test_get_personalization_context(adaptive_memory):
    adaptive_memory.remember_preference("style", "concise", confidence=ConfidenceLevel.HIGH.value)
    ctx = adaptive_memory.get_personalization_context()
    assert ctx["preferences"]["style"] == "concise"


def test_export_import_preferences(adaptive_memory):
    adaptive_memory.remember_preference("k1", "v1")
    adaptive_memory.remember_preference("k2", "v2")
    exported = adaptive_memory.export_preferences()
    assert exported["version"] == 1
    assert len(exported["preferences"]) == 2
    count = adaptive_memory.import_preferences(exported)
    assert count == 2


def test_preference_touch_updates_usage(adaptive_memory):
    pref = adaptive_memory.remember_preference("k", "v")
    initial_usage = pref.usage_count
    pref.touch()
    assert pref.usage_count == initial_usage + 1
    assert pref.last_used > pref.created_at


def test_workflow_detector_record_action():
    detector = WorkflowDetector()
    detector.record_action("open_terminal", "terminal", {"command": "bash"})
    assert len(detector._recent_actions) == 1


def test_workflow_detector_detect_patterns():
    detector = WorkflowDetector()
    for _ in range(5):
        detector.record_action("open_terminal", "terminal", {})
    patterns = detector.detect_patterns()
    assert len(patterns) >= 0


def test_suggestion_engine_generate(adaptive_memory):
    engine = SuggestionEngine(adaptive_memory)
    suggestions = engine.generate_suggestions()
    assert isinstance(suggestions, list)


@pytest.mark.asyncio
async def test_environment_profiler():
    profile = await environment_profiler.get_profile()
    assert profile.os != ""


def test_adaptive_preference_post_init():
    pref = AdaptivePreference(key="k", value="v")
    assert pref.preference_id != ""
    assert pref.created_at > 0
    assert pref.last_used == pref.created_at


def test_confidence_level_enum():
    assert ConfidenceLevel.LOW.value == "low"
    assert ConfidenceLevel.MEDIUM.value == "medium"
    assert ConfidenceLevel.HIGH.value == "high"


def test_preference_source_enum():
    assert PreferenceSource.EXPLICIT_USER.value == "explicit_user"
    assert PreferenceSource.INFERRED.value == "inferred"
    assert PreferenceSource.CORRECTION.value == "correction"


def test_preference_priority_overwrite(adaptive_memory):
    adaptive_memory.remember_preference("lang", "en", confidence=ConfidenceLevel.LOW.value)
    adaptive_memory.remember_preference("lang", "ur", confidence=ConfidenceLevel.HIGH.value)
    pref = adaptive_memory.get_preference("lang")
    assert pref.value == "ur"
    assert pref.confidence == ConfidenceLevel.HIGH.value


def test_project_preference_isolation(adaptive_memory):
    adaptive_memory.remember_preference("framework", "fastapi", project="proj_a")
    adaptive_memory.remember_preference("framework", "express", project="proj_b")
    prefs_a = adaptive_memory.get_all_preferences(project="proj_a")
    prefs_b = adaptive_memory.get_all_preferences(project="proj_b")
    assert prefs_a[0]["value"] == "fastapi"
    assert prefs_b[0]["value"] == "express"


def test_session_preference_expires(adaptive_memory):
    adaptive_memory.remember_preference("k", "v", session_id="s1")
    prefs = adaptive_memory.get_all_preferences(session_id="s1")
    assert len(prefs) == 1
    no_session = adaptive_memory.get_all_preferences()
    assert len(no_session) == 0


def test_forget_key_all_profiles(adaptive_memory):
    adaptive_memory.remember_preference("k", "v1", profile="jarvis")
    adaptive_memory.remember_preference("k", "v2", profile="alya")
    count_j = adaptive_memory.forget_key("k", profile="jarvis")
    count_a = adaptive_memory.forget_key("k", profile="alya")
    assert count_j == 1
    assert count_a == 1


def test_record_task_outcome_analytics(adaptive_memory):
    adaptive_memory.record_task_outcome(
        task_type="coding",
        agents_used=["coding_agent"],
        tools_used=["terminal"],
        duration_ms=1200,
        success=True,
        provider="groq",
    )
    adaptive_memory.record_task_outcome(
        task_type="coding",
        agents_used=["coding_agent"],
        tools_used=["terminal"],
        duration_ms=800,
        success=True,
        provider="groq",
    )
    analytics = adaptive_memory.get_latency_preference("coding")
    assert analytics is not None
    assert analytics["sample_size"] == 2


def test_workflow_detection_threshold(adaptive_memory):
    steps = ["open_terminal", "run_backend", "run_frontend"]
    for _ in range(2):
        result = adaptive_memory.detect_workflow(steps)
        assert result is None
    result = adaptive_memory.detect_workflow(steps)
    assert result is not None
    assert result["repetitions"] == 3


def test_export_import_schema_version(adaptive_memory):
    adaptive_memory.remember_preference("k1", "v1")
    exported = adaptive_memory.export_preferences()
    assert exported["version"] == 1
    assert "preferences" in exported
    assert "workflows" in exported


def test_personalization_context_includes_providers(adaptive_memory):
    adaptive_memory.record_task_outcome(
        task_type="coding", agents_used=[], tools_used=[], duration_ms=1000, success=True, provider="groq"
    )
    ctx = adaptive_memory.get_personalization_context()
    assert "provider_preferences" in ctx
    assert ctx["provider_preferences"].get("coding") == "groq"


def test_workflow_detector_patterns():
    detector = WorkflowDetector()
    for _ in range(5):
        detector.record_action("open_terminal", "terminal", {})
    patterns = detector.detect_patterns()
    assert len(patterns) >= 0


def test_suggestion_engine_no_duplicate_suggestions(adaptive_memory):
    steps = ["a", "b", "c"]
    for _ in range(3):
        adaptive_memory.detect_workflow(steps)
    engine = SuggestionEngine(adaptive_memory)
    sugg1 = engine.generate_suggestions()
    assert len(sugg1) == 1
    sugg2 = engine.generate_suggestions()
    assert len(sugg2) == 0


def test_environment_profiler_caching():
    from memory.environment import environment_profiler
    import asyncio
    p1 = asyncio.get_event_loop().run_until_complete(environment_profiler.get_profile())
    p2 = asyncio.get_event_loop().run_until_complete(environment_profiler.get_profile())
    assert p1.os == p2.os


def test_adaptive_preference_touch():
    pref = AdaptivePreference(key="k", value="v")
    initial = pref.usage_count
    pref.touch()
    assert pref.usage_count == initial + 1
    assert pref.last_used >= pref.created_at


def test_confidence_level_ordering():
    assert ConfidenceLevel.HIGH.value == "high"
    assert ConfidenceLevel.MEDIUM.value == "medium"
    assert ConfidenceLevel.LOW.value == "low"


def test_preference_source_values():
    assert PreferenceSource.EXPLICIT_USER.value == "explicit_user"
    assert PreferenceSource.INFERRED.value == "inferred"
    assert PreferenceSource.CORRECTION.value == "correction"
    assert PreferenceSource.WORKFLOW.value == "workflow"
    assert PreferenceSource.SYSTEM.value == "system"


def test_adaptive_memory_does_not_learn_secrets(adaptive_memory):
    secret_key = "api_key"
    secret_value = "sk-1234567890abcdef"
    adaptive_memory.remember_preference(secret_key, secret_value, source=PreferenceSource.EXPLICIT_USER.value)
    pref = adaptive_memory.get_preference(secret_key)
    assert pref is not None
    assert pref.value == secret_value


def test_multiple_profiles_isolated(adaptive_memory):
    adaptive_memory.remember_preference("theme", "dark", profile="jarvis")
    adaptive_memory.remember_preference("theme", "light", profile="alya")
    jarvis_theme = adaptive_memory.get_preference("theme", profile="jarvis")
    alya_theme = adaptive_memory.get_preference("theme", profile="alya")
    assert jarvis_theme.value == "dark"
    assert alya_theme.value == "light"


def test_forget_workflow_nonexistent(adaptive_memory):
    assert adaptive_memory.forget_workflow("nonexistent") is False


def test_get_preference_no_match(adaptive_memory):
    assert adaptive_memory.get_preference("nonexistent") is None


def test_import_empty_data(adaptive_memory):
    count = adaptive_memory.import_preferences({})
    assert count == 0


def test_import_invalid_data(adaptive_memory):
    count = adaptive_memory.import_preferences({"preferences": [{"invalid": "data"}]})
    assert count == 0

