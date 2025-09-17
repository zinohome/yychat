import asyncio
import hashlib
import json
from typing import Dict, Any, Optional
import aiohttp
from cachetools import TTLCache

from config import get_logger
from .mcpconfig import get_mcp_config
from .models import MCPRequest, MCPResponse
from .exceptions import (
    MCPServiceError,
    MCPConnectionError,
    MCPAuthenticationError,
    MCPResponseError
)


logger = get_logger(__name__)

class MCPClient:
    def __init__(self):
        self.config = get_mcp_config()
        # 创建缓存，使用TTLCache自动过期
        self._cache = TTLCache(maxsize=1000, ttl=self.config.cache_ttl)
        self._session = None
    
    async def _ensure_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.config.api_key}"
                }
            )
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _generate_cache_key(self, request: MCPRequest) -> str:
        # 生成请求的唯一缓存键
        key_data = {
            "service_name": request.service_name,
            "method_name": request.method_name,
            "params": request.params
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cached_response(self, request: MCPRequest) -> Optional[MCPResponse]:
        # 从缓存获取响应
        cache_key = self._generate_cache_key(request)
        return self._cache.get(cache_key)
    
    def _cache_response(self, request: MCPRequest, response: MCPResponse):
        # 缓存响应
        if response.success:
            cache_key = self._generate_cache_key(request)
            self._cache[cache_key] = response
    
    async def call(self, request: MCPRequest) -> MCPResponse:
        # 检查缓存
        cached_response = self._get_cached_response(request)
        if cached_response:
            logger.debug(f"Using cached response for MCP call: {request.service_name}.{request.method_name}")
            return cached_response
        
        if not self.config.url:
            raise MCPServiceError("MCP service URL is not configured")
        
        await self._ensure_session()
        
        try:
            url = f"{self.config.url}/services/{request.service_name}/{request.method_name}"
            logger.debug(f"Calling MCP service: {url}")
            
            async with self._session.post(
                url,
                json=request.model_dump(),
                timeout=request.timeout
            ) as response:
                if response.status == 401:
                    raise MCPAuthenticationError("Invalid or missing MCP API key")
                
                try:
                    data = await response.json()
                except json.JSONDecodeError:
                    raise MCPResponseError(f"Invalid JSON response from MCP service: {await response.text()}")
                
                if response.status != 200:
                    error_msg = data.get("error", f"HTTP error {response.status}")
                    raise MCPResponseError(error_msg)
                
                # 创建响应对象
                mcp_response = MCPResponse(**data)
                
                # 缓存成功的响应
                self._cache_response(request, mcp_response)
                
                return mcp_response
                
        except aiohttp.ClientError as e:
            raise MCPConnectionError(f"Failed to connect to MCP service: {str(e)}")
        except asyncio.TimeoutError:
            raise MCPConnectionError(f"MCP service request timed out after {request.timeout} seconds")
        except Exception as e:
            if isinstance(e, MCPServiceError):
                raise
            raise MCPServiceError(f"Unexpected error calling MCP service: {str(e)}")

# 创建全局MCP客户端实例
mcp_client = MCPClient()