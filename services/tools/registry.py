from typing import Dict, Type, Optional
from .base import Tool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Type[Tool]] = {}
    
    def register(self, tool_class: Type[Tool]):
        tool = tool_class()
        self._tools[tool.name] = tool_class
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        tool_class = self._tools.get(tool_name)
        if tool_class:
            return tool_class()
        return None
    
    def list_tools(self) -> Dict[str, Tool]:
        return {name: tool_class() for name, tool_class in self._tools.items()}
    
    def get_functions_schema(self) -> list:
        return [tool.to_function_call_schema() for tool in self.list_tools().values()]

# 创建全局注册表实例
tool_registry = ToolRegistry()