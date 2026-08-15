"""Tests for the time/date tools."""

from __future__ import annotations

from datetime import datetime

import pytest

from tools.time import DateTool, TimeTool


@pytest.mark.asyncio
async def test_time_tool_local():
    tool = TimeTool()
    result = await tool.execute()
    assert result.get("success") is not False
    assert result["timezone"] == "local"
    assert len(result["time"]) == 8


@pytest.mark.asyncio
async def test_time_tool_known_timezone():
    tool = TimeTool()
    result = await tool.execute(timezone="UTC")
    assert result["timezone"] == "UTC"
    assert len(result["time"]) == 8
    assert (
        result["iso"].endswith("+00:00")
        or result["iso"].endswith("Z")
        or "+00:00" in result["iso"]
        or result["iso"].startswith("202")
    )


@pytest.mark.asyncio
async def test_time_tool_unknown_timezone():
    tool = TimeTool()
    result = await tool.execute(timezone="Not/AZone")
    assert result["success"] is False
    assert "Unknown timezone" in result["error"]


@pytest.mark.asyncio
async def test_date_tool():
    tool = DateTool()
    result = await tool.execute()
    assert result["date"] == datetime.now().astimezone().date().isoformat()
    assert result["weekday"]
