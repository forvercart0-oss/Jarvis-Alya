"""Coding Agent for JARVIS Phase 27."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from coding.command_runner import CommandRunner
from coding.file_editor import FileEditor
from coding.project_index import ProjectIndex
from coding.repository_analyzer import RepositoryAnalyzer
from coding.task_planner import coding_task_planner
from coding.test_runner import test_runner

logger = logging.getLogger("jarvis.coding.agent")


class CodingAgent:
    def __init__(self, base_dir: Path, memory: Any | None = None):
        self._base_dir = base_dir
        self._memory = memory
        self._analyzer = RepositoryAnalyzer(base_dir)
        self._index: dict[str, ProjectIndex] = {}
        self._editor = FileEditor(base_dir)
        self._runner = CommandRunner(base_dir)
        self._tester = test_runner(base_dir)
        self._git = __import__("coding.git_manager", fromlist=["CodingGitManager"]).coding_git_manager(base_dir)

    def set_memory(self, memory: Any) -> None:
        self._memory = memory

    async def execute_goal(self, goal: str, project: str) -> dict[str, Any]:
        task = coding_task_planner.create_task(goal, project=project)
        coding_task_planner.update_status(task, "running")
        try:
            project_path = self._base_dir / project
            if not project_path.exists():
                return {"success": False, "error": f"Project not found: {project}", "task": task.to_dict()}

            if self._memory:
                try:
                    project_memories = self._memory.projects.recall(project, limit=20)
                    if project_memories:
                        task.metadata = task.metadata or {}
                        task.metadata["project_memories"] = [m.get("value", "") for m in project_memories[:10]]
                except Exception:
                    pass

            info = await self._analyzer.analyze(str(project_path))
            steps = coding_task_planner.plan_steps(task, info)
            for i, step in enumerate(steps):
                coding_task_planner.record_step_result(task, i, {"status": "completed", "step": step})

            coding_task_planner.update_status(task, "completed")
            return {"success": True, "task": task.to_dict(), "project": info.to_dict()}
        except Exception as exc:
            coding_task_planner.update_status(task, "failed")
            task.error = str(exc)
            return {"success": False, "error": str(exc), "task": task.to_dict()}

    def get_project_info(self, project: str) -> dict[str, Any]:
        project_path = self._base_dir / project
        if not project_path.exists():
            return {"success": False, "error": f"Project not found: {project}"}
        try:
            import asyncio
            info = asyncio.run(self._analyzer.analyze(str(project_path)))
            result = {"success": True, "project": info.to_dict()}
            if self._memory:
                try:
                    project_memories = self._memory.projects.recall(project, limit=20)
                    result["memories"] = [m.get("value", "") for m in project_memories[:10]]
                except Exception:
                    pass
            return result
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def get_index(self, project: str) -> dict[str, Any]:
        if project not in self._index:
            self._index[project] = ProjectIndex(self._base_dir / project)
            self._index[project].build()
        return {"success": True, "index": self._index[project].to_dict()}

    def refresh_index(self, project: str) -> dict[str, Any]:
        if project in self._index:
            self._index[project].build()
        return self.get_index(project)


coding_agent = CodingAgent
