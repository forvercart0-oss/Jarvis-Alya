"""Memory types, importance levels, and metadata for JARVIS Phase 16."""

from __future__ import annotations

from enum import Enum


class MemoryType(str, Enum):
    USER_PREFERENCE = "user_preference"
    USER_PROFILE = "user_profile"
    PROJECT = "project"
    PROJECT_PREFERENCE = "project_preference"
    WORKFLOW = "workflow"
    SKILL = "skill"
    TASK = "task"
    CONVERSATION = "conversation"
    FACT = "fact"
    DECISION = "decision"
    GOAL = "goal"
    IMPORTANT_CONTEXT = "important_context"
    SESSION = "session"
    PROFILE = "profile"
    GENERAL = "general"
    PREFERENCE = "preference"
    CODING = "coding"
    TECHNICAL = "technical"
    UI = "ui"
    VOICE = "voice"
    ASSISTANT = "assistant"
    KNOWLEDGE = "knowledge"
    TASK_HISTORY = "task_history"
    ERROR = "error"
    IDEA = "idea"
    DOCUMENT = "document"
    RESEARCH = "research"


class MemoryImportance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MemorySource(str, Enum):
    EXPLICIT_USER = "explicit_user"
    CONVERSATION = "conversation"
    TASK = "task"
    AGENT = "agent"
    IMPORT = "import"
    SYSTEM = "system"


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    CONFLICTED = "conflicted"
    EXPIRED = "expired"


class PrivacyLevel(str, Enum):
    NORMAL = "normal"
    PRIVATE = "private"
    SENSITIVE = "sensitive"


class TrustLevel(str, Enum):
    TRUSTED = "trusted"
    NORMAL = "normal"
    UNTRUSTED = "untrusted"


class IdeaStatus(str, Enum):
    IDEA = "idea"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ErrorCategory(str, Enum):
    NETWORK = "network"
    BUILD = "build"
    DEPLOYMENT = "deployment"
    DATABASE = "database"
    PERMISSION = "permission"
    CONFIGURATION = "configuration"
    RUNTIME = "runtime"
    OTHER = "other"


MEMORY_TYPE_LABELS = {
    MemoryType.USER_PREFERENCE: "User Preference",
    MemoryType.USER_PROFILE: "User Profile",
    MemoryType.PROJECT: "Project",
    MemoryType.PROJECT_PREFERENCE: "Project Preference",
    MemoryType.WORKFLOW: "Workflow",
    MemoryType.SKILL: "Skill",
    MemoryType.TASK: "Task",
    MemoryType.CONVERSATION: "Conversation",
    MemoryType.FACT: "Fact",
    MemoryType.DECISION: "Decision",
    MemoryType.GOAL: "Goal",
    MemoryType.IMPORTANT_CONTEXT: "Important Context",
    MemoryType.SESSION: "Session",
    MemoryType.PROFILE: "Profile",
    MemoryType.GENERAL: "General",
    MemoryType.PREFERENCE: "Preference",
    MemoryType.CODING: "Coding",
    MemoryType.TECHNICAL: "Technical",
    MemoryType.UI: "UI",
    MemoryType.VOICE: "Voice",
    MemoryType.ASSISTANT: "Assistant",
    MemoryType.KNOWLEDGE: "Knowledge",
    MemoryType.TASK_HISTORY: "Task History",
    MemoryType.ERROR: "Error",
    MemoryType.IDEA: "Idea",
    MemoryType.DOCUMENT: "Document",
    MemoryType.RESEARCH: "Research",
}


def normalize_memory_type(value: str | None) -> str:
    if not value:
        return MemoryType.GENERAL.value
    normalized = value.strip().lower()
    for member in MemoryType:
        if member.value == normalized:
            return member.value
    return MemoryType.GENERAL.value
