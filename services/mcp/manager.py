import json
import logging
import os
from typing import Any, Dict, List

from config.config import get_config
from services.mcp.exceptions import MCPServerNotFoundError, MCPToolNotFoundError, MCPServiceError
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
            # 从配置文件加载MCP服务器配置
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'mcp.json')
            
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        servers_config = json.load(f)
                    logger.info(f"Loading MCP servers config from file: {servers_config}")
                    self._clients = McpClients(servers_config)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse MCP servers config JSON file: {str(e)}")
                    logger.warning("Using empty MCP clients configuration")
                    self._clients = None
            else:
                logger.warning(f"MCP servers config file not found at {config_path}")
                # 回退到从环境变量加载
                config = get_config()
                servers_config_json = config.MCP_SERVERS_CONFIG
                if servers_config_json:
                    try:
                        servers_config = json.loads(servers_config_json)
                        logger.info(f"Loading MCP servers config from environment variable: {servers_config}")
                        self._clients = McpClients(servers_config)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse MCP servers config JSON from environment variable: {str(e)}")
                        logger.warning("Using empty MCP clients configuration")
                        self._clients = None
                else:
                    logger.warning("No MCP servers config found")
                    self._clients = None
        except Exception as e:
            logger.error(f"Failed to initialize MCP clients: {str(e)}")
            # 使用None而不是抛出异常，这样应用程序可以继续运行
            self._clients = None
    
    def list_tools(self) -> List[Dict]:
        """列出所有可用的MCP工具"""
        if not self._clients:
            return []
        try:
            return self._clients.fetch_tools()
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {str(e)}")
            raise MCPServiceError(f"Failed to list MCP tools: {str(e)}")
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any], mcp_server: str = None) -> List[Dict]:
        """调用指定的MCP工具，可以选择特定的MCP服务器"""
        if not self._clients:
            raise MCPServiceError("MCP clients not initialized")
        try:
            logger.info(f"Calling MCP tool: {tool_name}, arguments: {arguments}, server: {mcp_server or 'auto'}")
            
            # 如果指定了服务器，优先尝试在该服务器上调用
            if mcp_server:
                # 检查服务器是否存在
                if mcp_server not in self._clients._clients:
                    raise MCPServerNotFoundError(f"MCP server '{mcp_server}' not found")
                
                # 构建完整的工具名（如果需要）
                full_tool_name = tool_name
                if not tool_name.startswith(f"{mcp_server}__"):
                    # 检查是否存在带前缀的同名工具
                    prefixed_tool_name = f"{mcp_server}__{tool_name}"
                    if prefixed_tool_name in self._clients._tool_actions:
                        full_tool_name = prefixed_tool_name
                
                try:
                    return self._clients.execute_tool(full_tool_name, arguments)
                except Exception as e:
                    # 如果指定服务器调用失败，尝试自动选择服务器
                    logger.warning(f"Failed to call tool on specified server, trying auto-selection: {str(e)}")
                    
            # 自动选择服务器调用
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


def call_tool(self, tool_name: str, params: dict, mcp_server: str = None):
    """调用指定的MCP工具，可以选择特定的MCP服务器"""
    try:
        # 如果指定了服务器，则使用该服务器
        if mcp_server:
            client = self.clients.get_client(mcp_server)
            if not client:
                raise MCPServerNotFoundError(f"MCP server '{mcp_server}' not found")
            return client.call_tool(tool_name, params)
        
        # 否则使用默认逻辑查找可用工具
        for client in self.clients.clients:
            if client.has_tool(tool_name):
                return client.call_tool(tool_name, params)
        
        # 如果找不到工具，尝试在所有客户端上调用（兼容性处理）
        for client in self.clients.clients:
            try:
                return client.call_tool(tool_name, params)
            except MCPToolNotFoundError:
                continue
        
        raise MCPToolNotFoundError(f"Tool '{tool_name}' not found in any MCP server")
    except Exception as e:
        logger.error(f"Error calling MCP tool '{tool_name}': {str(e)}")
        raise MCPServiceError(f"Failed to call MCP tool: {str(e)}")