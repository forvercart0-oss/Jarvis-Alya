"""Workflow condition evaluator for JARVIS Phase 11."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.workflows.conditions")


class ConditionEvaluator:
    """Evaluates workflow conditions."""

    def evaluate(self, condition: dict[str, Any], context: dict[str, Any]) -> bool:
        if not condition:
            return True
        operator = condition.get("operator", "and")
        conditions = condition.get("conditions", [])
        if not conditions:
            return True

        if operator == "and":
            return all(self._evaluate_single(c, context) for c in conditions)
        if operator == "or":
            return any(self._evaluate_single(c, context) for c in conditions)
        if operator == "not":
            return not self._evaluate_single(conditions[0], context)

        return False

    def _evaluate_single(self, condition: dict[str, Any], context: dict[str, Any]) -> bool:
        if "operator" in condition and "conditions" in condition:
            return self.evaluate(condition, context)

        field = condition.get("field", "")
        operator = condition.get("operator", "eq")
        value = condition.get("value")
        context_value = context.get(field)

        try:
            if operator == "eq":
                return context_value == value
            if operator == "ne":
                return context_value != value
            if operator == "gt":
                return float(context_value or 0) > float(value or 0)
            if operator == "lt":
                return float(context_value or 0) < float(value or 0)
            if operator == "gte":
                return float(context_value or 0) >= float(value or 0)
            if operator == "lte":
                return float(context_value or 0) <= float(value or 0)
            if operator == "contains":
                return str(value) in str(context_value or "")
            if operator == "not_contains":
                return str(value) not in str(context_value or "")
            if operator == "exists":
                return context_value is not None and str(context_value) != ""
            if operator == "not_exists":
                return context_value is None or str(context_value) == ""
            if operator == "is_true":
                return bool(context_value) is True
            if operator == "is_false":
                return bool(context_value) is False
        except Exception as exc:
            logger.debug("Condition evaluation failed: %s", exc)
            return False

        return False
