"""Task manager: central orchestrator for all automation tasks."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from typing import Any

from automation.executor import TaskExecutor
from automation.monitor import get_task_monitor
from automation.planner import TaskPlanner
from automation.policies import classify_task_complexity
from automation.scheduler import TaskScheduler
from automation.task_state import TaskState
from automation.task_store import TaskStore
from backend.services.ws_manager import ws_manager

logger = logging.getLogger("jarvis.automation.manager")


class TaskManager:
    """Central orchestrator for JARVIS automation tasks."""

    def __init__(
        self,
        memory_manager: Any,
        tool_execute: Any,
        ai_service: Any | None = None,
        tts_callback: Any | None = None,
    ):
        self._memory = memory_manager
        self._tool_execute = tool_execute
        self._ai_service = ai_service
        self._tts = tts_callback
        self._store = TaskStore(memory_manager)
        self._planner = TaskPlanner(
            ai_service=ai_service,
            tool_registry=getattr(tool_execute, "registry", None),
        )
        self._executor = TaskExecutor(
            tool_execute=tool_execute,
            ai_service=ai_service,
            tts_callback=tts_callback,
        )
        self._scheduler = TaskScheduler(
            self._store, execute_callback=self._background_execute
        )
        self._active_generators: dict[str, Any] = {}
        self._running = False

    @property
    def store(self) -> TaskStore:
        return self._store

    # ------------------------------------------------------------- lifecycle
    async def start(self) -> None:
        self._running = True
        await self._scheduler.start()

    async def stop(self) -> None:
        self._running = False
        await self._scheduler.stop()
        for task_id in list(self._active_generators.keys()):
            await self.cancel_task(task_id)

    # ------------------------------------------------------------- task creation
    async def create_task(
        self,
        description: str,
        task_type: str = "general",
        auto_execute: bool = False,
        context: dict | None = None,
    ) -> dict:
        """Create a new task and optionally start it."""
        complexity = classify_task_complexity(description)
        task = self._store.create_task(
            description,
            task_type=task_type,
            complexity=complexity.value,
            metadata=context,
        )

        await ws_manager.broadcast("task_created", {"task": task})

        plan = self._planner.create_plan(task["id"], description, context)
        await ws_manager.broadcast("task_planning", {"task_id": task["id"], "plan": plan.to_dict()})

        if auto_execute:
            self._active_generators[task["id"]] = asyncio.create_task(
                self._execute_task(task["id"], plan)
            )
        else:
            self._store.update_task(task["id"], status=TaskState.PLANNING.value)

        return task

    # ------------------------------------------------------------- execution
    async def _execute_task(self, task_id: str, plan: Any) -> None:
        """Execute a task plan."""
        gen = self._executor.execute_plan(task_id, plan)
        self._active_generators[task_id] = gen
        try:
            async for event in gen:
                ev_type = event.get("event")
                if ev_type == "task_completed":
                    status = event["data"].get("status", TaskState.COMPLETED.value)
                    self._store.update_task(task_id, status=status, result=event["data"])
                elif ev_type == "task_cancelled":
                    self._store.update_task(task_id, status=TaskState.CANCELLED.value)
                elif ev_type == "task_step_completed":
                    step_data = event["data"]
                    self._store.append_log(
                        task_id,
                        step_data.get("current_action", f"Step {step_data.get('step_index', 0)}"),
                        "success" if step_data.get("success") else f"Failed: {step_data.get('error', 'unknown')}",
                        step_data.get("duration_ms", 0),
                    )
        except asyncio.CancelledError:
            self._store.update_task(task_id, status=TaskState.CANCELLED.value)
        except Exception as exc:
            logger.error("Task %s execution error: %s", task_id, exc)
            self._store.update_task(task_id, status=TaskState.FAILED.value, result=str(exc))
        finally:
            self._active_generators.pop(task_id, None)

    async def _background_execute(self, task_id: str) -> None:
        """Execute a scheduled task in background."""
        task = self._store.get_task(task_id)
        if not task:
            return
        plan = self._planner.create_plan(
            task_id, task.get("description", ""), task.get("metadata")
        )
        await self._execute_task(task_id, plan)

    # ------------------------------------------------------------- control
    async def start_task(self, task_id: str) -> dict:
        task = self._store.get_task(task_id)
        if not task:
            return {"error": "Task not found"}
        plan = self._planner.create_plan(
            task_id, task.get("description", ""), task.get("metadata")
        )
        self._store.update_task(task_id, status=TaskState.RUNNING.value)
        self._active_generators[task_id] = asyncio.create_task(
            self._execute_task(task_id, plan)
        )
        return {"status": "started", "task_id": task_id}

    async def pause_task(self, task_id: str) -> dict:
        task = self._store.get_task(task_id)
        if not task:
            return {"error": "Task not found"}
        self._store.update_task(task_id, status=TaskState.PAUSED.value)
        monitor = get_task_monitor()
        monitor.cancel(task_id)
        return {"status": "paused", "task_id": task_id}

    async def resume_task(self, task_id: str) -> dict:
        task = self._store.get_task(task_id)
        if not task:
            return {"error": "Task not found"}
        self._store.update_task(task_id, status=TaskState.RUNNING.value)
        plan = self._planner.create_plan(
            task_id, task.get("description", ""), task.get("metadata")
        )
        self._active_generators[task_id] = asyncio.create_task(
            self._execute_task(task_id, plan)
        )
        return {"status": "resumed", "task_id": task_id}

    async def cancel_task(self, task_id: str) -> dict:
        task = self._store.get_task(task_id)
        if not task:
            return {"error": "Task not found"}
        self._store.update_task(task_id, status=TaskState.CANCELLED.value)
        monitor = get_task_monitor()
        monitor.cancel(task_id)
        gen = self._active_generators.pop(task_id, None)
        if gen:
            with suppress(Exception):
                await gen.aclose()
        await ws_manager.broadcast("task_cancelled", {"task_id": task_id})
        return {"status": "cancelled", "task_id": task_id}

    async def approve_plan(self, task_id: str) -> dict:
        task = self._store.get_task(task_id)
        if not task:
            return {"error": "Task not found"}
        self._store.update_task(task_id, status=TaskState.RUNNING.value)
        plan = self._planner.create_plan(
            task_id, task.get("description", ""), task.get("metadata")
        )
        self._active_generators[task_id] = asyncio.create_task(
            self._execute_task(task_id, plan)
        )
        return {"status": "approved", "task_id": task_id}

    async def deny_plan(self, task_id: str) -> dict:
        task = self._store.get_task(task_id)
        if not task:
            return {"error": "Task not found"}
        self._store.update_task(task_id, status=TaskState.FAILED.value, result="User denied the plan.")
        return {"status": "denied", "task_id": task_id}

    # ------------------------------------------------------------- queries
    def get_task(self, task_id: str) -> dict | None:
        return self._store.get_task(task_id)

    def get_tasks(self, status: str | None = None) -> list[dict]:
        return self._store.get_tasks(status)

    def get_active_tasks(self) -> list[dict]:
        return self._store.get_active_tasks()

    def get_task_history(self, limit: int = 50) -> list[dict]:
        return self._store.get_tasks(limit=limit)
