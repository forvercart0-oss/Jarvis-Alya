"""Tests for Phase 13 advanced task engine."""

from __future__ import annotations


from automation.task_state import TaskState, TaskPriority
from automation.router import AgentRouter, ToolRouter
from automation.command_executor import CommandExecutor, CommandResult
from automation.process_manager import ProcessManager
from automation.task_queue import TaskQueue
from automation.task_templates import TaskTemplateRegistry
from automation.audit import AuditLogger


def test_task_state_values():
    assert TaskState.PENDING == "pending"
    assert TaskState.PLANNING == "planning"
    assert TaskState.READY == "ready"
    assert TaskState.NEEDS_APPROVAL == "needs_approval"
    assert TaskState.BLOCKED == "blocked"


def test_task_priority_values():
    assert TaskPriority.LOW == "low"
    assert TaskPriority.NORMAL == "normal"
    assert TaskPriority.HIGH == "high"
    assert TaskPriority.URGENT == "urgent"


def test_agent_router_browser():
    router = AgentRouter()
    assert router.route("Search the web for Python tutorials") == "browser"


def test_agent_router_coding():
    router = AgentRouter()
    assert router.route("Write a Python API with FastAPI") == "coding"


def test_agent_router_research():
    router = AgentRouter()
    assert router.route("Research machine learning trends") == "research"


def test_agent_router_memory():
    router = AgentRouter()
    assert router.route("Remember my preference for dark theme") == "memory"


def test_tool_router_risk():
    router = ToolRouter()
    assert router.get_risk("read_file") == "low"
    assert router.get_risk("write_file") == "medium"
    assert router.get_risk("delete_file") == "high"
    assert router.get_risk("shutdown") == "critical"


def test_tool_router_approval():
    router = ToolRouter()
    assert router.requires_approval("delete_file") is True
    assert router.requires_approval("read_file") is False


def test_command_executor_dangerous():
    executor = CommandExecutor()
    dangerous, reason = executor.is_dangerous("rm -rf /")
    assert dangerous is True


def test_command_executor_safe():
    executor = CommandExecutor()
    dangerous, _ = executor.is_dangerous("ls -la")
    assert dangerous is False


def test_command_executor_redact_secrets():
    executor = CommandExecutor()
    text = "api_key=sk-1234567890abcdefghij"
    redacted = executor.redact_secrets(text)
    assert "sk-1234567890abcdefghij" not in redacted


def test_process_manager_lifecycle():
    mgr = ProcessManager()
    proc = mgr.register("proc1", 1234, "sleep 10")
    assert proc.status == "running"
    assert mgr.get("proc1") is not None
    mgr.terminate("proc1")
    assert proc.status == "terminated"


def test_task_queue_priority():
    queue = TaskQueue()
    queue.enqueue({"id": "low"}, "low")
    queue.enqueue({"id": "urgent"}, "urgent")
    queue.enqueue({"id": "normal"}, "normal")
    first = queue.dequeue()
    assert first["id"] == "urgent"
    second = queue.dequeue()
    assert second["id"] == "normal"


def test_task_queue_remove():
    queue = TaskQueue()
    queue.enqueue({"id": "task1"}, "normal")
    queue.enqueue({"id": "task2"}, "normal")
    assert queue.remove("task1") is True
    assert queue.remove("task1") is False
    assert len(queue) == 1


def test_task_template_registry():
    registry = TaskTemplateRegistry()
    templates = registry.list_templates()
    assert len(templates) >= 5
    template = registry.get_template("build_website")
    assert template is not None
    assert template["name"] == "Build Website"


def test_task_template_categories():
    registry = TaskTemplateRegistry()
    dev_templates = registry.get_templates_by_category("development")
    assert len(dev_templates) >= 1


def test_audit_logger_redacts_secrets():
    logger = AuditLogger()
    detail = {"api_key": "secret123", "command": "ls"}
    redacted = logger._redact(detail)
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["command"] == "ls"


def test_audit_logger_no_store():
    logger = AuditLogger(store=None)
    logger.log("task1", "test_event", {"detail": "value"})
    # should not raise


def test_command_result_properties():
    result = CommandResult("ls", 0, "file1\nfile2", "", 0.1)
    assert result.success is True
    assert result.exit_code == 0
    assert result.stdout == "file1\nfile2"


def test_process_manager_cleanup():
    mgr = ProcessManager()
    proc = mgr.register("proc1", 1234, "sleep 10")
    proc.status = "finished"
    mgr.cleanup()
    assert mgr.get("proc1") is None


def test_task_queue_peek():
    queue = TaskQueue()
    queue.enqueue({"id": "task1"}, "normal")
    assert queue.peek()["id"] == "task1"
    queue.dequeue()
    assert queue.peek() is None
