import pytest
from tools.calculator import CalculatorTool


@pytest.mark.asyncio
async def test_calculate_add():
    tool = CalculatorTool()
    result = await tool.execute(expression="2 + 2")
    assert result.success is True
    assert result.result["result"] == 4


@pytest.mark.asyncio
async def test_calculate_mul():
    tool = CalculatorTool()
    result = await tool.execute(expression="25 * 48")
    assert result.success is True
    assert result.result["result"] == 1200


@pytest.mark.asyncio
async def test_calculate_unsupported():
    tool = CalculatorTool()
    result = await tool.execute(expression="import os")
    assert result.success is False
