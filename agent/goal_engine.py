"""Goal Engine for JARVIS Phase 23.

Represents every complex request as a structured goal with objectives,
constraints, resources, tasks, dependencies, success criteria, and
final output.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger("jarvis.agent.goal")

class GoalStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class GoalTask:
    """A single task within a goal."""
    task_id: str
    title: str
    description: str
    agent: str = "general"
    tools: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.NORMAL
    estimated_duration_ms: int = 0
    success_criteria: list[str] = field(default_factory=list)
    fallback_agent: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    status: GoalStatus = GoalStatus.PENDING
    result: Any = None
    error: str | None = None
    started_at: float = 0.0
    finished_at: float = 0.0
    retries: int = 0
    max_retries: int = 3
    verification: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "agent": self.agent,
            "tools": self.tools,
            "dependencies": self.dependencies,
            "priority": self.priority.value,
            "estimated_duration_ms": self.estimated_duration_ms,
            "success_criteria": self.success_criteria,
            "fallback_agent": self.fallback_agent,
            "metadata": self.metadata,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "verification": self.verification,
        }


@dataclass
class Goal:
    """Represents a high-level user goal with decomposed tasks."""
    goal_id: str
    user_request: str
    objective: str = ""
    constraints: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    tasks: list[GoalTask] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    final_output: str = ""
    status: GoalStatus = GoalStatus.PENDING
    current_task_index: int = 0
    created_at: float = field(default_factory=datetime.utcnow().timestamp)
    completed_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.goal_id:
            self.goal_id = str(uuid.uuid4())[:8]

    def get_ready_tasks(self) -> list[GoalTask]:
        completed = {t.task_id for t in self.tasks if t.status in (GoalStatus.COMPLETED, GoalStatus.CANCELLED)}
        return [t for t in self.tasks if t.status == GoalStatus.PENDING and all(d in completed for d in t.dependencies)]

    def get_running_tasks(self) -> list[GoalTask]:
        return [t for t in self.tasks if t.status == GoalStatus.RUNNING]

    def get_failed_tasks(self) -> list[GoalTask]:
        return [t for t in self.tasks if t.status == GoalStatus.FAILED]

    def is_complete(self) -> bool:
        return all(t.status in (GoalStatus.COMPLETED, GoalStatus.CANCELLED) for t in self.tasks)

    def progress(self) -> float:
        if not self.tasks:
            return 0.0
        done = sum(1 for t in self.tasks if t.status == GoalStatus.COMPLETED)
        return done / len(self.tasks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "user_request": self.user_request,
            "objective": self.objective,
            "constraints": self.constraints,
            "resources": self.resources,
            "tasks": [t.to_dict() for t in self.tasks],
            "success_criteria": self.success_criteria,
            "final_output": self.final_output,
            "status": self.status.value,
            "current_task_index": self.current_task_index,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "progress": self.progress(),
            "metadata": self.metadata,
        }


class GoalEngine:
    """Decomposes high-level user goals into executable task graphs."""

    def __init__(self, ai_service: Any | None = None):
        self._ai_service = ai_service

    def analyze(self, user_request: str) -> Goal:
        """Analyze a user request and create a structured goal."""
        goal_id = str(uuid.uuid4())[:8]
        lower = user_request.lower()
        objective = user_request.strip()
        constraints: list[str] = []
        resources: list[str] = []

        if "do not" in lower or "don't" in lower or "avoid" in lower:
            constraints.append("user_restrictions")
        if "fast" in lower or "quick" in lower:
            constraints.append("speed_priority")
        if "test" in lower:
            resources.append("test_runner")
        if "database" in lower or "db" in lower:
            resources.append("database")

        tasks = self._decompose(goal_id, user_request, objective, constraints, resources)
        success_criteria = self._derive_success_criteria(user_request, tasks)

        return Goal(
            goal_id=goal_id,
            user_request=user_request,
            objective=objective,
            constraints=constraints,
            resources=resources,
            tasks=tasks,
            success_criteria=success_criteria,
        )

    def _decompose(self, goal_id: str, request: str, objective: str, constraints: list[str], resources: list[str]) -> list[GoalTask]:
        """Decompose a goal into tasks. This is a heuristic decomposition."""
        lower = request.lower()
        tasks: list[GoalTask] = []

        if any(k in lower for k in ["build", "create", "make", "develop"]):
            if "website" in lower or "web" in lower or "store" in lower or "ecommerce" in lower:
                tasks.extend([
                    GoalTask(task_id=f"{goal_id}_t1", title="Analyze requirements", description="Analyze project requirements and architecture", agent="planning", priority=TaskPriority.HIGH, success_criteria=["requirements documented"]),
                    GoalTask(task_id=f"{goal_id}_t2", title="Design architecture", description="Design system architecture", agent="planning", priority=TaskPriority.HIGH, dependencies=[f"{goal_id}_t1"], success_criteria=["architecture documented"]),
                    GoalTask(task_id=f"{goal_id}_t3", title="Create frontend", description="Create frontend application", agent="coding", priority=TaskPriority.HIGH, dependencies=[f"{goal_id}_t2"], tools=["write_file", "terminal"], success_criteria=["frontend files created"]),
                    GoalTask(task_id=f"{goal_id}_t4", title="Create backend", description="Create backend application", agent="coding", priority=TaskPriority.HIGH, dependencies=[f"{goal_id}_t2"], tools=["write_file", "terminal"], success_criteria=["backend files created"]),
                    GoalTask(task_id=f"{goal_id}_t5", title="Create database schema", description="Create database schema", agent="coding", priority=TaskPriority.NORMAL, dependencies=[f"{goal_id}_t4"], tools=["write_file"], success_criteria=["schema defined"]),
                    GoalTask(task_id=f"{goal_id}_t6", title="Run tests", description="Run tests", agent="coding", priority=TaskPriority.NORMAL, dependencies=[f"{goal_id}_t3", f"{goal_id}_t4"], tools=["terminal"], success_criteria=["tests pass"]),
                    GoalTask(task_id=f"{goal_id}_t7", title="Verify application", description="Verify application runs", agent="verification", priority=TaskPriority.HIGH, dependencies=[f"{goal_id}_t6"], success_criteria=["application starts", "pages load"]),
                ])
                return tasks

        if any(k in lower for k in ["research", "search", "find", "analyze"]):
            topic = request.replace("research", "").replace("search", "").replace("find", "").replace("analyze", "").strip() or "the topic"
            tasks.extend([
                GoalTask(task_id=f"{goal_id}_t1", title="Plan research", description=f"Plan research on {topic}", agent="planning", priority=TaskPriority.HIGH, success_criteria=["research plan created"]),
                GoalTask(task_id=f"{goal_id}_t2", title="Execute research", description=f"Research {topic}", agent="research", priority=TaskPriority.HIGH, dependencies=[f"{goal_id}_t1"], tools=["web_search", "browser"], success_criteria=["sources collected"]),
                GoalTask(task_id=f"{goal_id}_t3", title="Synthesize findings", description="Synthesize research findings", agent="research", priority=TaskPriority.NORMAL, dependencies=[f"{goal_id}_t2"], success_criteria=["report generated"]),
            ])
            return tasks

        if any(k in lower for k in ["fix", "debug", "error", "issue"]):
            tasks.extend([
                GoalTask(task_id=f"{goal_id}_t1", title="Analyze error", description="Analyze the error or issue", agent="coding", priority=TaskPriority.URGENT, tools=["terminal", "filesystem"], success_criteria=["error identified"]),
                GoalTask(task_id=f"{goal_id}_t2", title="Implement fix", description="Implement fix", agent="coding", priority=TaskPriority.URGENT, dependencies=[f"{goal_id}_t1"], tools=["write_file", "terminal"], success_criteria=["fix implemented"]),
                GoalTask(task_id=f"{goal_id}_t3", title="Verify fix", description="Verify fix works", agent="verification", priority=TaskPriority.HIGH, dependencies=[f"{goal_id}_t2"], success_criteria=["error resolved"]),
            ])
            return tasks

        if any(k in lower for k in ["open", "launch", "start", "run"]):
            tasks.extend([
                GoalTask(task_id=f"{goal_id}_t1", title="Execute command", description=request, agent="terminal", priority=TaskPriority.NORMAL, tools=["terminal"], success_criteria=["command executed"]),
            ])
            return tasks

        tasks.append(GoalTask(task_id=f"{goal_id}_t1", title="Process request", description=request, agent="general", priority=TaskPriority.NORMAL, success_criteria=["task completed"]))
        return tasks

    def _derive_success_criteria(self, request: str, tasks: list[GoalTask]) -> list[str]:
        criteria = [f"All {len(tasks)} tasks completed"]
        for task in tasks:
            criteria.extend(task.success_criteria)
        return criteria

    def re_plan(self, goal: Goal, failed_task: GoalTask) -> Goal:
        """Re-plan after a task failure."""
        if failed_task.retries < failed_task.max_retries:
            failed_task.retries += 1
            failed_task.status = GoalStatus.PENDING
            failed_task.error = None
            return goal

        fallback = failed_task.fallback_agent or "general"
        failed_task.agent = fallback
        failed_task.status = GoalStatus.PENDING
        failed_task.error = None
        failed_task.retries = 0
        return goal


_goal_engine: GoalEngine | None = None


def get_goal_engine(ai_service: Any | None = None) -> GoalEngine:
    global _goal_engine
    if _goal_engine is None:
        _goal_engine = GoalEngine(ai_service=ai_service)
    return _goal_engine
