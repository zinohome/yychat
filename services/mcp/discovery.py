import logging
from typing import Dict, Any

from services.mcp.manager import mcp_manager
from services.tools.registry import tool_registry
from services.tools.base import Tool

logger = logging.getLogger(__name__)


def discover_and_register_mcp_tools():
    """发现并注册MCP工具"""
    try:
        # 获取MCP服务中的所有工具
        tools = mcp_manager.list_tools()
        logger.info(f"Discovered {len(tools)} MCP tools")
        
        # 动态创建Tool类并注册
        for tool_info in tools:
            tool_name = tool_info.get('name')
            tool_description = tool_info.get('description', '')
            input_schema = tool_info.get('inputSchema', {})
            
            # 创建动态Tool类
            class DynamicMCPTool(Tool):
                @property
                def name(self):
                    return tool_name
                
                @property
                def description(self):
                    return tool_description
                
                @property
                def parameters(self):
                    return input_schema
                
                async def execute(self, **kwargs):
                    return mcp_manager.call_tool(tool_name, kwargs)
        
            # 注册工具
            tool_registry.register(DynamicMCPTool())
            logger.info(f"Registered MCP tool: {tool_name}")
    except Exception as e:
        logger.error(f"Failed to discover and register MCP tools: {str(e)}")