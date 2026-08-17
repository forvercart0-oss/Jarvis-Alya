"""DevOps Phase 28 API routes for JARVIS."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.ws_manager import ws_manager
from devops.agent import DevOpsAgent
from devops.cicd import cicd_manager
from devops.cloud import cloud_manager
from devops.container_manager import container_manager
from devops.database import database_manager
from devops.health_checker import health_checker
from devops.iac import ansible_manager, terraform_manager
from devops.incident_manager import incident_manager
from devops.infra_analyzer import infrastructure_analyzer
from devops.kubernetes import kubernetes_manager
from devops.monitoring import monitoring_manager
from devops.remote_manager import remote_server_manager
from devops.reverse_proxy import reverse_proxy_manager

logger = logging.getLogger("jarvis.api.devops")

router = APIRouter(prefix="/devops", tags=["devops"])

_base_dir = Path(__import__("config.settings", fromlist=["get_settings"]).get_settings().data_dir) / "projects"
_devops_agent = DevOpsAgent(_base_dir)


def _inject_memory():
    try:
        from backend.main import memory_manager
        _devops_agent._memory = memory_manager
    except Exception:
        pass


class DeployRequest(BaseModel):
    goal: str
    project: str
    environment: str = "local"


class ServerRegisterRequest(BaseModel):
    name: str
    host: str
    port: int = 22
    username: str = ""
    os: str = ""


@router.get("/status")
async def devops_status() -> dict[str, Any]:
    return {
        "docker_available": container_manager.available,
        "servers": remote_server_manager.list_servers(),
        "alerts": monitoring_manager.get_alerts(10),
    }


@router.post("/deploy")
async def devops_deploy(request: DeployRequest):
    _inject_memory()
    await ws_manager.broadcast("devops_deployment_started", {
        "goal": request.goal,
        "project": request.project,
        "environment": request.environment,
    })
    result = await _devops_agent.deploy(request.goal, request.project, request.environment)
    await ws_manager.broadcast("devops_deployment_completed", {
        "goal": request.goal,
        "success": result.get("success"),
    })
    return result


@router.get("/projects/{name}/deployment-info")
async def devops_project_info(name: str):
    _inject_memory()
    result = _devops_agent.get_project_deployment_info(name)
    return result


@router.get("/containers")
async def devops_containers() -> dict[str, Any]:
    if not container_manager.available:
        return {"success": False, "error": "Docker not available"}
    containers = container_manager.list_containers()
    return {"success": True, "containers": [c.to_dict() for c in containers]}


@router.post("/containers/build")
async def devops_build_container(request: dict) -> dict[str, Any]:
    result = container_manager.build_image(request.get("project_path", ""), request.get("tag", "latest"))
    return result


@router.post("/containers/start")
async def devops_start_container(request: dict) -> dict[str, Any]:
    result = container_manager.start_service(request.get("service", ""))
    return result


@router.post("/containers/stop")
async def devops_stop_container(request: dict) -> dict[str, Any]:
    result = container_manager.stop_service(request.get("service", ""))
    return result


@router.get("/containers/logs")
async def devops_container_logs(service: str, tail: int = 100) -> dict[str, Any]:
    result = container_manager.get_logs(service, tail=tail)
    return result


@router.post("/health/check")
async def devops_health_check(request: dict) -> dict[str, Any]:
    check_type = request.get("type", "http")
    target = request.get("target", "")
    if check_type == "http":
        return await health_checker.check_http(target, request.get("expected_status", 200), request.get("timeout", 10))
    if check_type == "tcp":
        return await health_checker.check_tcp(target, request.get("timeout", 10))
    return {"success": False, "error": f"Unknown check type: {check_type}"}


@router.post("/incidents")
async def devops_create_incident(request: dict) -> dict[str, Any]:
    incident = incident_manager.create_incident(
        request.get("service", ""),
        request.get("description", ""),
        request.get("severity", "high"),
    )
    return {"success": True, "incident": incident.to_dict()}


@router.get("/incidents")
async def devops_list_incidents() -> dict[str, Any]:
    return {"success": True, "incidents": incident_manager.list_active()}


@router.post("/incidents/{incident_id}/resolve")
async def devops_resolve_incident(incident_id: str, request: dict) -> dict[str, Any]:
    incident = incident_manager.resolve(incident_id, request.get("cause", ""))
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"success": True, "incident": incident.to_dict()}


@router.post("/servers")
async def devops_register_server(request: ServerRegisterRequest) -> dict[str, Any]:
    result = remote_server_manager.register_server(
        request.name, request.host, request.port, request.username, os=request.os
    )
    return result


@router.get("/servers")
async def devops_list_servers() -> dict[str, Any]:
    return {"success": True, "servers": remote_server_manager.list_servers()}


@router.post("/servers/{name}/health")
async def devops_server_health(name: str) -> dict[str, Any]:
    return await remote_server_manager.health_check(name)


@router.post("/servers/{name}/execute")
async def devops_server_execute(name: str, request: dict) -> dict[str, Any]:
    return await remote_server_manager.execute(name, request.get("command", ""))


@router.get("/servers/{name}/logs")
async def devops_server_logs(name: str, service: str = "", tail: int = 100) -> dict[str, Any]:
    return await remote_server_manager.get_logs(name, service, tail=tail)


@router.get("/environment")
async def devops_environment() -> dict[str, Any]:
    return infrastructure_analyzer.analyze_local()


@router.get("/cicd/detect")
async def devops_cicd_detect(project: str) -> dict[str, Any]:
    project_path = str(_base_dir / project) if project else str(_base_dir)
    system = cicd_manager.detect_system(project_path)
    return {"success": True, "system": system}


@router.post("/cicd/generate")
async def devops_cicd_generate(request: dict) -> dict[str, Any]:
    project = request.get("project", {})
    system = request.get("system", "github_actions")
    if system == "github_actions":
        return {"success": True, "workflow": cicd_manager.generate_github_workflow(project)}
    return {"success": True, "workflow": cicd_manager.generate_gitlab_ci(project)}


@router.get("/monitoring/alerts")
async def devops_alerts(limit: int = 20) -> dict[str, Any]:
    return {"success": True, "alerts": monitoring_manager.get_alerts(limit)}


@router.post("/rollback")
async def devops_rollback(request: dict) -> dict[str, Any]:
    result = await _devops_agent.rollback(request.get("task_id", ""))
    return result


@router.get("/reverse-proxy/detect")
async def devops_reverse_proxy_detect() -> dict[str, Any]:
    return {"success": True, "proxy": reverse_proxy_manager.detect()}


@router.post("/reverse-proxy/generate")
async def devops_reverse_proxy_generate(request: dict) -> dict[str, Any]:
    proxy = request.get("proxy", "nginx")
    services = request.get("services", [])
    if proxy == "nginx":
        return {"success": True, "config": reverse_proxy_manager.generate_nginx_config(services)}
    if proxy == "caddy":
        return {"success": True, "config": reverse_proxy_manager.generate_caddyfile(services)}
    return {"success": False, "error": f"Unsupported proxy: {proxy}"}


@router.get("/projects/{name}/migrations")
async def devops_migrations(name: str) -> dict[str, Any]:
    project_path = str(_base_dir / name) if name else str(_base_dir)
    return database_manager.detect_migrations(project_path)


@router.post("/projects/{name}/migrations/run")
async def devops_run_migrations(name: str, request: dict) -> dict[str, Any]:
    project_path = str(_base_dir / name) if name else str(_base_dir)
    tool = request.get("tool", "alembic")
    return database_manager.run_migrations(tool, project_path, request.get("environment", "development"))


@router.get("/projects/{name}/backup/check")
async def devops_backup_check(name: str) -> dict[str, Any]:
    project_path = str(_base_dir / name) if name else str(_base_dir)
    return database_manager.check_backup_capability(project_path)


@router.get("/projects/{name}/diff")
async def devops_project_diff(name: str, old_version: str = "", new_version: str = "") -> dict[str, Any]:
    return _devops_agent.get_deployment_diff(old_version, new_version, name)


@router.get("/projects/{name}/supply-chain")
async def devops_supply_chain(name: str) -> dict[str, Any]:
    return _devops_agent.get_supply_chain_report(name)


@router.get("/audit/logs")
async def devops_audit_logs(limit: int = 50) -> dict[str, Any]:
    return {"success": True, "logs": _devops_agent.get_audit_logs(limit)}


@router.get("/kubernetes/pods")
async def devops_k8s_pods(namespace: str = "default") -> dict[str, Any]:
    return kubernetes_manager.get_pods(namespace)


@router.get("/kubernetes/services")
async def devops_k8s_services(namespace: str = "default") -> dict[str, Any]:
    return kubernetes_manager.get_services(namespace)


@router.get("/kubernetes/logs")
async def devops_k8s_logs(pod: str, namespace: str = "default", tail: int = 100) -> dict[str, Any]:
    return kubernetes_manager.get_logs(pod, namespace, tail=tail)


@router.get("/terraform/validate")
async def devops_terraform_validate(project: str) -> dict[str, Any]:
    project_path = str(_base_dir / project) if project else str(_base_dir)
    return terraform_manager.validate(project_path)


@router.get("/terraform/plan")
async def devops_terraform_plan(project: str) -> dict[str, Any]:
    project_path = str(_base_dir / project) if project else str(_base_dir)
    return terraform_manager.plan(project_path)


@router.get("/ansible/validate")
async def devops_ansible_validate(path: str) -> dict[str, Any]:
    return ansible_manager.validate_playbook(path)


@router.get("/cloud/available")
async def devops_cloud_available() -> dict[str, Any]:
    return {"success": True, "providers": cloud_manager.detect_available()}
