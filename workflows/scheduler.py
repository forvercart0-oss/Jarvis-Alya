"""Workflow scheduler for JARVIS Phase 11."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

from workflows.engine import WorkflowEngine
from workflows.models import Workflow
from workflows.store import WorkflowStore

logger = logging.getLogger("jarvis.workflows.scheduler")


class WorkflowScheduler:
    def __init__(self, store: WorkflowStore, engine: WorkflowEngine, execute_callback: Any | None = None):
        self._store = store
        self._engine = engine
        self._execute = execute_callback
        self._running = False
        self._task: asyncio.Task | None = None
        self._active_workflows: dict[str, asyncio.Task] = {}

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._tick())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        for task in list(self._active_workflows.values()):
            task.cancel()
        self._active_workflows.clear()

    async def _tick(self) -> None:
        while self._running:
            try:
                now = datetime.now(UTC)
                workflows = self._store.get_workflows(status="active")
                for wf_data in workflows:
                    trigger = wf_data.get("trigger", {})
                    trigger_type = trigger.get("type", "manual")
                    if trigger_type in ("scheduled", "recurring"):
                        schedule = trigger.get("schedule", "")
                        if self._is_due(schedule, now, wf_data.get("last_run")):
                            if self._execute and wf_data.get("enabled"):
                                self._execute(wf_data["workflow_id"])
            except Exception as exc:
                logger.warning("Scheduler tick failed: %s", exc)
            await asyncio.sleep(30)

    def _is_due(self, schedule: str, now: datetime, last_run: str | None) -> bool:
        try:
            hour_min = schedule.strip()
            if ":" in hour_min:
                parts = hour_min.split(":")
                target_hour = int(parts[0])
                target_min = int(parts[1])
                current = now.strftime("%H:%M")
                expected = f"{target_hour:02d}:{target_min:02d}"
                if current == expected and (last_run or "") != current:
                    return True
        except Exception as exc:
            logger.debug("Schedule parse failed: %s", exc)
        return False

    async def run_now(self, workflow_id: str) -> None:
        wf_data = self._store.get_workflow(workflow_id)
        if not wf_data:
            return
        from workflows.models import Workflow
        workflow = Workflow.from_dict(wf_data)
        if workflow_id in self._active_workflows:
            task = self._active_workflows[workflow_id]
            task.cancel()
        task = asyncio.create_task(self._run_workflow(workflow))
        self._active_workflows[workflow_id] = task

    async def _run_workflow(self, workflow: Workflow) -> None:
        self._store.update_workflow(workflow.workflow_id, {"status": "running"})
        async for event in self._engine.execute(workflow):
            if self._engine._ws_broadcast:
                try:
                    await self._engine._ws_broadcast(event.get("event", ""), event.get("data", {}))
                except Exception:
                    pass
        self._active_workflows.pop(workflow.workflow_id, None)
        final_status = "active" if event.get("data", {}).get("status") != "failed" else "failed"
        self._store.update_workflow(workflow.workflow_id, {"status": final_status, "last_run": datetime.utcnow().isoformat()})


def suppress(exc_type):
    import contextlib
    return contextlib.suppress(exc_type)
