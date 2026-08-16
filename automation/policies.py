"""Task policies: risk levels, timeouts, retry policies, and limits."""

from __future__ import annotations

from dataclasses import dataclass

from automation.task_state import TaskComplexity


@dataclass(frozen=True)
class TaskPolicy:
    """Policy configuration for a single task."""

    timeout_seconds: float = 300.0
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    max_subprocesses: int = 4
    max_memory_mb: int = 512
    auto_execute: bool = False
    require_confirmation: bool = True
    allow_background: bool = True
    notification_on_complete: bool = True
    notification_on_failure: bool = True
    verification_required: bool = True
    max_checkpoint_age_seconds: float = 3600.0


# Default policies per complexity level
COMPLEXITY_POLICIES: dict[TaskComplexity, TaskPolicy] = {
    TaskComplexity.SIMPLE: TaskPolicy(
        timeout_seconds=60.0,
        max_retries=2,
        max_subprocesses=1,
        auto_execute=True,
        require_confirmation=False,
        verification_required=True,
    ),
    TaskComplexity.MODERATE: TaskPolicy(
        timeout_seconds=180.0,
        max_retries=3,
        max_subprocesses=2,
        auto_execute=False,
        require_confirmation=True,
        verification_required=True,
    ),
    TaskComplexity.COMPLEX: TaskPolicy(
        timeout_seconds=600.0,
        max_retries=3,
        max_subprocesses=4,
        auto_execute=False,
        require_confirmation=True,
        verification_required=True,
    ),
}

# Risk levels for automation actions
RISK_LEVELS = {
    "minimal": {"score": 0, "requires_confirmation": False, "requires_approval": False},
    "low": {"score": 1, "requires_confirmation": False, "requires_approval": False},
    "medium": {"score": 2, "requires_confirmation": True, "requires_approval": False},
    "high": {"score": 3, "requires_confirmation": True, "requires_approval": True},
    "critical": {
        "score": 4,
        "requires_confirmation": True,
        "requires_approval": True,
        "immutable": True,
    },
}

# Default tool risk mapping
TOOL_RISK_MAP: dict[str, str] = {
    "read_file": "minimal",
    "system_info": "minimal",
    "cpu_usage": "minimal",
    "memory_usage": "minimal",
    "disk_usage": "minimal",
    "battery_status": "minimal",
    "get_time": "minimal",
    "get_date": "minimal",
    "calculator": "minimal",
    "web_search": "low",
    "open_browser": "low",
    "open_application": "low",
    "close_application": "low",
    "write_file": "medium",
    "terminal": "medium",
    "run_project_command": "medium",
    "screenshot": "medium",
    "vision_capture_screen": "medium",
    "vision_analyze_screen": "medium",
    "vision_find_target": "medium",
    "vision_ocr": "medium",
    "computer_control": "medium",
    "computer_mouse_click": "medium",
    "computer_keyboard_type": "medium",
    "browser_click": "medium",
    "browser_type": "medium",
    "browser_navigate": "medium",
    "delete_file": "high",
    "shutdown": "critical",
    "reboot": "critical",
    "suspend": "critical",
    "lock_screen": "medium",
    "volume_control": "low",
    "remember": "minimal",
    "forget": "low",
    "recall_memories": "minimal",
    "create_project": "medium",
    "delete_project": "high",
    "write_project_file": "medium",
    "send_message": "high",
    "execute_automation": "low",
}


def get_policy_for_complexity(complexity: TaskComplexity | str) -> TaskPolicy:
    """Return the default policy for a given task complexity."""
    if isinstance(complexity, str):
        complexity = TaskComplexity(complexity)
    return COMPLEXITY_POLICIES.get(complexity, COMPLEXITY_POLICIES[TaskComplexity.MODERATE])


def get_tool_risk(tool_name: str) -> str:
    """Return the risk level for a given tool name."""
    return TOOL_RISK_MAP.get(tool_name, "medium")


def classify_task_complexity(description: str, steps: int = 0) -> TaskComplexity:
    """Classify a task as SIMPLE, MODERATE, or COMPLEX based on description and steps."""
    lower = description.lower()
    step_count = max(
        steps,
        lower.count(" and ") + lower.count(" then ") + lower.count(",") + 1,
    )

    complex_keywords = {
        "build",
        "create",
        "deploy",
        "install",
        "setup",
        "test",
        "ecommerce",
        "project",
        "application",
        "app",
        "fullstack",
    }
    moderate_keywords = {
        "open",
        "check",
        "search",
        "find",
        "read",
        "list",
        "show",
        "get",
        "verify",
    }

    if any(k in lower for k in complex_keywords) or step_count > 5:
        return TaskComplexity.COMPLEX
    if any(k in lower for k in moderate_keywords) and step_count > 1:
        return TaskComplexity.MODERATE
    return TaskComplexity.SIMPLE
