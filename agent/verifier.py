"""Verification engine for JARVIS Phase 15."""

from __future__ import annotations

import logging
from typing import Any

from agent.models import ConfidenceLevel

logger = logging.getLogger("jarvis.agent.verifier")


class VerificationEngine:
    VERIFICATION_RULES: dict[str, dict[str, Any]] = {
        "filesystem_read": {"success_path": "success", "expected_true": True, "require_content": True},
        "filesystem_write": {"success_path": "success", "expected_true": True, "post_check": "file_exists"},
        "filesystem_delete": {"success_path": "success", "expected_true": True, "post_check": "file_not_exists"},
        "terminal": {"success_path": "success", "expected_true": True},
        "open_browser": {"success_path": "success", "expected_true": True},
        "browser_navigate": {"success_path": "success", "expected_true": True},
        "web_search": {"success_path": "success", "expected_true": True, "require_results": True},
        "run_project_command": {"success_path": "success", "expected_true": True},
        "create_project": {"success_path": "success", "expected_true": True},
        "system_info": {"success_path": "success", "expected_true": True},
        "vision_capture_screen": {"success_path": "success", "expected_true": True},
        "vision_analyze_screen": {"success_path": "success", "expected_true": True, "require_description": True},
        "vision_find_target": {"success_path": "found", "expected_true": True},
        "vision_ocr": {"success_path": "success", "expected_true": True, "require_text": True},
        "computer_mouse_click": {"success_path": "success", "expected_true": True},
        "computer_keyboard_type": {"success_path": "success", "expected_true": True},
        "browser_click": {"success_path": "success", "expected_true": True},
        "browser_type": {"success_path": "success", "expected_true": True},
        "form_submit": {"success_path": "success", "expected_true": True},
        "send_message": {"success_path": "success", "expected_true": True},
        "download_file": {"success_path": "success", "expected_true": True, "post_check": "file_exists"},
    }

    def verify(self, tool_name: str, result: Any, observation: str = "") -> tuple[bool, ConfidenceLevel, str]:
        if result is None:
            return False, ConfidenceLevel.LOW, f"No result returned from {tool_name}."

        data = self._extract_data(result)
        rule = self.VERIFICATION_RULES.get(tool_name, {"success_path": "success", "expected_true": True})

        success_path = rule.get("success_path", "success")
        expected = rule.get("expected_true", True)

        actual_success = data.get(success_path)
        if expected and not actual_success:
            error = data.get("error") or data.get("stderr") or "Unknown error"
            return False, ConfidenceLevel.HIGH, f"{tool_name} failed: {error}"

        if rule.get("require_content") and not data.get("content"):
            return False, ConfidenceLevel.MEDIUM, f"{tool_name} returned no content."
        if rule.get("require_text") and not data.get("text"):
            return False, ConfidenceLevel.MEDIUM, f"{tool_name} returned no text."
        if rule.get("require_description") and not data.get("description"):
            return False, ConfidenceLevel.MEDIUM, f"{tool_name} returned no description."
        if rule.get("require_results") and not data.get("results") and not data.get("data"):
            return False, ConfidenceLevel.MEDIUM, f"{tool_name} returned no results."

        post_check = rule.get("post_check")
        if post_check:
            ok, msg = self._post_check(tool_name, data, post_check)
            if not ok:
                return False, ConfidenceLevel.MEDIUM, msg

        confidence = ConfidenceLevel.HIGH
        if observation:
            if any(k in observation.lower() for k in ["error", "failed", "timeout", "not found"]):
                confidence = ConfidenceLevel.LOW
            elif any(k in observation.lower() for k in ["warning", "retry", "uncertain"]):
                confidence = ConfidenceLevel.MEDIUM

        return True, confidence, f"{tool_name} verified successfully."

    def _extract_data(self, result: Any) -> dict[str, Any]:
        if hasattr(result, "_data"):
            return result._data
        if hasattr(result, "__dict__"):
            return {k: v for k, v in result.__dict__.items() if not k.startswith("_")}
        if isinstance(result, dict):
            return result
        return {"success": bool(result)}

    def _post_check(self, tool_name: str, data: dict[str, Any], check: str) -> tuple[bool, str]:
        if check == "file_exists":
            path = data.get("path") or data.get("file")
            if not path:
                return True, "Write verified (no path to check)."
            import os
            if os.path.exists(path):
                return True, f"File {path} exists after write."
            return False, f"File {path} was not created."
        if check == "file_not_exists":
            path = data.get("path") or data.get("file")
            if not path:
                return True, "Deletion verified (no path to check)."
            import os
            if not os.path.exists(path):
                return True, f"File {path} was deleted."
            return False, f"File {path} still exists after deletion."
        return True, f"{tool_name} passed post-check ({check})."


verification_engine = VerificationEngine()
