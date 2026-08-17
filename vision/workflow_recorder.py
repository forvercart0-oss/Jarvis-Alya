"""Workflow recorder for JARVIS Phase 30.

Records visual automation workflows: screen state, target element,
action, and result.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.vision.workflow_recorder")


@dataclass
class RecordedStep:
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    screen_hash: str = ""
    screenshot_path: str = ""
    target: str = ""
    action_type: str = ""
    coordinates: dict[str, int] = field(default_factory=dict)
    text_entered: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    success: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "timestamp": self.timestamp,
            "screen_hash": self.screen_hash,
            "screenshot_path": self.screenshot_path,
            "target": self.target,
            "action_type": self.action_type,
            "coordinates": self.coordinates,
            "text_entered": self.text_entered,
            "result": self.result,
            "success": self.success,
            "metadata": self.metadata,
        }


@dataclass
class RecordedWorkflow:
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    created_at: float = field(default_factory=time.time)
    steps: list[RecordedStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "created_at": self.created_at,
            "steps": [s.to_dict() for s in self.steps],
            "metadata": self.metadata,
        }


class WorkflowRecorder:
    def __init__(self):
        self._recording: bool = False
        self._current_workflow: RecordedWorkflow | None = None

    @property
    def recording(self) -> bool:
        return self._recording

    def start(self, name: str = "") -> RecordedWorkflow:
        self._current_workflow = RecordedWorkflow(name=name or f"workflow_{int(time.time())}")
        self._recording = True
        return self._current_workflow

    def stop(self) -> RecordedWorkflow | None:
        self._recording = False
        return self._current_workflow

    def record_step(self, **kwargs: Any) -> RecordedStep:
        if not self._recording or not self._current_workflow:
            raise RuntimeError("No active recording")
        step = RecordedStep(**kwargs)
        self._current_workflow.steps.append(step)
        return step

    def get_current(self) -> RecordedWorkflow | None:
        return self._current_workflow


workflow_recorder = WorkflowRecorder()
