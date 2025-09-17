from typing import Dict, Type, Optional, List
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
    
    def list_tools(self, tool_type: Optional[str] = None) -> Dict[str, Tool]:
        """列出所有可用工具，可以按类型过滤"""
        if tool_type is None:
            return {name: tool_class() for name, tool_class in self._tools.items()}
        
        # 按类型过滤工具
        return {
            name: tool_class()
            for name, tool_class in self._tools.items()
            if getattr(tool_class, 'tool_type', None) == tool_type
        }
    
    def get_functions_schema(self, tool_type: Optional[str] = None) -> list:
        return [tool.to_function_call_schema() for tool in self.list_tools(tool_type).values()]

# 创建全局注册表实例
tool_registry = ToolRegistry()