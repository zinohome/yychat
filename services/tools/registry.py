from typing import Dict, Optional, Type
from .base import Tool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Type[Tool]] = {}
        self._schema_cache = None  # Schema缓存
        self._schema_dirty = False  # 缓存脏标记
    
    def register(self, tool_class: Type[Tool]):
        # 检查是否是Tool的子类
        if not issubclass(tool_class, Tool):
            raise TypeError(f"Only Tool subclasses can be registered, got {tool_class.__name__}")
        
        tool = tool_class()
        # 如果工具已经注册，跳过（避免重复注册）
        if tool.name in self._tools:
            return
        self._tools[tool.name] = tool_class
        self._schema_dirty = True  # 标记Schema缓存失效
    
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
        # 如果缓存有效且不需要过滤类型，直接返回缓存
        if tool_type is None and self._schema_cache is not None and not self._schema_dirty:
            return self._schema_cache
        
        # 重建Schema
        schema = [tool.to_function_call_schema() for tool in self.list_tools(tool_type).values()]
        
        # 只有在不过滤类型时才缓存
        if tool_type is None:
            self._schema_cache = schema
            self._schema_dirty = False
        
        return schema

# 创建全局注册表实例
tool_registry = ToolRegistry()