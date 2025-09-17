import json
import logging
from typing import Any, Dict, List

from config.config import get_config
from services.mcp.exceptions import MCPServiceError
from services.mcp.utils.mcp_client import McpClients

logger = logging.getLogger(__name__)


class MCPManager:
    """MCP服务管理器，提供统一的MCP服务调用接口"""
    _instance = None
    _clients = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MCPManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化MCP客户端"""
        try:
            config = get_config()
            # 从环境变量加载MCP服务器配置
            servers_config_json = config.MCP_SERVERS_CONFIG
            if servers_config_json:
                servers_config = json.loads(servers_config_json)
                logger.info(f"Loading MCP servers config: {servers_config}")
                self._clients = McpClients(servers_config)
            else:
                logger.warning("No MCP servers config found")
                self._clients = None
        except Exception as e:
            logger.error(f"Failed to initialize MCP clients: {str(e)}")
            raise MCPServiceError(f"Failed to initialize MCP clients: {str(e)}")
    
    def list_tools(self) -> List[Dict]:
        """列出所有可用的MCP工具"""
        if not self._clients:
            return []
        try:
            return self._clients.fetch_tools()
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {str(e)}")
            raise MCPServiceError(f"Failed to list MCP tools: {str(e)}")
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> List[Dict]:
        """调用指定的MCP工具"""
        if not self._clients:
            raise MCPServiceError("MCP clients not initialized")
        try:
            logger.info(f"Calling MCP tool: {tool_name}, arguments: {arguments}")
            return self._clients.execute_tool(tool_name, arguments)
        except Exception as e:
            logger.error(f"Failed to call MCP tool {tool_name}: {str(e)}")
            raise MCPServiceError(f"Failed to call MCP tool {tool_name}: {str(e)}")
    
    def close(self):
        """关闭所有MCP客户端连接"""
        if self._clients:
            try:
                self._clients.close()
            except Exception as e:
                logger.error(f"Failed to close MCP clients: {str(e)}")


# 创建全局MCP管理器实例
mcp_manager = MCPManager()