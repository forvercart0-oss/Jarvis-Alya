"""Workflow execution engine for JARVIS Phase 11."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, AsyncGenerator

from workflows.conditions import ConditionEvaluator
from workflows.models import Workflow, WorkflowRun, WorkflowStep, WorkflowStatus
from workflows.variables import VariableResolver

logger = logging.getLogger("jarvis.workflows.engine")


class WorkflowEngine:
    def __init__(
        self,
        tool_execute: Any | None = None,
        ai_provider: Any | None = None,
        ws_broadcast: Any | None = None,
        approval_callback: Any | None = None,
    ):
        self._tool_execute = tool_execute
        self._ai_provider = ai_provider
        self._ws_broadcast = ws_broadcast
        self._approval_callback = approval_callback
        self._condition_evaluator = ConditionEvaluator()
        self._running_tasks: dict[str, asyncio.Task] = {}

    async def execute(self, workflow: Workflow, context: dict[str, Any] | None = None) -> AsyncGenerator[dict[str, Any], None]:
        run = WorkflowRun(run_id=str(__import__("uuid").uuid4())[:8], workflow_id=workflow.workflow_id)
        context = context or {}
        variables = VariableResolver(context)
        for key, value in workflow.variables.items():
            variables.set(key, value)

        yield {"event": "workflow_started", "data": {"workflow_id": workflow.workflow_id, "run_id": run.run_id}}

        start_time = time.time()
        step_results: list[dict[str, Any]] = []

        sorted_steps = sorted(workflow.steps, key=lambda s: s.order)
        step_map = {s.step_id: s for s in sorted_steps}
        current_step_id = sorted_steps[0].step_id if sorted_steps else None

        while current_step_id:
            step = step_map.get(current_step_id)
            if not step:
                break

            if step.condition and not self._condition_evaluator.evaluate(step.condition, variables.to_dict()):
                current_step_id = step.next_step_id
                continue

            step_start = time.time()
            success = False
            error = None
            result = None

            yield {"event": "workflow_step_started", "data": {"run_id": run.run_id, "step": step.to_dict()}}

            try:
                result = await self._execute_step(step, variables, run)
                success = True
            except Exception as exc:
                error = str(exc)
                logger.error("Workflow step failed: %s", error)

            duration = time.time() - step_start
            step_record = {
                "step_id": step.step_id,
                "name": step.name,
                "type": step.type,
                "success": success,
                "error": error,
                "result": result,
                "duration_seconds": duration,
                "started_at": datetime.utcnow().isoformat(),
            }
            step_results.append(step_record)
            run.steps.append(step_record)

            if not success:
                run.errors.append({"step_id": step.step_id, "error": error})
                yield {"event": "workflow_step_failed", "data": {"run_id": run.run_id, "step": step.to_dict(), "error": error}}
                if step.retry_policy and step.retry_policy.get("retries", 0) > 0:
                    retries = step.retry_policy.get("retries", 0)
                    backoff = step.retry_policy.get("backoff_seconds", 1.0)
                    for attempt in range(retries):
                        await asyncio.sleep(backoff * (2 ** attempt))
                        try:
                            result = await self._execute_step(step, variables, run)
                            step_record["success"] = True
                            step_record["error"] = None
                            step_record["result"] = result
                            step_record["retry"] = attempt + 1
                            success = True
                            break
                        except Exception as retry_exc:
                            error = str(retry_exc)
                            step_record["error"] = error
                            yield {"event": "workflow_step_failed", "data": {"run_id": run.run_id, "step": step.to_dict(), "error": error, "attempt": attempt + 1}}  # noqa: E501

                if not success:
                    run.status = WorkflowStatus.FAILED
                    run.finished_at = datetime.utcnow().isoformat()
                    run.duration_seconds = time.time() - start_time
                    yield {"event": "workflow_failed", "data": {"run_id": run.run_id, "errors": run.errors}}
                    return

            yield {"event": "workflow_step_completed", "data": {"run_id": run.run_id, "step": step.to_dict(), "result": result}}

            if step.type == "variable" and result:
                variables.set(step.config.get("key", ""), result)

            current_step_id = step.next_step_id

        run.status = WorkflowStatus.COMPLETED
        run.finished_at = datetime.utcnow().isoformat()
        run.duration_seconds = time.time() - start_time
        run.result = {"steps": step_results}
        yield {"event": "workflow_completed", "data": {"run_id": run.run_id, "result": run.result}}

    async def _execute_step(self, step: WorkflowStep, variables: VariableResolver, run: WorkflowRun) -> Any:
        config = variables.resolve(step.config)
        step_type = step.type

        if step_type == "action":
            return await self._execute_action(config)
        if step_type == "browser":
            return await self._execute_browser(config)
        if step_type == "computer":
            return await self._execute_computer(config)
        if step_type == "agent":
            return await self._execute_agent(config)
        if step_type == "research":
            return await self._execute_research(config)
        if step_type == "document":
            return await self._execute_document(config)
        if step_type == "notification":
            return await self._execute_notification(config)
        if step_type == "delay":
            seconds = float(config.get("seconds", 1))
            await asyncio.sleep(seconds)
            return {"waited": seconds}
        if step_type == "variable":
            return config.get("value", "")
        if step_type == "condition":
            return True

        return {"success": True}

    async def _execute_action(self, config: dict[str, Any]) -> Any:
        if not self._tool_execute:
            return {"success": True, "mock": True}
        tool = config.get("tool", "")
        args = config.get("arguments", {})
        return await self._tool_execute(tool, confirmed=False, **args)

    async def _execute_browser(self, config: dict[str, Any]) -> Any:
        action = config.get("action", "navigate")
        url = config.get("url", "")
        if action == "navigate" and url:
            from browser.manager import BrowserManager
            mgr = BrowserManager()
            if not mgr.available:
                await mgr.initialize()
            return await mgr.navigate(url)
        return {"success": True, "action": action}

    async def _execute_computer(self, config: dict[str, Any]) -> Any:
        action = config.get("action", "")
        arguments = config.get("arguments", {})
        from computer.manager import ComputerManager
        mgr = ComputerManager()
        if mgr._safety.requires_confirmation(action):
            if self._approval_callback:
                approved = await self._approval_callback(action, arguments)
                if not approved:
                    raise PermissionError(f"Computer action '{action}' was denied.")
            else:
                raise PermissionError(f"Computer action '{action}' requires approval.")
        return await mgr._run_platform(action, **arguments)

    async def _execute_agent(self, config: dict[str, Any]) -> Any:
        task = config.get("task", "")
        if not task:
            return {"success": True}
        if self._ai_provider:
            try:
                result = await self._ai_provider.chat_with_tools([{"role": "user", "content": task}], tools_spec=[])
                return result
            except Exception as exc:
                return {"success": False, "error": str(exc)}
        return {"success": True, "mock": True}

    async def _execute_research(self, config: dict[str, Any]) -> Any:
        topic = config.get("topic", "")
        if not topic:
            return {"success": False, "error": "No topic provided"}
        try:
            from backend.main import get_research_manager_instance
            mgr = get_research_manager_instance()
            job = await mgr.start_research(topic)
            return {"success": True, "job_id": job.id, "topic": topic}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def _execute_document(self, config: dict[str, Any]) -> Any:
        title = config.get("title", "Workflow Document")
        content = config.get("content", "")
        path = config.get("path", "")
        if not path:
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            path = f"~/Documents/JARVIS-Workflows/{title.replace(' ', '_')}-{timestamp}.md"
        try:
            from pathlib import Path
            dest = Path(path).expanduser()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            return {"success": True, "path": str(dest)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def _execute_notification(self, config: dict[str, Any]) -> Any:
        title = config.get("title", "Workflow Notification")
        message = config.get("message", "")
        if self._ws_broadcast:
            try:
                await self._ws_broadcast("notification_created", {"title": title, "body": message})
            except Exception:
                pass
        return {"success": True, "title": title, "message": message}
