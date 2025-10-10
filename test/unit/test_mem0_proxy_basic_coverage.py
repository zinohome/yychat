"""
Mem0Proxy基础覆盖率测试
专注于容易覆盖的代码路径
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from core.mem0_proxy import Mem0ChatEngine, Mem0Client, OpenAIClient


class TestMem0ProxyBasicCoverage:
    """Mem0Proxy基础覆盖率测试"""

    def test_mem0_client_get_client(self):
        """测试Mem0Client的get_client方法"""
        with patch('core.mem0_proxy.get_config') as mock_config, \
             patch('core.mem0_proxy.Mem0') as mock_mem0:
            
            # Mock配置
            mock_config.return_value.MEM0_USE_LOCAL = True
            mock_config.return_value.MEM0_API_KEY = "test_key"
            mock_config.return_value.OPENAI_API_KEY = "test_key"
            mock_config.return_value.OPENAI_MODEL = "gpt-4"
            mock_config.return_value.MEMORY_SAVE_MODE = "both"
            mock_config.return_value.CHROMA_COLLECTION_NAME = "test_collection"
            mock_config.return_value.CHROMA_PERSIST_DIRECTORY = "./test_db"
            mock_config.return_value.MEM0_LLM_PROVIDER = "openai"
            mock_config.return_value.MEM0_LLM_CONFIG_MODEL = "gpt-4"
            mock_config.return_value.MEM0_LLM_CONFIG_MAX_TOKENS = 1000
            
            mock_client = Mock()
            mock_mem0.return_value = mock_client
            
            # 创建Mem0Client实例
            client = Mem0Client(mock_config.return_value)
            
            # 测试get_client方法
            result = client.get_client()
            assert result == mock_client

    def test_openai_client_init_success(self):
        """测试OpenAIClient初始化成功"""
        with patch('core.mem0_proxy.get_config') as mock_config, \
             patch('core.mem0_proxy.OpenAI') as mock_openai:
            
            # Mock配置
            mock_config.return_value.OPENAI_API_KEY = "test_key"
            mock_config.return_value.OPENAI_MODEL = "gpt-4"
            
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # 创建OpenAIClient实例
            client = OpenAIClient(mock_config.return_value)
            
            # 验证客户端初始化
            assert hasattr(client, 'client')
            assert client.client == mock_client

    def test_openai_client_init_failure(self):
        """测试OpenAIClient初始化失败"""
        with patch('core.mem0_proxy.get_config') as mock_config, \
             patch('core.mem0_proxy.OpenAI') as mock_openai:
            
            # Mock配置
            mock_config.return_value.OPENAI_API_KEY = "test_key"
            mock_config.return_value.OPENAI_MODEL = "gpt-4"
            
            # Mock OpenAI抛出异常
            mock_openai.side_effect = Exception("OpenAI init error")
            
            # 创建OpenAIClient实例
            client = OpenAIClient(mock_config.return_value)
            
            # 验证异常处理
            assert hasattr(client, 'client')
            assert client.client is None

    @pytest.mark.asyncio
    async def test_mem0_chat_engine_health_check_basic(self):
        """测试Mem0ChatEngine基础健康检查"""
        with patch('core.mem0_proxy.Mem0') as mock_mem0, \
             patch('core.mem0_proxy.OpenAI') as mock_openai, \
             patch('core.mem0_proxy.get_config') as mock_config, \
             patch('core.mem0_proxy.get_async_chat_memory') as mock_memory:
            
            # Mock配置
            mock_config.return_value.MEM0_USE_LOCAL = True
            mock_config.return_value.MEM0_API_KEY = "test_key"
            mock_config.return_value.OPENAI_API_KEY = "test_key"
            mock_config.return_value.OPENAI_MODEL = "gpt-4"
            mock_config.return_value.MEMORY_SAVE_MODE = "both"
            mock_config.return_value.CHROMA_COLLECTION_NAME = "test_collection"
            mock_config.return_value.CHROMA_PERSIST_DIRECTORY = "./test_db"
            mock_config.return_value.MEM0_LLM_PROVIDER = "openai"
            mock_config.return_value.MEM0_LLM_CONFIG_MODEL = "gpt-4"
            mock_config.return_value.MEM0_LLM_CONFIG_MAX_TOKENS = 1000
            
            # Mock客户端
            mock_mem0_client = Mock()
            mock_mem0.return_value = mock_mem0_client
            mock_openai_client = Mock()
            mock_openai.return_value = mock_openai_client
            
            # Mock异步内存
            mock_async_memory = Mock()
            mock_memory.return_value = mock_async_memory
            
            # 创建Mem0ChatEngine实例
            engine = Mem0ChatEngine()
            
            # 执行健康检查
            result = await engine.health_check()
            
            # 验证结果包含基本字段
            assert "healthy" in result
            assert "timestamp" in result
            assert "details" in result

    @pytest.mark.asyncio
    async def test_mem0_chat_engine_get_engine_info(self):
        """测试Mem0ChatEngine获取引擎信息"""
        with patch('core.mem0_proxy.Mem0') as mock_mem0, \
             patch('core.mem0_proxy.OpenAI') as mock_openai, \
             patch('core.mem0_proxy.get_config') as mock_config, \
             patch('core.mem0_proxy.get_async_chat_memory') as mock_memory:
            
            # Mock配置
            mock_config.return_value.MEM0_USE_LOCAL = True
            mock_config.return_value.MEM0_API_KEY = "test_key"
            mock_config.return_value.OPENAI_API_KEY = "test_key"
            mock_config.return_value.OPENAI_MODEL = "gpt-4"
            mock_config.return_value.MEMORY_SAVE_MODE = "both"
            mock_config.return_value.CHROMA_COLLECTION_NAME = "test_collection"
            mock_config.return_value.CHROMA_PERSIST_DIRECTORY = "./test_db"
            mock_config.return_value.MEM0_LLM_PROVIDER = "openai"
            mock_config.return_value.MEM0_LLM_CONFIG_MODEL = "gpt-4"
            mock_config.return_value.MEM0_LLM_CONFIG_MAX_TOKENS = 1000
            
            # Mock客户端
            mock_mem0_client = Mock()
            mock_mem0.return_value = mock_mem0_client
            mock_openai_client = Mock()
            mock_openai.return_value = mock_openai_client
            
            # Mock异步内存
            mock_async_memory = Mock()
            mock_memory.return_value = mock_async_memory
            
            # 创建Mem0ChatEngine实例
            engine = Mem0ChatEngine()
            
            # 获取引擎信息
            info = await engine.get_engine_info()
            
            # 验证信息包含基本字段
            assert "name" in info
            assert "version" in info
            assert "status" in info

    @pytest.mark.asyncio
    async def test_mem0_chat_engine_get_supported_personalities(self):
        """测试Mem0ChatEngine获取支持的人格"""
        with patch('core.mem0_proxy.Mem0') as mock_mem0, \
             patch('core.mem0_proxy.OpenAI') as mock_openai, \
             patch('core.mem0_proxy.get_config') as mock_config, \
             patch('core.mem0_proxy.get_async_chat_memory') as mock_memory:
            
            # Mock配置
            mock_config.return_value.MEM0_USE_LOCAL = True
            mock_config.return_value.MEM0_API_KEY = "test_key"
            mock_config.return_value.OPENAI_API_KEY = "test_key"
            mock_config.return_value.OPENAI_MODEL = "gpt-4"
            mock_config.return_value.MEMORY_SAVE_MODE = "both"
            mock_config.return_value.CHROMA_COLLECTION_NAME = "test_collection"
            mock_config.return_value.CHROMA_PERSIST_DIRECTORY = "./test_db"
            mock_config.return_value.MEM0_LLM_PROVIDER = "openai"
            mock_config.return_value.MEM0_LLM_CONFIG_MODEL = "gpt-4"
            mock_config.return_value.MEM0_LLM_CONFIG_MAX_TOKENS = 1000
            
            # Mock客户端
            mock_mem0_client = Mock()
            mock_mem0.return_value = mock_mem0_client
            mock_openai_client = Mock()
            mock_openai.return_value = mock_openai_client
            
            # Mock异步内存
            mock_async_memory = Mock()
            mock_memory.return_value = mock_async_memory
            
            # 创建Mem0ChatEngine实例
            engine = Mem0ChatEngine()
            
            # 获取支持的人格
            personalities = await engine.get_supported_personalities()
            
            # 验证返回列表
            assert isinstance(personalities, list)

    @pytest.mark.asyncio
    async def test_mem0_chat_engine_get_available_tools(self):
        """测试Mem0ChatEngine获取可用工具"""
        with patch('core.mem0_proxy.Mem0') as mock_mem0, \
             patch('core.mem0_proxy.OpenAI') as mock_openai, \
             patch('core.mem0_proxy.get_config') as mock_config, \
             patch('core.mem0_proxy.get_async_chat_memory') as mock_memory:
            
            # Mock配置
            mock_config.return_value.MEM0_USE_LOCAL = True
            mock_config.return_value.MEM0_API_KEY = "test_key"
            mock_config.return_value.OPENAI_API_KEY = "test_key"
            mock_config.return_value.OPENAI_MODEL = "gpt-4"
            mock_config.return_value.MEMORY_SAVE_MODE = "both"
            mock_config.return_value.CHROMA_COLLECTION_NAME = "test_collection"
            mock_config.return_value.CHROMA_PERSIST_DIRECTORY = "./test_db"
            mock_config.return_value.MEM0_LLM_PROVIDER = "openai"
            mock_config.return_value.MEM0_LLM_CONFIG_MODEL = "gpt-4"
            mock_config.return_value.MEM0_LLM_CONFIG_MAX_TOKENS = 1000
            
            # Mock客户端
            mock_mem0_client = Mock()
            mock_mem0.return_value = mock_mem0_client
            mock_openai_client = Mock()
            mock_openai.return_value = mock_openai_client
            
            # Mock异步内存
            mock_async_memory = Mock()
            mock_memory.return_value = mock_async_memory
            
            # 创建Mem0ChatEngine实例
            engine = Mem0ChatEngine()
            
            # 获取可用工具
            tools = await engine.get_available_tools()
            
            # 验证返回列表
            assert isinstance(tools, list)
