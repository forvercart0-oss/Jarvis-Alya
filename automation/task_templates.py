"""Task templates for JARVIS Phase 13."""

from __future__ import annotations

import logging

logger = logging.getLogger("jarvis.automation.templates")


class TaskTemplateRegistry:
    TEMPLATES = [
        {
            "template_id": "build_website",
            "name": "Build Website",
            "description": "Create a simple website with HTML, CSS, and JavaScript.",
            "category": "development",
            "steps": [
                {"title": "Analyze requirements", "action": "analyze", "risk": "low"},
                {"title": "Create project structure", "action": "create_project", "risk": "medium"},
                {"title": "Build frontend", "action": "write_file", "risk": "medium"},
                {"title": "Add assets", "action": "write_file", "risk": "low"},
                {"title": "Test locally", "action": "run_project_command", "risk": "medium"},
                {"title": "Build production", "action": "run_project_command", "risk": "medium"},
            ],
        },
        {
            "template_id": "create_api",
            "name": "Create API",
            "description": "Create a REST API with FastAPI or Flask.",
            "category": "development",
            "steps": [
                {"title": "Analyze requirements", "action": "analyze", "risk": "low"},
                {"title": "Initialize project", "action": "create_project", "risk": "medium"},
                {"title": "Create API endpoints", "action": "write_file", "risk": "medium"},
                {"title": "Add database", "action": "write_file", "risk": "medium"},
                {"title": "Run tests", "action": "run_project_command", "risk": "medium"},
            ],
        },
        {
            "template_id": "create_ecommerce",
            "name": "Create Ecommerce Store",
            "description": "Create a full ecommerce store with frontend and backend.",
            "category": "development",
            "steps": [
                {"title": "Analyze requirements", "action": "analyze", "risk": "low"},
                {"title": "Create project structure", "action": "create_project", "risk": "medium"},
                {"title": "Setup database", "action": "run_project_command", "risk": "medium"},
                {"title": "Create backend", "action": "write_file", "risk": "medium"},
                {"title": "Create frontend", "action": "write_file", "risk": "medium"},
                {"title": "Add authentication", "action": "write_file", "risk": "medium"},
                {"title": "Add product system", "action": "write_file", "risk": "medium"},
                {"title": "Add cart and checkout", "action": "write_file", "risk": "medium"},
                {"title": "Run tests", "action": "run_project_command", "risk": "medium"},
                {"title": "Build production", "action": "run_project_command", "risk": "medium"},
            ],
        },
        {
            "template_id": "research_topic",
            "name": "Research Topic",
            "description": "Deep research on a topic with sources and report.",
            "category": "research",
            "steps": [
                {"title": "Search web", "action": "web_search", "risk": "low"},
                {"title": "Collect sources", "action": "browser_navigate", "risk": "low"},
                {"title": "Analyze findings", "action": "analyze", "risk": "low"},
                {"title": "Create report", "action": "write_file", "risk": "low"},
            ],
        },
        {
            "template_id": "debug_project",
            "name": "Debug Project",
            "description": "Debug a project and fix errors.",
            "category": "development",
            "steps": [
                {"title": "Inspect project", "action": "read_file", "risk": "low"},
                {"title": "Run tests", "action": "run_project_command", "risk": "medium"},
                {"title": "Analyze errors", "action": "analyze", "risk": "low"},
                {"title": "Fix issues", "action": "write_file", "risk": "medium"},
                {"title": "Verify fix", "action": "run_project_command", "risk": "medium"},
            ],
        },
        {
            "template_id": "deploy_project",
            "name": "Deploy Project",
            "description": "Deploy a project to production.",
            "category": "deployment",
            "steps": [
                {"title": "Run tests", "action": "run_project_command", "risk": "medium"},
                {"title": "Build project", "action": "run_project_command", "risk": "medium"},
                {"title": "Check git status", "action": "run_project_command", "risk": "low"},
                {"title": "Commit changes", "action": "run_project_command", "risk": "high"},
                {"title": "Push to remote", "action": "run_project_command", "risk": "high"},
                {"title": "Deploy", "action": "run_project_command", "risk": "high"},
            ],
        },
        {
            "template_id": "install_project",
            "name": "Install Project",
            "description": "Install a project and its dependencies.",
            "category": "development",
            "steps": [
                {"title": "Clone repository", "action": "run_project_command", "risk": "low"},
                {"title": "Install dependencies", "action": "run_project_command", "risk": "medium"},
                {"title": "Setup environment", "action": "write_file", "risk": "medium"},
                {"title": "Verify installation", "action": "run_project_command", "risk": "low"},
            ],
        },
        {
            "template_id": "generate_docs",
            "name": "Generate Documentation",
            "description": "Generate documentation for a project.",
            "category": "documentation",
            "steps": [
                {"title": "Analyze project", "action": "read_file", "risk": "low"},
                {"title": "Generate README", "action": "write_file", "risk": "low"},
                {"title": "Create API docs", "action": "write_file", "risk": "low"},
            ],
        },
    ]

    def list_templates(self) -> list[dict]:
        return list(self.TEMPLATES)

    def get_template(self, template_id: str) -> dict | None:
        for t in self.TEMPLATES:
            if t["template_id"] == template_id:
                return t
        return None

    def get_templates_by_category(self, category: str) -> list[dict]:
        return [t for t in self.TEMPLATES if t.get("category") == category]
