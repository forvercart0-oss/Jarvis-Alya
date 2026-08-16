"""Tests for project tools."""

from __future__ import annotations

import pytest

from tools.projects import ListProjectsTool, CreateProjectTool, _slug, _project_path, _read_allowed


def test_slug_generation():
    assert _slug("My Cool Project") == "my-cool-project"
    assert _slug("   ") == "project"


def test_project_path_sanitization(tmp_path):
    from tools.projects import _PROJECTS_DIR
    original = _PROJECTS_DIR
    try:
        import tools.projects as proj_mod
        proj_mod._PROJECTS_DIR = tmp_path
        path = _project_path("test")
        assert path.is_relative_to(tmp_path)
    finally:
        proj_mod._PROJECTS_DIR = original


def test_read_allowed_blocks_escape(tmp_path):
    with pytest.raises(ValueError):
        _read_allowed(tmp_path, "../../etc/passwd")


@pytest.mark.asyncio
async def test_list_projects_empty(tmp_db):
    tool = ListProjectsTool()
    result = await tool.execute()
    assert result.success is True
    assert "projects" in result.result


@pytest.mark.asyncio
async def test_create_and_list_project(tmp_db):
    import uuid
    name = f"phase2-test-{uuid.uuid4().hex[:8]}"
    create = CreateProjectTool()
    res = await create.execute(name=name, description="Test project", stack="python")
    assert res.success is True
    assert res.result["project"]["name"] == name

    list_tool = ListProjectsTool()
    result = await list_tool.execute()
    names = [p["name"] for p in result.result["projects"]]
    assert name in names
