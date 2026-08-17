"""Checkpoint Manager for JARVIS Phase 23.

Provides task checkpointing for long-running goals so execution
can resume from the last valid checkpoint after crashes.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.agent.checkpoints")


@dataclass
class Checkpoint:
    checkpoint_id: str
    goal_id: str
    task_id: str
    label: str
    state: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.checkpoint_id:
            self.checkpoint_id = str(uuid.uuid4())[:8]

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "goal_id": self.goal_id,
            "task_id": self.task_id,
            "label": self.label,
            "state": self.state,
            "artifacts": self.artifacts,
            "created_at": self.created_at,
        }


class CheckpointManager:
    """Manages checkpoints for goal execution."""

    def __init__(self):
        self._checkpoints: dict[str, Checkpoint] = {}
        self._goal_checkpoints: dict[str, list[str]] = {}

    def create(self, goal_id: str, task_id: str, label: str, state: dict[str, Any] | None = None, artifacts: list[str] | None = None) -> Checkpoint:
        checkpoint = Checkpoint(
            checkpoint_id=str(uuid.uuid4())[:8],
            goal_id=goal_id,
            task_id=task_id,
            label=label,
            state=state or {},
            artifacts=artifacts or [],
        )
        self._checkpoints[checkpoint.checkpoint_id] = checkpoint
        self._goal_checkpoints.setdefault(goal_id, []).append(checkpoint.checkpoint_id)
        logger.debug("Created checkpoint: %s for goal %s", checkpoint.checkpoint_id, goal_id)
        return checkpoint

    def get_last(self, goal_id: str) -> Checkpoint | None:
        cids = self._goal_checkpoints.get(goal_id, [])
        if not cids:
            return None
        last = cids[-1]
        return self._checkpoints.get(last)

    def get_for_goal(self, goal_id: str) -> list[Checkpoint]:
        return [self._checkpoints[cid] for cid in self._goal_checkpoints.get(goal_id, []) if cid in self._checkpoints]

    def restore(self, goal_id: str) -> dict[str, Any] | None:
        checkpoint = self.get_last(goal_id)
        if checkpoint:
            return checkpoint.state
        return None

    def clear_goal(self, goal_id: str) -> int:
        cids = self._goal_checkpoints.pop(goal_id, [])
        for cid in cids:
            self._checkpoints.pop(cid, None)
        return len(cids)


checkpoint_manager = CheckpointManager()
