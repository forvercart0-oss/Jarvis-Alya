"""DevOps Agent for JARVIS Phase 28."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from devops.build_manager import BuildManager
from devops.deployment_diff import deployment_audit_logger, deployment_diff, supply_chain_checker
from devops.deployment_planner import deployment_planner
from devops.deployment_strategy import deployment_strategy
from devops.health_checker import health_checker
from devops.incident_manager import incident_manager
from devops.infra_analyzer import infrastructure_analyzer
from devops.kubernetes import kubernetes_manager
from devops.reverse_proxy import reverse_proxy_manager

logger = logging.getLogger("jarvis.devops.agent")


class DevOpsAgent:
    def __init__(self, base_dir: Path, memory: Any | None = None):
        self._base_dir = base_dir
        self._memory = memory

    async def deploy(self, goal: str, project: str, environment: str = "local") -> dict[str, Any]:
        from devops.models import DeploymentStatus, DeploymentTask
        task = DeploymentTask(goal=goal, project=project, environment=environment)
        try:
            project_path = self._base_dir / project
            if not project_path.exists():
                return {"success": False, "error": f"Project not found: {project}", "task": task.to_dict()}

            task.status = DeploymentStatus.PLANNING
            plan = deployment_planner.create_plan(project, environment, None)
            checkpoint = deployment_strategy.create_checkpoint(task.task_id, project, environment)

            task.status = DeploymentStatus.BUILDING
            build = BuildManager(self._base_dir)
            build_result = await build.build(project)

            if self._memory:
                try:
                    errors = self._memory.find_error_resolution("build", limit=5)
                    if errors:
                        task.metadata = task.metadata or {}
                        task.metadata["known_errors"] = [e.get("resolution", "") for e in errors[:3]]
                except Exception:
                    pass

            task.status = DeploymentStatus.VERIFYING
            health = await health_checker.check_http("http://localhost:8000/health")

            deployment_audit_logger.log(
                action="deploy",
                environment=environment,
                version=task.version,
                commit=task.commit,
                status="completed" if health.get("success") else "failed",
            )

            task.status = DeploymentStatus.COMPLETED
            return {
                "success": health.get("success", False),
                "task": task.to_dict(),
                "plan": plan.to_dict(),
                "build": build_result,
                "health": health,
                "checkpoint": checkpoint.to_dict(),
            }
        except Exception as exc:
            task.status = DeploymentStatus.FAILED
            task.error = str(exc)
            if self._memory:
                try:
                    self._memory.record_error(
                        error_signature=str(exc)[:200],
                        resolution="Check logs for details",
                        category="deployment",
                        project=project,
                    )
                except Exception:
                    pass
            return {"success": False, "error": str(exc), "task": task.to_dict()}

    async def rollback(self, task_id: str) -> dict[str, Any]:
        from devops.models import DeploymentStatus, DeploymentTask
        task = DeploymentTask(task_id=task_id)
        checkpoint = deployment_strategy.create_checkpoint(task_id, "", "local")
        plan = deployment_strategy.plan_rollback(checkpoint)
        task.status = DeploymentStatus.ROLLED_BACK
        deployment_audit_logger.log(
            action="rollback",
            environment="local",
            version=checkpoint.version,
            commit=checkpoint.commit,
            status="completed",
        )
        return {"success": True, "task": task.to_dict(), "plan": plan}

    async def diagnose(self, service: str) -> dict[str, Any]:
        incident = incident_manager.create_incident(service, f"Diagnosing {service}")
        return {"success": True, "incident": incident.to_dict()}

    def get_project_deployment_info(self, project: str) -> dict[str, Any]:
        project_path = self._base_dir / project
        if not project_path.exists():
            return {"success": False, "error": f"Project not found: {project}"}
        try:
            infra = infrastructure_analyzer.analyze_project(str(project_path))
            infra["reverse_proxy"] = reverse_proxy_manager.detect()
            infra["kubernetes"] = kubernetes_manager.available
            return infra
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def get_deployment_diff(self, old_version: str, new_version: str, project: str) -> dict[str, Any]:
        project_path = self._base_dir / project
        if not project_path.exists():
            return {"success": False, "error": f"Project not found: {project}"}
        return deployment_diff.compute(old_version, new_version, str(project_path))

    def get_supply_chain_report(self, project: str) -> dict[str, Any]:
        project_path = self._base_dir / project
        if not project_path.exists():
            return {"success": False, "error": f"Project not found: {project}"}
        return supply_chain_checker.check_dependencies(str(project_path))

    def get_audit_logs(self, limit: int = 50) -> list[dict[str, Any]]:
        return deployment_audit_logger.get_logs(limit)


devops_agent = DevOpsAgent
