import json
from utils.log import log
from typing import Optional, Dict, Any

from config.config import get_config




class MCPConfig:
    """MCP服务配置类"""
    
    def __init__(self):
        config = get_config()
        self.mcp_service_url = config.MCP_SERVICE_URL
        self.mcp_api_key = config.MCP_API_KEY
        self.mcp_cache_ttl = config.MCP_CACHE_TTL
        
        # 加载多MCP服务器配置
        try:
            self.servers_config = json.loads(config.MCP_SERVERS_CONFIG) if config.MCP_SERVERS_CONFIG else None
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse MCP servers config: {str(e)}")
            self.servers_config = None


def get_mcp_config() -> MCPConfig:
    """获取MCP服务配置"""
    return MCPConfig()