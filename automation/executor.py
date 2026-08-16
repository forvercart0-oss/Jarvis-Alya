"""Task executor: execute task plans step by step with verification, retry, and recovery."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from contextlib import suppress
from typing import Any

from automation.monitor import get_task_monitor
from automation.policies import get_policy_for_complexity
from automation.recovery import TaskRecovery
from automation.task_state import TaskComplexity, TaskState
from automation.verifier import ActionVerifier
from backend.services.ws_manager import ws_manager
from safety.checker import get_safety_checker
from safety.confirmation import get_confirmation_manager
from safety.policy import PolicyAction, get_policy_engine

logger = logging.getLogger("jarvis.automation.executor")


class TaskExecutor:
    """Executes task plans with verification, retry, and recovery."""

    def __init__(self, tool_execute: Any, ai_service: Any | None = None, tts_callback: Any | None = None):
        self._tool_execute = tool_execute
        self._ai_service = ai_service
        self._tts = tts_callback
        self._verifier = ActionVerifier()
        self._recovery = TaskRecovery(tool_execute)
        self._safety = get_safety_checker()
        self._policy = get_policy_engine()

    async def execute_plan(
        self, task_id: str, plan: Any, dry_run: bool = False
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Execute a task plan step by step."""
        monitor = get_task_monitor()
        complexity = TaskComplexity(
            plan.complexity.value if hasattr(plan, "complexity") else "moderate"
        )
        policy = get_policy_for_complexity(complexity)

        plan_dict = plan.to_dict() if hasattr(plan, "to_dict") else str(plan)
        await ws_manager.broadcast("task_started", {"task_id": task_id, "plan": plan_dict})

        if dry_run:
            await ws_manager.broadcast(
                "task_completed",
                {
                    "task_id": task_id,
                    "status": TaskState.COMPLETED.value,
                    "dry_run": True,
                    "result": "Dry run completed.",
                },
            )
            yield {
                "event": "task_completed",
                "data": {
                    "task_id": task_id,
                    "status": TaskState.COMPLETED.value,
                    "dry_run": True,
                },
            }
            return

        monitor.register(task_id, timeout=policy.timeout_seconds)
        step_results: list[dict[str, Any]] = []
        start_time = time.time()

        for idx, step in enumerate(plan.steps):
            entry = monitor.get_entry(task_id)
            if entry and entry.cancelled:
                await ws_manager.broadcast("task_cancelled", {"task_id": task_id})
                yield {"event": "task_cancelled", "data": {"task_id": task_id}}
                return

            step_dict = step.to_dict() if hasattr(step, "to_dict") else str(step)
            await ws_manager.broadcast(
                "task_step_started",
                {
                    "task_id": task_id,
                    "step_index": idx,
                    "step": step_dict,
                    "current_action": step.title,
                },
            )

            step_start = time.time()
            success = False
            result = None
            error = None

            try:
                result = await self._execute_step(step, task_id, policy)
                success = True
            except Exception as exc:
                error = str(exc)
                logger.error("Step %d failed: %s", idx, error)
                step_dict = (
                    step.to_dict() if hasattr(step, "to_dict") else str(step)
                )
                recovered, recovery_result = await self._recovery.recover_step(
                    step_dict, error
                )
                if recovered:
                    success = True
                    result = recovery_result
                    error = None

            duration_ms = (time.time() - step_start) * 1000
            step_results.append(
                {
                    "step": idx,
                    "title": step.title,
                    "success": success,
                    "error": error,
                    "duration_ms": duration_ms,
                }
            )

            monitor.heartbeat(task_id)

            yield {
                "event": "task_step_completed",
                "data": {
                    "task_id": task_id,
                    "step_index": idx,
                    "success": success,
                    "error": error,
                    "duration_ms": duration_ms,
                    "result": result,
                },
            }

            if not success:
                await ws_manager.broadcast(
                    "task_step_failed",
                    {
                        "task_id": task_id,
                        "step_index": idx,
                        "error": error,
                    },
                )

        elapsed = time.time() - start_time
        final_status = (
            TaskState.COMPLETED
            if all(r["success"] for r in step_results)
            else TaskState.FAILED
        )

        await ws_manager.broadcast(
            "task_completed",
            {
                "task_id": task_id,
                "status": final_status.value,
                "elapsed_seconds": elapsed,
                "steps": step_results,
            },
        )

        yield {
            "event": "task_completed",
            "data": {
                "task_id": task_id,
                "status": final_status.value,
                "elapsed_seconds": elapsed,
                "steps": step_results,
            },
        }

        if self._tts and final_status == TaskState.COMPLETED:
            with suppress(Exception):
                await self._tts("Task complete.")

        monitor.unregister(task_id)

    async def _execute_step(self, step: Any, task_id: str, policy: Any) -> Any:
        """Execute a single step."""
        tool_name = step.tool or step.action
        arguments = dict(step.arguments or {})

        # Safety check
        safety_verdict = self._safety.check_tool(tool_name, arguments)
        if safety_verdict.verdict.value == "disallowed":
            raise PermissionError(
                safety_verdict.message or f"Tool {tool_name} is not permitted."
            )

        # Policy check
        action, message = self._policy.evaluate_request(tool_name, arguments)

        if action == PolicyAction.ASK:
            await ws_manager.broadcast(
                "task_permission_required",
                {
                    "task_id": task_id,
                    "tool": tool_name,
                    "arguments": arguments,
                    "message": message,
                },
            )
            confirmed = await self._wait_for_confirmation(task_id, message)
            if not confirmed:
                raise PermissionError("User denied the operation.")

        # Execute
        result = await self._tool_execute(tool_name, confirmed=True, **arguments)
        data = self._extract_data(result)

        # Verification
        if policy.verification_required:
            verified, verify_msg = self._verifier.verify(tool_name, data)
            await ws_manager.broadcast(
                "task_verifying",
                {
                    "task_id": task_id,
                    "verified": verified,
                    "message": verify_msg,
                },
            )
            if not verified:
                raise RuntimeError(f"Verification failed: {verify_msg}")

        return data

    def _extract_data(self, result: Any) -> dict[str, Any]:
        if hasattr(result, "_data"):
            return result._data
        if hasattr(result, "__dict__"):
            return {
                k: v for k, v in result.__dict__.items() if not k.startswith("_")
            }
        if isinstance(result, dict):
            return result
        return {"success": bool(result)}

    async def _wait_for_confirmation(self, task_id: str, message: str) -> bool:
        """Wait for user confirmation."""
        request = get_confirmation_manager().create_request(
            tool_name="task_step",
            arguments={"task_id": task_id},
            risk_level="medium",
            timeout_seconds=120,
        )
        await ws_manager.broadcast(
            "task_permission_required",
            {
                "task_id": task_id,
                "request_id": request.id,
                "message": message,
            },
        )
        confirmed = await get_confirmation_manager().wait_for_confirmation(
            request.id, timeout=120.0
        )
        return bool(confirmed)
