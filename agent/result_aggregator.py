"""Result aggregator for JARVIS Phase 20."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.agent.result_aggregator")


class ResultAggregator:
    def aggregate(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        if not results:
            return {"success": False, "error": "No results to aggregate"}
        success_count = sum(1 for r in results if r.get("success"))
        total = len(results)
        combined_output = []
        errors = []
        for r in results:
            if r.get("success"):
                output = r.get("output") or r.get("result") or r.get("data")
                if output:
                    combined_output.append(output)
            else:
                errors.append(r.get("error", "Unknown error"))
        confidence = success_count / total if total > 0 else 0.0
        return {
            "success": success_count == total,
            "partial_success": 0 < success_count < total,
            "success_count": success_count,
            "total_count": total,
            "confidence": confidence,
            "output": combined_output,
            "errors": errors,
            "summary": f"{success_count}/{total} agents succeeded",
        }

    def merge(self, primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
        merged = dict(primary)
        if secondary.get("success") and not merged.get("success"):
            merged["success"] = True
        if secondary.get("output"):
            existing = merged.get("output")
            if existing:
                if isinstance(existing, list) and isinstance(secondary["output"], list):
                    merged["output"] = existing + secondary["output"]
                elif isinstance(existing, dict) and isinstance(secondary["output"], dict):
                    merged.setdefault("output", {}).update(secondary["output"])
            else:
                merged["output"] = secondary["output"]
        if secondary.get("errors"):
            merged.setdefault("errors", []).extend(secondary["errors"] if isinstance(secondary["errors"], list) else [secondary["errors"]])
        return merged


result_aggregator = ResultAggregator()
