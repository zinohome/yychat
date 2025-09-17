import pytest
from services.tools.base import Tool
from typing import Dict, Any

# 创建一个实现了Tool抽象类的具体工具类用于测试
class TestTool(Tool):
    tool_type = "test"
    
    @property
    def name(self):
        return "test_tool"
    
    @property
    def description(self):
        return "A test tool"
    
    @property
    def parameters(self):
        return {
            "param1": {
                "type": "string",
                "description": "First parameter"
            },
            "param2": {
                "type": "integer",
                "description": "Second parameter"
            }
        }
    
    async def execute(self, params: Dict[str, Any]):
        return f"Executed with {params}"

# 测试Tool基类的基本功能
def test_tool_base_properties():
    tool = TestTool()
    assert tool.name == "test_tool"
    assert tool.description == "A test tool"
    assert tool.tool_type == "test"
    assert "param1" in tool.parameters
    assert "param2" in tool.parameters

# 测试to_function_call_schema方法
def test_tool_function_call_schema():
    tool = TestTool()
    schema = tool.to_function_call_schema()
    
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "test_tool"
    assert schema["function"]["description"] == "A test tool"
    assert schema["function"]["parameters"]["type"] == "object"
    assert "param1" in schema["function"]["parameters"]["properties"]
    assert "param2" in schema["function"]["parameters"]["properties"]

# 测试execute方法
@pytest.mark.asyncio
async def test_tool_execute():
    tool = TestTool()
    result = await tool.execute({"param1": "value1", "param2": 42})
    
    assert result == "Executed with {'param1': 'value1', 'param2': 42}"

# 测试未实现抽象方法的情况
def test_abstract_method_enforcement():
    # 定义一个没有实现所有抽象方法的类
    with pytest.raises(TypeError):
        class IncompleteTool(Tool):
            @property
            def name(self):
                return "incomplete_tool"
            # 故意不实现其他抽象方法