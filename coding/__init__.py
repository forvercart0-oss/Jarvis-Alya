"""Coding package for JARVIS Phase 27."""

from __future__ import annotations

from coding.agent import CodingAgent, coding_agent
from coding.command_runner import CommandRunner, command_runner
from coding.database_agent import DatabaseAgent, database_agent
from coding.debugger import Debugger, debugger
from coding.file_editor import FileEditor, file_editor
from coding.git_manager import CodingGitManager, coding_git_manager
from coding.log_analyzer import LogAnalyzer, log_analyzer
from coding.model_router import CodingModelRouter, coding_model_router
from coding.models import (
    AgentType,
    ChangeCheckpoint,
    ChangeStatus,
    CodeReviewIssue,
    CodingTask,
    FileDiff,
    ProjectInfo,
    Severity,
    TaskStatus,
)
from coding.multi_agent import MultiAgentSystem, multi_agent_system
from coding.project_index import ProjectIndex, project_index
from coding.repository_analyzer import RepositoryAnalyzer, repository_analyzer
from coding.secret_scanner import SecretScanner, secret_scanner
from coding.task_planner import CodingTaskPlanner, coding_task_planner
from coding.test_runner import TestRunner, test_runner

__all__ = [
    "AgentType",
    "ChangeCheckpoint",
    "ChangeStatus",
    "CodeReviewIssue",
    "CodingAgent",
    "CodingGitManager",
    "CodingModelRouter",
    "CodingTask",
    "CodingTaskPlanner",
    "CommandRunner",
    "DatabaseAgent",
    "Debugger",
    "FileDiff",
    "FileEditor",
    "LogAnalyzer",
    "MultiAgentSystem",
    "ProjectIndex",
    "ProjectInfo",
    "RepositoryAnalyzer",
    "SecretScanner",
    "Severity",
    "TaskStatus",
    "TestRunner",
    "coding_agent",
    "coding_git_manager",
    "coding_model_router",
    "coding_task_planner",
    "command_runner",
    "database_agent",
    "debugger",
    "file_editor",
    "log_analyzer",
    "multi_agent_system",
    "project_index",
    "repository_analyzer",
    "secret_scanner",
    "test_runner",
]
