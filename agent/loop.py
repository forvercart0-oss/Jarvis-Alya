"""Agent loop: PLAN → EXECUTE → OBSERVE → VERIFY → RECOVER → COMPLETE."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import suppress
from typing import Any

from agent.models import AgentArtifacts, AgentPlan, AgentState, AgentTask, ConfidenceLevel, TaskStatus
from agent.state import get_state_manager
from agent.verifier import verification_engine

logger = logging.getLogger("jarvis.agent.loop")


class AgentLoop:
    def __init__(
        self,
        tool_execute: Any,
        ai_provider: Any | None = None,
        max_retries: int = 3,
        on_event: Any = None,
    ):
        self._tool_execute = tool_execute
        self._ai_provider = ai_provider
        self._max_retries = max_retries
        self._on_event = on_event
        self._cancel = False

    async def run(self, session_id: str, plan: AgentPlan) -> AsyncGenerator[dict[str, Any], None]:
        state_mgr = get_state_manager()
        artifacts = AgentArtifacts(task_id=session_id)
        await self._emit("agent_loop_started", {"session_id": session_id})

        try:
            for idx, task in enumerate(plan.tasks):
                if self._cancel:
                    await state_mgr.set_state(session_id, AgentState.CANCELLED)
                    yield {"event": "agent_cancelled", "data": {"session_id": session_id}}
                    return

                task.status = TaskStatus.RUNNING
                task.started_at = __import__("datetime").datetime.utcnow()
                await self._emit("agent_step_started", {"task": task.to_dict(), "index": idx})

                success = False
                observation = ""
                for attempt in range(task.max_retries + 1):
                    if self._cancel:
                        task.status = TaskStatus.CANCELLED
                        yield {"event": "agent_cancelled", "data": {"session_id": session_id}}
                        return

                    if attempt > 0:
                        task.status = TaskStatus.RECOVERING
                        await state_mgr.set_state(session_id, AgentState.RECOVERING)
                        await self._emit("agent_recovering", {"task_id": task.task_id, "attempt": attempt})
                        fixed = await self._attempt_fix(task, artifacts, observation)
                        if not fixed:
                            break

                    task.status = TaskStatus.RUNNING
                    await state_mgr.set_state(session_id, AgentState.EXECUTING)
                    result = await self._execute_task(task, artifacts)
                    task.duration_ms = result.get("duration_ms", 0)

                    if task.dry_run:
                        success = True
                        task.result = result
                        break

                    await state_mgr.set_state(session_id, AgentState.OBSERVING)
                    observation = await self._observe(task, result, artifacts)
                    task.observation = observation

                    await state_mgr.set_state(session_id, AgentState.VERIFYING)
                    verified, confidence, verification_msg = verification_engine.verify(
                        task.type.value, result, observation
                    )
                    task.verification = verification_msg
                    task.confidence = confidence
                    await self._emit(
                        "agent_verifying",
                        {"task_id": task.task_id, "confidence": confidence.value, "message": verification_msg},
                    )

                    if verified and confidence in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM):
                        success = True
                        task.result = result
                        task.status = TaskStatus.COMPLETED
                        break

                    task.error = result.get("error", "Verification failed")
                    artifacts.errors.append({
                        "task_id": task.task_id, "error": task.error,
                        "attempt": attempt, "observation": observation,
                    })
                    await self._emit(
                        "agent_error",
                        {"task_id": task.task_id, "error": task.error, "attempt": attempt, "observation": observation},
                    )

                task.finished_at = __import__("datetime").datetime.utcnow()
                if not success:
                    task.status = TaskStatus.FAILED
                    await self._emit("agent_step_completed", {"task": task.to_dict(), "success": False})
                    await state_mgr.set_state(session_id, AgentState.FAILED)
                    yield {"event": "agent_failed", "data": {"session_id": session_id, "task": task.to_dict()}}
                    return

                await self._emit("agent_step_completed", {"task": task.to_dict(), "success": True})

            await state_mgr.set_state(session_id, AgentState.COMPLETED)
            artifacts.summary = f"Completed {len(plan.tasks)} tasks successfully."
            await self._emit("agent_completed", {"session_id": session_id, "artifacts": artifacts.to_dict()})
            yield {
                "event": "agent_completed",
                "data": {
                    "session_id": session_id,
                    "state": AgentState.COMPLETED.value,
                    "artifacts": artifacts.to_dict(),
                },
            }
        except Exception as exc:
            logger.error("Agent loop error: %s", exc)
            await state_mgr.set_state(session_id, AgentState.FAILED)
            yield {"event": "agent_failed", "data": {"session_id": session_id, "error": str(exc)}}

    def cancel(self):
        self._cancel = True

    async def _execute_task(self, task: AgentTask, artifacts: AgentArtifacts) -> dict[str, Any]:
        start = __import__("time").time()
        try:
            if task.dry_run:
                return {"success": True, "dry_run": True, "duration_ms": 0, "output": "Dry run - no side effects"}

            result = await self._tool_execute(task.type.value, confirmed=False, **task.arguments)
            if hasattr(result, "_data"):
                data = result._data
            elif hasattr(result, "__dict__"):
                data = {k: v for k, v in result.__dict__.items() if not k.startswith("_")}
            elif isinstance(result, dict):
                data = result
            else:
                data = {"success": bool(result)}
            duration = int((__import__("time").time() - start) * 1000)
            data["duration_ms"] = duration
            task.output = str(data.get("stdout", data.get("result", data.get("output", ""))))[:5000]
            task.command = task.arguments.get("command", "")
            if data.get("success"):
                artifacts.commands_run.append({
                    "task_id": task.task_id, "command": task.command,
                    "success": True, "duration_ms": duration,
                })
            return data
        except Exception as exc:
            duration = int((__import__("time").time() - start) * 1000)
            return {"success": False, "error": str(exc), "duration_ms": duration}

    async def _observe(self, task: AgentTask, result: dict[str, Any], artifacts: AgentArtifacts) -> str:
        observation = ""
        try:
            if task.type.value in ("vision_capture_screen", "vision_analyze_screen"):
                observation = result.get("description", result.get("text", result.get("output", "")))
            elif task.type.value == "terminal":
                observation = result.get("stdout", "") + "\n" + result.get("stderr", "")
            else:
                observation = result.get("output", result.get("result", ""))
            artifacts.timeline.append({
                "ts": __import__("datetime").datetime.utcnow().isoformat(),
                "task_id": task.task_id,
                "type": "observation",
                "content": observation[:500],
            })
        except Exception as exc:
            logger.debug("Observation failed: %s", exc)
        return observation

    async def _attempt_fix(self, task: AgentTask, artifacts: AgentArtifacts, observation: str) -> bool:
        if not self._ai_provider:
            return False
        try:
            prompt = (
                f"A task failed. Analyze the error and observation, then suggest a fix.\n"
                f"Task: {task.title}\n"
                f"Error: {task.error}\n"
                f"Observation: {observation[:500]}\n"
                f"Command: {task.command}\n"
                f"Provide a concise fix suggestion."
            )
            messages = [{"role": "user", "content": prompt}]
            result = await self._ai_provider.chat_with_tools(messages, tools_spec=[])
            suggestion = result.get("content", "")
            artifacts.fixes_applied.append({"task_id": task.task_id, "suggestion": suggestion[:500]})
            return False
        except Exception:
            return False

    async def _emit(self, event: str, data: dict[str, Any]):
        if self._on_event:
            with suppress(Exception):
                await self._on_event(event, data)
