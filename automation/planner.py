"""Task planner: decompose user requests into executable plans."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from automation.policies import classify_task_complexity
from automation.task_state import TaskComplexity

logger = logging.getLogger("jarvis.automation.planner")


class PlanStep:
    """A single step in a task plan."""

    def __init__(
        self,
        step_id: str,
        title: str,
        action: str,
        tool: str | None = None,
        arguments: dict[str, Any] | None = None,
        risk: str = "low",
        verify: str | None = None,
        fallback: list[str] | None = None,
        estimated_duration: float = 5.0,
    ):
        self.step_id = step_id
        self.title = title
        self.action = action
        self.tool = tool
        self.arguments = arguments or {}
        self.risk = risk
        self.verify = verify
        self.fallback = fallback or []
        self.estimated_duration = estimated_duration

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "title": self.title,
            "action": self.action,
            "tool": self.tool,
            "arguments": self.arguments,
            "risk": self.risk,
            "verify": self.verify,
            "fallback": self.fallback,
            "estimated_duration": self.estimated_duration,
        }


class TaskPlan:
    """A complete plan for a task."""

    def __init__(
        self,
        plan_id: str,
        task_id: str,
        title: str,
        description: str,
        complexity: TaskComplexity,
        steps: list[PlanStep] | None = None,
        approved: bool = False,
        dry_run: bool = False,
        variables: dict[str, Any] | None = None,
        created_at: str = "",
    ):
        self.plan_id = plan_id
        self.task_id = task_id
        self.title = title
        self.description = description
        self.complexity = complexity
        self.steps = steps or []
        self.approved = approved
        self.dry_run = dry_run
        self.variables = variables or {}
        self.created_at = created_at or __import__(
            "datetime"
        ).datetime.utcnow().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "complexity": self.complexity.value,
            "steps": [s.to_dict() for s in self.steps],
            "approved": self.approved,
            "dry_run": self.dry_run,
            "variables": self.variables,
            "created_at": self.created_at,
        }


class TaskPlanner:
    """Plans multi-step automation tasks."""

    def __init__(self, ai_service: Any | None = None, tool_registry: Any | None = None):
        self._ai_service = ai_service
        self._tool_registry = tool_registry

    def create_plan(self, task_id: str, description: str, context: dict | None = None) -> TaskPlan:
        """Create a plan for a given task description."""
        complexity = classify_task_complexity(description)
        plan = TaskPlan(
            plan_id=str(uuid.uuid4())[:8],
            task_id=task_id,
            title=description[:80],
            description=description,
            complexity=complexity,
            variables=context or {},
        )
        plan.steps = self._decompose(description, complexity)
        return plan

    def _decompose(self, description: str, complexity: TaskComplexity) -> list[PlanStep]:
        """Decompose a description into executable steps."""
        lower = description.lower()
        steps: list[PlanStep] = []

        # Browser-based workflows
        if any(k in lower for k in ["github", "git", "repository", "repo"]):
            steps.append(
                PlanStep(
                    step_id=self._uid(),
                    title="Open browser",
                    action="open_browser",
                    tool="open_browser",
                    arguments={"url": "https://github.com"},
                    risk="low",
                    verify="Browser opened successfully",
                    fallback=["launch_chrome", "launch_firefox"],
                    estimated_duration=3.0,
                )
            )
            steps.append(
                PlanStep(
                    step_id=self._uid(),
                    title="Navigate to GitHub",
                    action="browser_navigate",
                    tool="browser_navigate",
                    arguments={"url": "https://github.com"},
                    risk="low",
                    verify="GitHub loaded",
                    estimated_duration=5.0,
                )
            )

        if "search" in lower and "github" in lower:
            steps.append(
                PlanStep(
                    step_id=self._uid(),
                    title="Search GitHub",
                    action="browser_find_and_click",
                    tool="browser_click",
                    arguments={"selector": "input[type='text']"},
                    risk="low",
                    verify="Search input found",
                    estimated_duration=3.0,
                )
            )

        if "check" in lower and "repository" in lower:
            steps.append(
                PlanStep(
                    step_id=self._uid(),
                    title="Check repository",
                    action="read_repo_info",
                    tool="browser_read",
                    arguments={"selector": "body"},
                    risk="low",
                    verify="Repository information extracted",
                    estimated_duration=5.0,
                )
            )

        # Project creation workflows
        if any(k in lower for k in ["create", "build", "make"]) and any(
            k in lower for k in ["project", "app", "react", "ecommerce"]
        ):
            steps.append(
                PlanStep(
                    step_id=self._uid(),
                    title="Create project structure",
                    action="create_project",
                    tool="create_project",
                    arguments={"name": "new-project"},
                    risk="medium",
                    verify="Project files created",
                    estimated_duration=5.0,
                )
            )
            steps.append(
                PlanStep(
                    step_id=self._uid(),
                    title="Install dependencies",
                    action="install_deps",
                    tool="terminal",
                    arguments={"command": "npm install"},
                    risk="medium",
                    verify="Dependencies installed",
                    estimated_duration=30.0,
                )
            )

        if "run" in lower and "test" in lower:
            steps.append(
                PlanStep(
                    step_id=self._uid(),
                    title="Run tests",
                    action="run_tests",
                    tool="run_project_command",
                    arguments={"command": "npm test"},
                    risk="low",
                    verify="Tests completed",
                    estimated_duration=20.0,
                )
            )

        if "start" in lower and ("server" in lower or "dev" in lower):
            steps.append(
                PlanStep(
                    step_id=self._uid(),
                    title="Start development server",
                    action="start_server",
                    tool="run_project_command",
                    arguments={"command": "npm run dev"},
                    risk="medium",
                    verify="Server started",
                    estimated_duration=5.0,
                )
            )

        # Browser open
        if "open" in lower and (
            "chrome" in lower or "firefox" in lower or "browser" in lower
        ):
            url = "https://github.com" if "github" in lower else None
            steps.append(
                PlanStep(
                    step_id=self._uid(),
                    title="Open browser",
                    action="open_browser",
                    tool="open_browser",
                    arguments={"url": url or "about:blank"},
                    risk="low",
                    verify="Browser opened",
                    estimated_duration=3.0,
                )
            )

        # Gmail / messages
        if "gmail" in lower or "messages" in lower or "email" in lower:
            steps.append(
                PlanStep(
                    step_id=self._uid(),
                    title="Open Gmail",
                    action="open_gmail",
                    tool="open_browser",
                    arguments={"url": "https://mail.google.com"},
                    risk="low",
                    verify="Gmail loaded",
                    estimated_duration=5.0,
                )
            )

        # Simple fallback
        if not steps:
            steps.append(
                PlanStep(
                    step_id=self._uid(),
                    title="Process request",
                    action="process",
                    tool="system_info",
                    arguments={},
                    risk="low",
                    verify="Completed",
                    estimated_duration=2.0,
                )
            )

        return steps

    def _uid(self) -> str:
        return str(uuid.uuid4())[:8]
