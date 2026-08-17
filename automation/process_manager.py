"""Process manager for JARVIS Phase 13."""

from __future__ import annotations

import logging
import os
import signal
import time
from typing import Any

logger = logging.getLogger("jarvis.automation.processes")


class ManagedProcess:
    def __init__(self, process_id: str, pid: int, command: str, working_dir: str = ""):
        self.process_id = process_id
        self.pid = pid
        self.command = command
        self.working_dir = working_dir
        self.started_at = time.time()
        self.finished_at = None
        self.exit_code = None
        self.status = "running"

    def to_dict(self) -> dict:
        return {
            "process_id": self.process_id,
            "pid": self.pid,
            "command": self.command,
            "working_dir": self.working_dir,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "exit_code": self.exit_code,
            "status": self.status,
        }


class ProcessManager:
    def __init__(self):
        self._processes: dict[str, ManagedProcess] = {}

    def register(self, process_id: str, pid: int, command: str, working_dir: str = "") -> ManagedProcess:
        proc = ManagedProcess(process_id, pid, command, working_dir)
        self._processes[process_id] = proc
        return proc

    def get(self, process_id: str) -> ManagedProcess | None:
        return self._processes.get(process_id)

    def terminate(self, process_id: str) -> bool:
        proc = self._processes.get(process_id)
        if not proc:
            return False
        try:
            os.kill(proc.pid, signal.SIGTERM)
            proc.status = "terminated"
            proc.finished_at = time.time()
            proc.exit_code = -1
            return True
        except ProcessLookupError:
            proc.status = "terminated"
            proc.finished_at = time.time()
            proc.exit_code = -1
            return True
        except Exception as exc:
            logger.error("Failed to terminate process %s: %s", process_id, exc)
            return False

    def cleanup(self) -> None:
        for pid in list(self._processes.keys()):
            proc = self._processes[pid]
            if proc.status in ("terminated", "finished"):
                del self._processes[pid]
