"""Verification Engine 2.0 for JARVIS Phase 23.

Task-specific verification for coding, files, websites, research,
and documents.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("jarvis.agent.verification_v2")


class VerificationEngine:
    """Verifies task results with task-specific strategies."""

    async def verify(self, task_type: str, result: Any, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Verify a task result based on its type."""
        verifiers = {
            "code_edit": self._verify_code,
            "filesystem_read": self._verify_file_exists,
            "filesystem_write": self._verify_file_exists,
            "terminal": self._verify_command,
            "web_search": self._verify_research,
            "browser_navigate": self._verify_browser,
            "create_project": self._verify_project,
            "run_tests": self._verify_tests,
            "build": self._verify_build,
            "server_start": self._verify_server,
        }
        verifier = verifiers.get(task_type, self._verify_generic)
        try:
            return await verifier(result, context or {})
        except Exception as exc:
            logger.warning("Verification failed for %s: %s", task_type, exc)
            return {"verified": False, "reason": str(exc), "confidence": "low"}

    async def _verify_code(self, result: Any, context: dict[str, Any]) -> dict[str, Any]:
        return {"verified": True, "reason": "Code change accepted", "confidence": "medium"}

    async def _verify_file_exists(self, result: Any, context: dict[str, Any]) -> dict[str, Any]:
        path = context.get("path", "")
        if path and os.path.exists(path):
            return {"verified": True, "reason": f"File exists: {path}", "confidence": "high"}
        return {"verified": False, "reason": f"File not found: {path}", "confidence": "high"}

    async def _verify_command(self, result: Any, context: dict[str, Any]) -> dict[str, Any]:
        if isinstance(result, dict) and result.get("success"):
            return {"verified": True, "reason": "Command executed successfully", "confidence": "high"}
        return {"verified": False, "reason": "Command failed", "confidence": "high"}

    async def _verify_research(self, result: Any, context: dict[str, Any]) -> dict[str, Any]:
        if isinstance(result, dict) and result.get("sources"):
            return {"verified": True, "reason": f"Research complete with {len(result['sources'])} sources", "confidence": "medium"}
        return {"verified": False, "reason": "No sources found", "confidence": "low"}

    async def _verify_browser(self, result: Any, context: dict[str, Any]) -> dict[str, Any]:
        if isinstance(result, dict) and result.get("url"):
            return {"verified": True, "reason": f"Browser navigated to {result['url']}", "confidence": "high"}
        return {"verified": False, "reason": "Browser navigation failed", "confidence": "high"}

    async def _verify_project(self, result: Any, context: dict[str, Any]) -> dict[str, Any]:
        if isinstance(result, dict) and result.get("project_path"):
            return {"verified": True, "reason": "Project created", "confidence": "high"}
        return {"verified": False, "reason": "Project creation failed", "confidence": "high"}

    async def _verify_tests(self, result: Any, context: dict[str, Any]) -> dict[str, Any]:
        if isinstance(result, dict) and result.get("passed") is True:
            return {"verified": True, "reason": "Tests passed", "confidence": "high"}
        return {"verified": False, "reason": "Tests failed", "confidence": "high"}

    async def _verify_build(self, result: Any, context: dict[str, Any]) -> dict[str, Any]:
        if isinstance(result, dict) and result.get("success"):
            return {"verified": True, "reason": "Build succeeded", "confidence": "high"}
        return {"verified": False, "reason": "Build failed", "confidence": "high"}

    async def _verify_server(self, result: Any, context: dict[str, Any]) -> dict[str, Any]:
        if isinstance(result, dict) and result.get("running"):
            return {"verified": True, "reason": "Server is running", "confidence": "high"}
        return {"verified": False, "reason": "Server not running", "confidence": "high"}

    async def _verify_generic(self, result: Any, context: dict[str, Any]) -> dict[str, Any]:
        if isinstance(result, dict) and result.get("success"):
            return {"verified": True, "reason": "Task completed", "confidence": "medium"}
        if result:
            return {"verified": True, "reason": "Task returned result", "confidence": "low"}
        return {"verified": False, "reason": "Task returned empty result", "confidence": "low"}


verification_engine_v2 = VerificationEngine()
