"""Memory subsystem for JARVIS 2.0 Phase 21."""

from __future__ import annotations

from memory.adaptive import AdaptiveMemory, AdaptivePreference, ConfidenceLevel, PreferenceSource
from memory.audit import MemoryAuditLog
from memory.backup import MemoryBackup
from memory.cleanup import MemoryCleanup
from memory.context_builder import ContextBuilder
from memory.contradictions import ContradictionDetector
from memory.decay import MemoryDecay
from memory.duplicates import DuplicateDetector
from memory.environment import EnvironmentProfiler, environment_profiler
from memory.extractor import MemoryExtractor
from memory.health import MemoryHealth
from memory.knowledge_graph import KnowledgeGraph
from memory.long_term import LongTermMemory
from memory.manager import MemoryManager, SecretMemoryError, normalize_category
from memory.preferences import PreferencesMemory
from memory.privacy import PrivacyController
from memory.projects import ProjectMemory
from memory.ranker import MemoryRanker
from memory.reminders import ReminderManager
from memory.semantic import SemanticMemory
from memory.short_term import ShortTermMemory
from memory.sqlite_memory import SQLiteMemory
from memory.store import MemoryStore
from memory.summaries import ConversationSummaries
from memory.tasks import TaskMemory
from memory.types import MemoryImportance, MemorySource, MemoryStatus, MemoryType, normalize_memory_type
from memory.vector_memory import VectorMemory
from memory.workflows import WorkflowDetector, SuggestionEngine, workflow_detector, suggestion_engine

__all__ = [
    "AdaptiveMemory",
    "AdaptivePreference",
    "ConfidenceLevel",
    "PreferenceSource",
    "ContextBuilder",
    "ContradictionDetector",
    "ConversationSummaries",
    "DuplicateDetector",
    "EnvironmentProfiler",
    "environment_profiler",
    "KnowledgeGraph",
    "LongTermMemory",
    "MemoryAuditLog",
    "MemoryBackup",
    "MemoryCleanup",
    "MemoryDecay",
    "MemoryExtractor",
    "MemoryHealth",
    "MemoryImportance",
    "MemoryManager",
    "MemoryRanker",
    "MemorySource",
    "MemoryStatus",
    "MemoryStore",
    "MemoryType",
    "PreferencesMemory",
    "PrivacyController",
    "ProjectMemory",
    "ReminderManager",
    "SecretMemoryError",
    "SemanticMemory",
    "ShortTermMemory",
    "SQLiteMemory",
    "TaskMemory",
    "VectorMemory",
    "WorkflowDetector",
    "SuggestionEngine",
    "workflow_detector",
    "suggestion_engine",
    "normalize_category",
    "normalize_memory_type",
]
