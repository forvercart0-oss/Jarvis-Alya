"""Tests for Phase 28 DevOps & Infrastructure 2.0."""

from __future__ import annotations

from devops.database import database_manager
from devops.deployment_diff import deployment_audit_logger, supply_chain_checker
from devops.deployment_planner import deployment_planner
from devops.deployment_strategy import deployment_strategy
from devops.env_detector import environment_detector
from devops.iac import ansible_manager, terraform_manager
from devops.incident_manager import IncidentManager
from devops.infra_analyzer import infrastructure_analyzer
from devops.kubernetes import kubernetes_manager
from devops.models import (
    ContainerInfo,
    ContainerStatus,
    DeploymentCheckpoint,
    DeploymentStatus,
    DeploymentTask,
    HealthCheck,
    IncidentStatus,
    ServerInfo,
)
from devops.monitoring import MonitoringManager
from devops.remote_manager import RemoteServerManager
from devops.reverse_proxy import reverse_proxy_manager


def test_deployment_task_defaults():
    task = DeploymentTask()
    assert task.status == DeploymentStatus.PENDING
    assert task.task_id != ""

def test_deployment_plan():
    plan = deployment_planner.create_plan("test", "local", None)
    assert plan.project == "test"
    assert plan.environment == "local"
    assert len(plan.steps) > 0

def test_deployment_plan_production():
    plan = deployment_planner.create_plan("test", "production", None)
    assert any(s["type"] == "migrate" for s in plan.steps)

def test_deployment_checkpoint_defaults():
    cp = DeploymentCheckpoint(task_id="t1", project="test")
    assert cp.project == "test"
    assert cp.checkpoint_id != ""

def test_container_info_defaults():
    info = ContainerInfo(name="web", image="nginx")
    assert info.name == "web"
    assert info.status == ContainerStatus.PENDING

def test_server_info_defaults():
    info = ServerInfo(name="prod", host="1.2.3.4")
    assert info.name == "prod"
    assert info.port == 22

def test_health_check_defaults():
    check = HealthCheck(name="web", type="http", target="http://localhost:8000")
    assert check.type == "http"
    assert check.expected_status == 200

def test_incident_manager():
    manager = IncidentManager()
    incident = manager.create_incident("backend", "Service down", "critical")
    assert incident.service == "backend"
    assert incident.status == IncidentStatus.DETECTED
    manager.update_status(incident.incident_id, IncidentStatus.INVESTIGATING)
    assert manager.get(incident.incident_id).status == IncidentStatus.INVESTIGATING
    manager.resolve(incident.incident_id, "OOM")
    assert manager.get(incident.incident_id).status == IncidentStatus.RESOLVED

def test_incident_actions():
    manager = IncidentManager()
    incident = manager.create_incident("api", "High latency")
    manager.add_action(incident.incident_id, "Restarted service")
    assert manager.get(incident.incident_id).actions == ["Restarted service"]

def test_monitoring_manager():
    mm = MonitoringManager()
    result = mm.check_cpu(90)
    assert result["alert"] is True
    result2 = mm.check_cpu(50)
    assert result2["alert"] is False
    mm.add_alert({"metric": "cpu", "usage": 95})
    assert len(mm.get_alerts()) == 1

def test_remote_server_manager():
    mgr = RemoteServerManager()
    mgr.register_server("prod", "1.2.3.4", username="ubuntu")
    servers = mgr.list_servers()
    assert len(servers) == 1
    assert servers[0]["name"] == "prod"

def test_environment_detector():
    env = environment_detector.detect()
    assert "os" in env
    assert "tools" in env
    assert "docker_available" in env

def test_infra_analyzer_local():
    info = infrastructure_analyzer.analyze_local()
    assert info.name == "local"
    assert info.host == "localhost"

def test_infra_analyzer_project():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        result = infrastructure_analyzer.analyze_project(tmpdir)
        assert result["success"] is True
        assert "project" in result

def test_deployment_planner_dry_run():
    plan = deployment_planner.create_plan("test", "staging", None)
    dry_run = deployment_planner.create_dry_run(plan)
    assert dry_run["dry_run"] is True
    assert dry_run["environment"] == "staging"

def test_incident_list_active():
    manager = IncidentManager()
    manager.create_incident("svc1", "Down")
    manager.create_incident("svc2", "Slow")
    active = manager.list_active()
    assert len(active) == 2

def test_monitoring_thresholds():
    mm = MonitoringManager()
    mm.set_threshold("cpu", 90)
    result = mm.check_cpu(85)
    assert result["alert"] is False
    result2 = mm.check_cpu(95)
    assert result2["alert"] is True

def test_container_status_parse():
    from devops.container_manager import ContainerManager
    cm = ContainerManager()
    assert cm._parse_status("Up 2 hours") == ContainerStatus.RUNNING
    assert cm._parse_status("Restarting") == ContainerStatus.RESTARTING
    assert cm._parse_status("Exited") == ContainerStatus.STOPPED

def test_deployment_strategy_rollback():
    checkpoint = deployment_strategy.create_checkpoint("t1", "proj", "local", "v1.0", "abc123", "img:1.0")
    plan = deployment_strategy.plan_rollback(checkpoint)
    assert plan["type"] == "rollback"
    assert len(plan["steps"]) == 3

def test_deployment_strategy_blue_green():
    plan = deployment_strategy.plan_blue_green("proj", "v2.0")
    assert plan["type"] == "blue_green"
    assert len(plan["steps"]) == 4

def test_deployment_strategy_canary():
    plan = deployment_strategy.plan_canary("proj", "v2.0", 10)
    assert plan["type"] == "canary"
    assert plan["traffic_percent"] == 10

def test_reverse_proxy_manager():
    proxy = reverse_proxy_manager.detect()
    assert proxy in ("nginx", "caddy", "traefik", "none")

def test_reverse_proxy_nginx():
    services = [{"name": "web", "host": "localhost", "port": 8000, "domain": "app.local"}]
    config = reverse_proxy_manager.generate_nginx_config(services)
    assert "upstream web" in config
    assert "proxy_pass" in config

def test_database_migration_detection():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        result = database_manager.detect_migrations(tmpdir)
        assert result["success"] is True
        assert "tools" in result

def test_supply_chain_checker():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        result = supply_chain_checker.check_dependencies(tmpdir)
        assert result["success"] is True
        assert "issues" in result

def test_deployment_audit_logger():
    deployment_audit_logger.log("deploy", "staging", "v1.0", "abc123", "completed")
    logs = deployment_audit_logger.get_logs()
    assert len(logs) == 1
    assert logs[0]["action"] == "deploy"

def test_kubernetes_available():
    assert hasattr(kubernetes_manager, "available")

def test_terraform_available():
    assert hasattr(terraform_manager, "available")

def test_ansible_available():
    assert hasattr(ansible_manager, "available")
