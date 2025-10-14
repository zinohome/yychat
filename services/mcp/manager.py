import json
from utils.log import log
import os
from typing import Any, Dict, List

from config.config import get_config
from services.mcp.exceptions import MCPServerNotFoundError, MCPToolNotFoundError, MCPServiceError
from services.mcp.utils.mcp_client import McpClients




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
                    log.info(f"Loading MCP servers config from file: {servers_config}")
                    self._clients = McpClients(servers_config)
                except json.JSONDecodeError as e:
                    log.error(f"Failed to parse MCP servers config JSON file: {str(e)}")
                    log.warning("Using empty MCP clients configuration")
                    self._clients = None
            else:
                log.warning(f"MCP servers config file not found at {config_path}")
                # 回退到从环境变量加载
                config = get_config()
                servers_config_json = config.MCP_SERVERS_CONFIG
                if servers_config_json:
                    try:
                        servers_config = json.loads(servers_config_json)
                        log.debug(f"Loading MCP servers config from environment variable: {servers_config}")
                        self._clients = McpClients(servers_config)
                    except json.JSONDecodeError as e:
                        log.error(f"Failed to parse MCP servers config JSON from environment variable: {str(e)}")
                        log.warning("Using empty MCP clients configuration")
                        self._clients = None
                else:
                    log.warning("No MCP servers config found")
                    self._clients = None
        except Exception as e:
            log.error(f"Failed to initialize MCP clients: {str(e)}")
            # 使用None而不是抛出异常，这样应用程序可以继续运行
            self._clients = None
    
    def list_tools(self) -> List[Dict]:
        """列出所有可用的MCP工具"""
        if not self._clients:
            log.warning("MCP clients not initialized, returning empty tool list")
            return []
        try:
            return self._clients.fetch_tools()
        except Exception as e:
            log.error(f"Failed to list MCP tools: {str(e)}")
            # 不抛出异常，而是返回空列表，让调用者可以继续工作
            return []
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any], mcp_server: str = None) -> List[Dict]:
        """调用指定的MCP工具，可以选择特定的MCP服务器"""
        if not self._clients:
            raise MCPServiceError("MCP clients not initialized")
        try:
            log.debug(f"Calling MCP tool: {tool_name}, arguments: {arguments}, server: {mcp_server or 'auto'}")
            
            # 如果指定了服务器，优先尝试在该服务器上调用
            if mcp_server:
                # 检查服务器是否存在
                if mcp_server not in self._clients._clients:
                    raise MCPServerNotFoundError(f"MCP server '{mcp_server}' not found")
                
                # 构建可能的完整工具名
                prefixed_tool_name = f"{mcp_server}__{tool_name}"
                
                # 检查是否存在带前缀的同名工具
                if prefixed_tool_name in self._clients._tool_actions:
                    log.info(f"MCP dispatch: server={mcp_server}, tool={prefixed_tool_name}, args={arguments}")
                    return self._clients.execute_tool(prefixed_tool_name, arguments)
                # 尝试直接使用原始工具名
                elif tool_name in self._clients._tool_actions:
                    log.info(f"MCP dispatch: server={mcp_server}, tool={tool_name}, args={arguments}")
                    return self._clients.execute_tool(tool_name, arguments)
                else:
                    raise MCPToolNotFoundError(f"MCP tool '{tool_name}' not found on server '{mcp_server}'")
            
            # 优先按固定偏好服务器调用（针对已知稳定服务），避免不必要的路由变更
            # 当前仅对 maps_weather 固定到 amap-amap-sse，如存在
            if tool_name == "maps_weather" and hasattr(self._clients, "_tool_actions"):
                preferred_server = "amap-amap-sse"
                preferred_registered = f"{preferred_server}__{tool_name}"
                if preferred_registered in self._clients._tool_actions:
                    try:
                        log.info(f"MCP dispatch: server={preferred_server}, tool={preferred_registered}, args={arguments}")
                        return self._clients.execute_tool(preferred_registered, arguments)
                    except Exception as e:
                        log.warning(f"Preferred server '{preferred_server}' failed for {tool_name}: {e}")
                        # 继续走默认逻辑

            # 自动选择服务器调用（按已注册的工具映射）
            log.info(f"MCP dispatch: server=auto, tool={tool_name}, args={arguments}")
            return self._clients.execute_tool(tool_name, arguments)
        except MCPToolNotFoundError:
            raise
        except Exception as e:
            # 对 5xx（如 502）执行一次快速重试，并在重试前重建客户端以刷新会话/连接
            error_text = str(e)
            log.error(f"Failed to call MCP tool: {error_text}")
            should_retry = (" 502 " in error_text) or ("502 Bad Gateway" in error_text) or ("HTTPStatusError" in error_text)
            if should_retry:
                try:
                    log.warning("MCP call received 5xx, reinitializing clients and retrying once...")
                    # 重建客户端（刷新会话/连接）
                    self._clients = None
                    self._initialize()
                    # 重试同样调用路径
                    if mcp_server:
                        log.info(f"MCP retry dispatch: server={mcp_server}, tool={tool_name}, args={arguments}")
                        return self.call_tool(tool_name, arguments, mcp_server=mcp_server)
                    if tool_name == "maps_weather" and hasattr(self._clients, "_tool_actions"):
                        preferred_server = "amap-amap-sse"
                        preferred_registered = f"{preferred_server}__{tool_name}"
                        if preferred_registered in self._clients._tool_actions:
                            log.info(f"MCP retry dispatch: server={preferred_server}, tool={preferred_registered}, args={arguments}")
                            return self._clients.execute_tool(preferred_registered, arguments)
                    log.info(f"MCP retry dispatch: server=auto, tool={tool_name}, args={arguments}")
                    return self._clients.execute_tool(tool_name, arguments)
                except Exception as e2:
                    log.error(f"Retry MCP tool call failed: {e2}")
                    raise MCPServiceError(f"Failed to call MCP tool: {e2}")
            raise MCPServiceError(f"Failed to call MCP tool: {error_text}")
    
    def close(self):
        """关闭所有MCP客户端连接"""
        if self._clients:
            try:
                self._clients.close()
            except Exception as e:
                log.error(f"Failed to close MCP clients: {str(e)}")


# 创建全局MCP管理器实例
# 延迟初始化，避免重复创建
mcp_manager = None

def get_mcp_manager():
    """获取MCP管理器实例（延迟初始化）"""
    global mcp_manager
    if mcp_manager is None:
        mcp_manager = MCPManager()
    return mcp_manager


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
        log.error(f"Error calling MCP tool '{tool_name}': {str(e)}")
        raise MCPServiceError(f"Failed to call MCP tool: {str(e)}")