"""Action verifier: verify that actions completed successfully."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.automation.verifier")


class ActionVerifier:
    """Verify that tool actions produced the expected results."""

    VERIFICATION_RULES: dict[str, dict[str, Any]] = {
        "read_file": {
            "success_path": "success",
            "expected_true": True,
            "missing_result_msg": "File content not returned.",
        },
        "write_file": {
            "success_path": "success",
            "expected_true": True,
            "post_check": "file_exists",
        },
        "delete_file": {
            "success_path": "success",
            "expected_true": True,
            "post_check": "file_not_exists",
        },
        "terminal": {
            "success_path": "success",
            "expected_true": True,
        },
        "open_browser": {
            "success_path": "success",
            "expected_true": True,
        },
        "browser_navigate": {
            "success_path": "success",
            "expected_true": True,
        },
        "web_search": {
            "success_path": "success",
            "expected_true": True,
        },
        "run_project_command": {
            "success_path": "success",
            "expected_true": True,
        },
        "create_project": {
            "success_path": "success",
            "expected_true": True,
        },
        "system_info": {
            "success_path": "success",
            "expected_true": True,
        },
    }

    def verify(self, tool_name: str, result: Any) -> tuple[bool, str]:
        """Verify a tool result.

        Returns (is_verified, message).
        """
        if result is None:
            return False, f"No result returned from {tool_name}."

        data = self._extract_data(result)
        rule = self.VERIFICATION_RULES.get(tool_name, {"success_path": "success", "expected_true": True})

        success_path = rule.get("success_path", "success")
        expected = rule.get("expected_true", True)

        actual_success = data.get(success_path)
        if expected and not actual_success:
            error = data.get("error") or data.get("stderr") or "Unknown error"
            return False, f"{tool_name} failed: {error}"

        post_check = rule.get("post_check")
        if post_check:
            return self._post_check(tool_name, data, post_check)

        return True, f"{tool_name} verified successfully."

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
