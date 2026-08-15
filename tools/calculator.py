import ast
import operator
from tools.registry import ToolResult


SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class CalculatorTool:
    name = "calculator"
    description = "Evaluate a mathematical expression."
    parameters = {
        "type": "object",
        "properties": {"expression": {"type": "string", "description": "Math expression like 25*48"}},
        "required": ["expression"],
    }

    async def execute(self, expression: str, **kwargs) -> ToolResult:
        try:
            node = ast.parse(expression, mode="eval")
            result = self._eval(node.body)
            return ToolResult(success=True, result={"result": result})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def _eval(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            left = self._eval(node.left)
            right = self._eval(node.right)
            return SAFE_OPERATORS[op_type](left, right)
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
            operand = self._eval(node.operand)
            return SAFE_OPERATORS[op_type](operand)
        if isinstance(node, ast.Expression):
            return self._eval(node.body)
        raise ValueError(f"Unsupported expression: {type(node).__name__}")
