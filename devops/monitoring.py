"""Monitoring manager for JARVIS Phase 28."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.devops.monitoring")


class MonitoringManager:
    def __init__(self):
        self._alerts: list[dict[str, Any]] = []
        self._thresholds = {"cpu": 85, "memory": 85, "disk": 90}

    def set_threshold(self, metric: str, value: int) -> None:
        self._thresholds[metric] = value

    def check_cpu(self, usage: float) -> dict[str, Any]:
        threshold = self._thresholds.get("cpu", 85)
        alert = usage >= threshold
        return {"metric": "cpu", "usage": usage, "threshold": threshold, "alert": alert}

    def check_memory(self, usage: float) -> dict[str, Any]:
        threshold = self._thresholds.get("memory", 85)
        alert = usage >= threshold
        return {"metric": "memory", "usage": usage, "threshold": threshold, "alert": alert}

    def check_disk(self, usage: float) -> dict[str, Any]:
        threshold = self._thresholds.get("disk", 90)
        alert = usage >= threshold
        return {"metric": "disk", "usage": usage, "threshold": threshold, "alert": alert}

    def add_alert(self, alert: dict[str, Any]) -> None:
        self._alerts.append(alert)
        if len(self._alerts) > 100:
            self._alerts = self._alerts[-100:]

    def get_alerts(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._alerts[-limit:]


monitoring_manager = MonitoringManager()
