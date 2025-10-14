"""
工具模块初始化
"""
from .registry import tool_registry
from .implementations.calculator import CalculatorTool
from .implementations.time_tool import TimeTool
from .implementations.tavily_search import TavilySearchTool

# 注册所有工具
tool_registry.register(CalculatorTool)
tool_registry.register(TimeTool)
tool_registry.register(TavilySearchTool)
