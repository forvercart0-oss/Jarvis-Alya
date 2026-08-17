"""Debugger for JARVIS Phase 27."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("jarvis.coding.debugger")


class Debugger:
    def parse_traceback(self, text: str) -> dict[str, Any]:
        lines = text.splitlines()
        errors = []
        current_error: dict[str, Any] = {}
        for line in lines:
            if "Traceback" in line or "Error:" in line or "Exception:" in line:
                if current_error:
                    errors.append(current_error)
                current_error = {"type": line.strip(), "frames": []}
            elif "File " in line and ", line " in line:
                if not current_error:
                    current_error = {"type": "Unknown", "frames": []}
                match = re.search(r'File "([^"]+)", line (\d+)', line)
                if match:
                    current_error["frames"].append({"file": match.group(1), "line": int(match.group(2)), "code": line.strip()})
            elif line.strip().startswith("raise ") or line.strip().startswith("return "):
                if current_error:
                    current_error["message"] = line.strip()
        if current_error:
            errors.append(current_error)
        return {"success": True, "errors": errors, "count": len(errors)}

    def analyze_test_failure(self, output: str) -> dict[str, Any]:
        return self.parse_traceback(output)

    def analyze_build_error(self, output: str) -> dict[str, Any]:
        return self.parse_traceback(output)

    def suggest_fix(self, error: dict[str, Any]) -> dict[str, Any]:
        suggestions = []
        error_type = error.get("type", "").lower()
        if "modulenotfounderror" in error_type or "importerror" in error_type:
            suggestions.append("Install missing dependency or fix import path")
        elif "filenotfounderror" in error_type:
            suggestions.append("Check file path and permissions")
        elif "permissionerror" in error_type:
            suggestions.append("Check file/directory permissions")
        elif "typeerror" in error_type:
            suggestions.append("Check argument types and function signatures")
        elif "valueerror" in error_type:
            suggestions.append("Validate input values and formats")
        elif "keyerror" in error_type:
            suggestions.append("Check dictionary key existence")
        elif "indexerror" in error_type:
            suggestions.append("Check array/list bounds")
        return {"success": True, "suggestions": suggestions, "error": error}


debugger = Debugger()
