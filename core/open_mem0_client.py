import hashlib
import logging
import os
from typing import Any, Dict, List, Optional

import httpx
import requests

from mem0.client.main import MemoryClient, AsyncMemoryClient
from mem0.client.project import AsyncProject, Project
from mem0.client.utils import api_error_handler
from mem0.memory.setup import get_user_id
from mem0.memory.telemetry import capture_client_event

logger = logging.getLogger(__name__)


class OpenMemoryClient(MemoryClient):
    """自定义的同步Mem0客户端，适配本地openmemory服务器

    继承自Mem0的MemoryClient，添加了默认的org_id、project_id和user_email，
    并重写了_validate_api_key方法以适配本地服务器的认证方式。
    """
    
    # 默认值常量
    DEFAULT_ORG_ID = "yyTech"
    DEFAULT_PROJECT_ID = "9a35980c-e2d0-4aeb-9cfb-d7b8f116e712"
    DEFAULT_USER_EMAIL = "yyassistant@yytech.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        host: Optional[str] = None,
        org_id: Optional[str] = None,
        project_id: Optional[str] = None,
        client: Optional[httpx.Client] = None,
    ):
        """初始化OpenMemoryClient

        Args:
            api_key: API密钥，如果未提供将尝试从环境变量MEM0_API_KEY获取
            host: API主机地址
            org_id: 组织ID，默认为"yyTech"
            project_id: 项目ID，默认为"9a35980c-e2d0-4aeb-9cfb-d7b8f116e712"
            client: 自定义httpx.Client实例
        """
        # 设置默认的org_id和project_id
        org_id = org_id or self.DEFAULT_ORG_ID
        project_id = project_id or self.DEFAULT_PROJECT_ID
        
        # 调用父类初始化，但不执行_validate_api_key
        # 我们将在后面自己处理验证
        self.api_key = api_key or os.getenv("MEM0_API_KEY")
        self.host = host or "https://api.mem0.ai"
        self.org_id = org_id
        self.project_id = project_id
        self.user_id = get_user_id()

        if not self.api_key:
            raise ValueError("Mem0 API Key not provided. Please provide an API Key.")

        # Create MD5 hash of API key for user_id
        self.user_id = hashlib.md5(self.api_key.encode()).hexdigest()

        if client is not None:
            self.client = client
            # Ensure the client has the correct base_url and headers
            self.client.base_url = httpx.URL(self.host)
            self.client.headers.update(
                {
                    "Authorization": f"Token {self.api_key}",
                    "Mem0-User-ID": self.user_id,
                }
            )
        else:
            self.client = httpx.Client(
                base_url=self.host,
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Mem0-User-ID": self.user_id,
                },
                timeout=300,
            )
        
        # 使用我们自己的验证方法
        self.user_email = self._validate_api_key()

        # 初始化项目管理器
        self.project = Project(
            client=self.client,
            org_id=self.org_id,
            project_id=self.project_id,
            user_email=self.user_email,
        )

        capture_client_event("client.init", self, {"sync_type": "sync"})

    def _validate_api_key(self):
        """验证API密钥，适配本地openmemory服务器

        访问/api/v1/auth/me端点，验证返回结果的user_id是否和用户ID相同。
        如果相同，则将默认email赋值给用户。
        
        Returns:
            str: 用户邮箱地址
        """
        try:
            # 访问本地服务器的认证端点
            response = self.client.get("/api/v1/auth/me")
            response.raise_for_status()
            
            data = response.json()
            
            # 验证返回的user_id是否与当前用户ID匹配
            if data.get("user_id") != self.user_id:
                logger.warning(f"User ID mismatch: expected {self.user_id}, got {data.get('user_id')}")
            
            # 不管怎样都返回默认邮箱
            return self.DEFAULT_USER_EMAIL
            
        except httpx.HTTPStatusError as e:
            try:
                error_data = e.response.json()
                error_message = error_data.get("detail", str(e))
            except Exception:
                error_message = str(e)
            logger.error(f"API key validation failed: {error_message}")
            # 即使验证失败，也返回默认邮箱以便继续使用
            return self.DEFAULT_USER_EMAIL
        except Exception as e:
            logger.error(f"Unexpected error during API key validation: {str(e)}")
            # 发生任何异常都返回默认邮箱
            return self.DEFAULT_USER_EMAIL

    def _prepare_params(self, kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """准备API请求的查询参数

        重写父类方法，确保org_id和project_id始终被设置
        
        Args:
            kwargs: 要包含在参数中的关键字参数
        
        Returns:
            Dict[str, Any]: 包含准备好的参数的字典
        """
        if kwargs is None:
            kwargs = {}

        # 始终添加org_id和project_id
        kwargs["org_id"] = self.org_id
        kwargs["project_id"] = self.project_id

        return {k: v for k, v in kwargs.items() if v is not None}


class AsyncOpenMemoryClient(AsyncMemoryClient):
    """自定义的异步Mem0客户端，适配本地openmemory服务器

    继承自Mem0的AsyncMemoryClient，添加了默认的org_id、project_id和user_email，
    并重写了_validate_api_key方法以适配本地服务器的认证方式。
    """
    
    # 默认值常量
    DEFAULT_ORG_ID = "yyTech"
    DEFAULT_PROJECT_ID = "9a35980c-e2d0-4aeb-9cfb-d7b8f116e712"
    DEFAULT_USER_EMAIL = "yyassistant@yytech.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        host: Optional[str] = None,
        org_id: Optional[str] = None,
        project_id: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ):
        """初始化AsyncOpenMemoryClient

        Args:
            api_key: API密钥，如果未提供将尝试从环境变量MEM0_API_KEY获取
            host: API主机地址
            org_id: 组织ID，默认为"yyTech"
            project_id: 项目ID，默认为"9a35980c-e2d0-4aeb-9cfb-d7b8f116e712"
            client: 自定义httpx.AsyncClient实例
        """
        # 设置默认的org_id和project_id
        org_id = org_id or self.DEFAULT_ORG_ID
        project_id = project_id or self.DEFAULT_PROJECT_ID
        
        # 调用父类初始化，但不执行_validate_api_key
        # 我们将在后面自己处理验证
        self.api_key = api_key or os.getenv("MEM0_API_KEY")
        self.host = host or "https://api.mem0.ai"
        self.org_id = org_id
        self.project_id = project_id
        self.user_id = get_user_id()

        if not self.api_key:
            raise ValueError("Mem0 API Key not provided. Please provide an API Key.")

        # Create MD5 hash of API key for user_id
        self.user_id = hashlib.md5(self.api_key.encode()).hexdigest()

        if client is not None:
            self.async_client = client
            # Ensure the client has the correct base_url and headers
            self.async_client.base_url = httpx.URL(self.host)
            self.async_client.headers.update(
                {
                    "Authorization": f"Token {self.api_key}",
                    "Mem0-User-ID": self.user_id,
                }
            )
        else:
            self.async_client = httpx.AsyncClient(
                base_url=self.host,
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Mem0-User-ID": self.user_id,
                },
                timeout=300,
            )
        
        # 使用我们自己的验证方法
        self.user_email = self._validate_api_key()

        # 初始化项目管理器
        self.project = AsyncProject(
            client=self.async_client,
            org_id=self.org_id,
            project_id=self.project_id,
            user_email=self.user_email,
        )

        capture_client_event("client.init", self, {"sync_type": "async"})

    def _validate_api_key(self):
        """验证API密钥，适配本地openmemory服务器

        访问/api/v1/auth/me端点，验证返回结果的user_id是否和用户ID相同。
        如果相同，则将默认email赋值给用户。
        
        Returns:
            str: 用户邮箱地址
        """
        try:
            # 注意：在异步客户端中使用同步请求来验证API密钥
            # 这是为了保持与父类行为一致
            response = requests.get(
                f"{self.host}/api/v1/auth/me",
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Mem0-User-ID": self.user_id,
                }
            )
            response.raise_for_status()
            
            data = response.json()
            
            # 验证返回的user_id是否与当前用户ID匹配
            if data.get("user_id") != self.user_id:
                logger.warning(f"User ID mismatch: expected {self.user_id}, got {data.get('user_id')}")
            
            # 不管怎样都返回默认邮箱
            return self.DEFAULT_USER_EMAIL
            
        except requests.exceptions.HTTPError as e:
            try:
                error_data = e.response.json()
                error_message = error_data.get("detail", str(e))
            except Exception:
                error_message = str(e)
            logger.error(f"API key validation failed: {error_message}")
            # 即使验证失败，也返回默认邮箱以便继续使用
            return self.DEFAULT_USER_EMAIL
        except Exception as e:
            logger.error(f"Unexpected error during API key validation: {str(e)}")
            # 发生任何异常都返回默认邮箱
            return self.DEFAULT_USER_EMAIL

    def _prepare_params(self, kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """准备API请求的查询参数

        重写父类方法，确保org_id和project_id始终被设置
        
        Args:
            kwargs: 要包含在参数中的关键字参数
        
        Returns:
            Dict[str, Any]: 包含准备好的参数的字典
        """
        if kwargs is None:
            kwargs = {}

        # 始终添加org_id和project_id
        kwargs["org_id"] = self.org_id
        kwargs["project_id"] = self.project_id

        return {k: v for k, v in kwargs.items() if v is not None}