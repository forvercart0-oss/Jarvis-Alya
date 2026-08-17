"""Log analyzer for JARVIS Phase 27."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.coding.log_analyzer")


class LogAnalyzer:
    def analyze(self, log_text: str, source: str = "unknown") -> dict[str, Any]:
        lines = log_text.splitlines()
        errors = []
        warnings = []
        for line in lines:
            lower = line.lower()
            if any(k in lower for k in ["error", "exception", "traceback", "failed", "crash"]):
                errors.append(line.strip())
            elif any(k in lower for k in ["warn", "deprecated", "notice"]):
                warnings.append(line.strip())
        return {
            "success": True,
            "source": source,
            "total_lines": len(lines),
            "errors": errors[:20],
            "warnings": warnings[:20],
            "error_count": len(errors),
            "warning_count": len(warnings),
        }

    def correlate(self, frontend_log: str, backend_log: str) -> dict[str, Any]:
        frontend_analysis = self.analyze(frontend_log, "frontend")
        backend_analysis = self.analyze(backend_log, "backend")
        correlations = []
        for fe in frontend_analysis.get("errors", []):
            for be in backend_analysis.get("errors", []):
                if any(k in fe.lower() for k in ["connection", "websocket", "network"]) and any(k in be.lower() for k in ["connection", "websocket", "network"]):
                    correlations.append({"frontend": fe, "backend": be, "type": "network_correlation"})
        return {
            "success": True,
            "frontend": frontend_analysis,
            "backend": backend_analysis,
            "correlations": correlations,
        }


log_analyzer = LogAnalyzer()
