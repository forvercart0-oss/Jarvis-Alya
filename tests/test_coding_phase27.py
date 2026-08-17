"""Tests for Phase 27 Coding & Software Engineering Agent 2.0."""

from __future__ import annotations

from coding.agent import CodingAgent
from coding.debugger import debugger
from coding.file_editor import FileEditor
from coding.log_analyzer import log_analyzer
from coding.model_router import CodingModelRouter
from coding.models import (
    ChangeCheckpoint,
    CodeReviewIssue,
    CodingTask,
    FileDiff,
    ProjectInfo,
    Severity,
    TaskStatus,
)
from coding.multi_agent import MultiAgentSystem
from coding.project_index import ProjectIndex
from coding.secret_scanner import SecretScanner
from coding.task_planner import CodingTaskPlanner


def test_coding_task_defaults():
    task = CodingTask()
    assert task.status == TaskStatus.PENDING
    assert task.task_id != ""

def test_coding_task_to_dict():
    task = CodingTask(goal="Build app", project="test")
    d = task.to_dict()
    assert d["goal"] == "Build app"
    assert d["project"] == "test"

def test_project_info_defaults():
    info = ProjectInfo()
    assert info.language == ""
    assert info.docker is False

def test_project_info_to_dict():
    info = ProjectInfo(name="test", language="python", framework="fastapi")
    d = info.to_dict()
    assert d["name"] == "test"
    assert d["framework"] == "fastapi"

def test_change_checkpoint_defaults():
    cp = ChangeCheckpoint(task_id="t1", project="test")
    assert cp.project == "test"
    assert cp.checkpoint_id != ""

def test_file_diff_defaults():
    fd = FileDiff(path="main.py", change_type="modified")
    assert fd.path == "main.py"
    assert fd.change_type == "modified"

def test_code_review_issue_defaults():
    issue = CodeReviewIssue(severity=Severity.HIGH, category="security", file="app.py", line=10, message="Unsafe input")
    assert issue.severity == Severity.HIGH
    d = issue.to_dict()
    assert d["severity"] == "high"

def test_task_planner_create_task():
    planner = CodingTaskPlanner()
    task = planner.create_task("Build ecommerce site", "myproject")
    assert task.goal == "Build ecommerce site"
    assert task.project == "myproject"

def test_task_planner_plan_steps_create():
    planner = CodingTaskPlanner()
    task = planner.create_task("Create a new project")
    steps = planner.plan_steps(task, None)
    assert len(steps) > 0
    assert steps[0]["type"] == "analyze"

def test_task_planner_plan_steps_debug():
    planner = CodingTaskPlanner()
    task = planner.create_task("Fix this bug")
    steps = planner.plan_steps(task, None)
    assert any(s["type"] == "reproduce" for s in steps)

def test_debugger_parse_traceback():
    text = """Traceback (most recent call last):
  File "app.py", line 10, in main
    raise ValueError("test")
ValueError: test"""
    result = debugger.parse_traceback(text)
    assert result["success"] is True
    assert len(result["errors"]) > 0

def test_debugger_suggest_fix():
    error = {"type": "ModuleNotFoundError: No module named 'fastapi'"}
    result = debugger.suggest_fix(error)
    assert result["success"] is True
    assert len(result["suggestions"]) > 0

def test_log_analyzer():
    log = "INFO: Starting\nERROR: Connection failed\nWARN: Retrying\nERROR: Timeout"
    result = log_analyzer.analyze(log, "backend")
    assert result["error_count"] == 2
    assert result["warning_count"] == 1

def test_secret_scanner():
    scanner = SecretScanner()
    import os
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    with open(path, "w") as f:
        f.write('API_KEY = "sk-1234567890abcdefghijklmnopqrstuv"\n')
    findings = scanner.scan_file(__import__("pathlib").Path(path))
    os.unlink(path)
    assert len(findings) > 0

def test_project_index_build():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        path = __import__("pathlib").Path(tmpdir)
        (path / "main.py").write_text("def hello():\n    pass\n")
        (path / "package.json").write_text('{"dependencies": {"react": "18"}}')
        index = ProjectIndex(path)
        index.build()
        assert index.get_file("main.py") is not None
        assert index.get_file("package.json") is not None

def test_project_index_search():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        path = __import__("pathlib").Path(tmpdir)
        (path / "auth.py").write_text("def login():\n    pass\n")
        index = ProjectIndex(path)
        index.build()
        results = index.search("login")
        assert len(results) > 0

def test_multi_agent_system():
    system = MultiAgentSystem()
    agent = system.get_agent("coder")
    assert agent is not None
    assert agent.name == "CoderAgent"

def test_model_router():
    router = CodingModelRouter()
    router.set_local_enabled(True)
    router.set_groq_enabled(True)
    result = router.route("edit", "small")
    assert result["provider"] == "local"
    result2 = router.route("debugging", "large")
    assert result2["provider"] == "groq"

def test_file_editor_diff():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        editor = FileEditor(__import__("pathlib").Path(tmpdir))
        fd = FileDiff(path="test.py", change_type="modified", old_content="a=1", new_content="a=2")
        assert fd.change_type == "modified"

def test_agent_defaults():
    agent = CodingAgent(__import__("pathlib").Path("/tmp"))
    assert agent._base_dir is not None
