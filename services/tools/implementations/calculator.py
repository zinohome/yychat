import math
from typing import Dict, Any
from ..base import Tool
from ..registry import tool_registry

class CalculatorTool(Tool):
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "用于执行数学计算的工具"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide", "pow", "sqrt"],
                "description": "要执行的操作"
            },
            "a": {
                "type": "number",
                "description": "第一个操作数"
            },
            "b": {
                "type": "number",
                "description": "第二个操作数，平方根操作不需要此项"
            }
        }
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        operation = params.get("operation")
        a = params.get("a")
        b = params.get("b")
        
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("除数不能为零")
            result = a / b
        elif operation == "pow":
            result = math.pow(a, b)
        elif operation == "sqrt":
            if a < 0:
                raise ValueError("不能计算负数的平方根")
            result = math.sqrt(a)
        else:
            raise ValueError(f"不支持的操作: {operation}")
        
        return {
            "operation": operation,
            "result": result,
            "input": params
        }

# 注册工具
tool_registry.register(CalculatorTool)