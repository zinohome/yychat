import logging
from typing import Dict, Any

from services.mcp.manager import mcp_manager
from services.tools.registry import tool_registry
from services.tools.base import Tool

logger = logging.getLogger(__name__)

def discover_and_register_mcp_tools():
    """发现并注册MCP工具"""
    try:
        # 检查mcp_manager是否初始化成功
        if not hasattr(mcp_manager, '_clients') or mcp_manager._clients is None:
            logger.warning("MCP manager not properly initialized, skipping tool discovery")
            return
        
        # 获取MCP服务中的所有工具
        tools = mcp_manager.list_tools()
        logger.info(f"发现并注册MCP工具, 共发现 {len(tools)} 个工具")
        
        # 动态创建Tool类并注册
        for tool_info in tools:
            tool_name = tool_info.get('name')
            tool_description = tool_info.get('description', '')
            input_schema = tool_info.get('inputSchema', {})
            
            # 使用类变量而不是闭包变量来存储工具信息
            class DynamicMCPTool(Tool):
                # 使用类变量存储工具信息
                _tool_name = tool_name
                _tool_description = tool_description
                _tool_input_schema = input_schema
                
                @property
                def name(self):
                    return self._tool_name
                
                @property
                def description(self):
                    return self._tool_description
                
                @property
                def parameters(self):
                    return self._tool_input_schema.get('properties', {})
                
                # 修复execute方法签名，使其匹配基类
                async def execute(self, params: Dict[str, Any]):
                    try:
                        result = mcp_manager.call_tool(tool_name, params)
                        # 格式化结果
                        if result and len(result) > 0:
                            return result[0].get('text') or str(result)
                        return str(result)
                    except Exception as e:
                        logger.error(f"Error executing MCP tool {tool_name}: {str(e)}")
                        return f"执行MCP工具失败: {str(e)}"
            # 注册工具类本身，而不是实例
            tool_registry.register(DynamicMCPTool)
            logger.info(f"自动注册MCP tool: {tool_name}")
    except Exception as e:
        logger.error(f"Failed to discover and register MCP tools: {str(e)}")