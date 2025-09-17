import pytest
from unittest.mock import patch, MagicMock
from services.tools.registry import ToolRegistry
from services.tools.base import Tool
from typing import Dict, Any

# 创建测试工具类
class TestTool1(Tool):
    @property
    def name(self):
        return "test_tool_1"
    
    @property
    def description(self):
        return "First test tool"
    
    @property
    def parameters(self):
        return {}
    
    async def execute(self, params: Dict[str, Any]):
        return "Test result 1"

class TestTool2(Tool):
    tool_type = "special"
    
    @property
    def name(self):
        return "test_tool_2"
    
    @property
    def description(self):
        return "Second test tool"
    
    @property
    def parameters(self):
        return {}
    
    async def execute(self, params: Dict[str, Any]):
        return "Test result 2"

# 测试ToolRegistry的基本功能
def test_tool_registry_register_and_get():
    registry = ToolRegistry()
    
    # 注册工具
    registry.register(TestTool1)
    
    # 获取工具
    tool = registry.get_tool("test_tool_1")
    
    # 验证工具是否正确获取
    assert tool is not None
    assert tool.name == "test_tool_1"
    
    # 尝试获取不存在的工具
    non_existent_tool = registry.get_tool("non_existent_tool")
    assert non_existent_tool is None

# 测试注册多个工具
def test_tool_registry_multiple_tools():
    registry = ToolRegistry()
    
    # 注册多个工具
    registry.register(TestTool1)
    registry.register(TestTool2)
    
    # 验证可以正确获取各个工具
    tool1 = registry.get_tool("test_tool_1")
    tool2 = registry.get_tool("test_tool_2")
    
    assert tool1 is not None
    assert tool1.name == "test_tool_1"
    assert tool2 is not None
    assert tool2.name == "test_tool_2"

# 测试list_tools方法
def test_tool_registry_list_tools():
    registry = ToolRegistry()
    
    # 注册多个工具
    registry.register(TestTool1)
    registry.register(TestTool2)
    
    # 列出所有工具
    tools = registry.list_tools()
    
    # 验证工具数量和名称
    assert len(tools) == 2
    assert "test_tool_1" in tools
    assert "test_tool_2" in tools

# 测试按类型过滤工具
def test_tool_registry_list_tools_by_type():
    registry = ToolRegistry()
    
    # 注册多个具有不同类型的工具
    registry.register(TestTool1)  # 没有指定tool_type
    registry.register(TestTool2)  # tool_type="special"
    
    # 按类型过滤工具
    special_tools = registry.list_tools(tool_type="special")
    
    # 验证只返回了指定类型的工具
    assert len(special_tools) == 1
    assert "test_tool_2" in special_tools
    
    # 测试过滤不存在的类型
    non_existent_type_tools = registry.list_tools(tool_type="non_existent")
    assert len(non_existent_type_tools) == 0

# 测试get_functions_schema方法
def test_tool_registry_get_functions_schema():
    registry = ToolRegistry()
    
    # 注册工具
    registry.register(TestTool1)
    
    # 获取工具函数调用模式
    schemas = registry.get_functions_schema()
    
    # 验证模式数量和内容
    assert len(schemas) == 1
    assert schemas[0]["type"] == "function"
    assert schemas[0]["function"]["name"] == "test_tool_1"
    
    # 测试按类型获取模式
    special_schemas = registry.get_functions_schema(tool_type="special")
    assert len(special_schemas) == 0

# 测试全局registry实例
def test_global_tool_registry():
    from services.tools.registry import tool_registry
    
    # 验证全局实例是ToolRegistry的实例
    assert isinstance(tool_registry, ToolRegistry)

# 测试工具注册的异常处理
def test_tool_registry_register_exception():
    registry = ToolRegistry()
    
    # 创建一个有问题的工具类
    class ProblematicTool:
        # 不是Tool的子类
        @property
        def name(self):
            return "problematic"
    
    # 尝试注册非Tool子类，应该会抛出异常
    with pytest.raises(Exception):
        registry.register(ProblematicTool)