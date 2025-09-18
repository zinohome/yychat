
import importlib
import inspect
import os
from typing import List, Type
from .base import Tool
from .registry import tool_registry

class ToolDiscoverer:
    @staticmethod
    def discover_tools(directory: str) -> List[Type[Tool]]:
        """自动发现指定目录下所有的Tool子类"""
        discovered_tools = []
        
        # 获取目录的绝对路径
        abs_directory = os.path.abspath(directory)
        
        # 遍历目录下所有的.py文件
        for filename in os.listdir(abs_directory):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = f"services.tools.implementations.{filename[:-3]}"
                
                try:
                    # 动态导入模块
                    module = importlib.import_module(module_name)
                    
                    # 查找模块中所有的Tool子类
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # 检查是否是Tool的子类，且不是Tool本身，且位于当前模块
                        if issubclass(obj, Tool) and obj != Tool and obj.__module__ == module_name:
                            discovered_tools.append(obj)
                except Exception as e:
                    print(f"导入模块 {module_name} 时出错: {e}")
        
        return discovered_tools
    
    @staticmethod
    def register_discovered_tools(directory: str = None) -> int:
        """发现并注册指定目录下的所有工具，返回注册的工具数量"""
        if directory is None:
            # 默认从implementations目录中发现工具
            directory = os.path.join(os.path.dirname(__file__), 'implementations')
        
        # 发现工具
        tools = ToolDiscoverer.discover_tools(directory)
        
        # 注册工具
        for tool_class in tools:
            tool_registry.register(tool_class)
        
        return len(tools)