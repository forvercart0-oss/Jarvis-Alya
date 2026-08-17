"""Incident manager for JARVIS Phase 28."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from devops.models import Incident, IncidentStatus, Severity

logger = logging.getLogger("jarvis.devops.incident_manager")


class IncidentManager:
    def __init__(self):
        self._incidents: dict[str, Incident] = {}

    def create_incident(self, service: str, description: str, severity: str = Severity.HIGH) -> Incident:
        incident = Incident(service=service, description=description, severity=severity)
        incident.timeline.append({"event": "created", "timestamp": incident.created_at, "description": description})
        self._incidents[incident.incident_id] = incident
        return incident

    def update_status(self, incident_id: str, status: str) -> Incident | None:
        incident = self._incidents.get(incident_id)
        if incident:
            incident.status = status
            now = datetime.now(UTC).isoformat()
            incident.timeline.append({"event": "status_update", "timestamp": now, "status": status})
        return incident

    def add_action(self, incident_id: str, action: str) -> Incident | None:
        incident = self._incidents.get(incident_id)
        if incident:
            incident.actions.append(action)
            now = datetime.now(UTC).isoformat()
            incident.timeline.append({"event": "action", "timestamp": now, "action": action})
        return incident

    def resolve(self, incident_id: str, cause: str = "") -> Incident | None:
        incident = self._incidents.get(incident_id)
        if incident:
            incident.status = IncidentStatus.RESOLVED
            incident.cause = cause
            incident.resolved_at = datetime.now(UTC).isoformat()
            incident.timeline.append({"event": "resolved", "timestamp": incident.resolved_at, "cause": cause})
        return incident

    def get(self, incident_id: str) -> Incident | None:
        return self._incidents.get(incident_id)

    def list_active(self) -> list[dict[str, Any]]:
        active_statuses = {IncidentStatus.RESOLVED, IncidentStatus.FAILED}
        return [i.to_dict() for i in self._incidents.values() if i.status not in active_statuses]


incident_manager = IncidentManager()
