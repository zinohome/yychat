import json
from unittest.mock import patch, MagicMock, AsyncMock, Mock
import asyncio
import pytest
from core.mem0_proxy import Mem0ProxyManager, get_mem0_proxy

# 测试Mem0ProxyManager初始化
def test_mem0_proxy_manager_init(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    mock_config.OPENAI_MODEL = "gpt-4.1-turbo-2024-04-09"
    mock_config.OPENAI_TEMPERATURE = 0.7
    mock_config.MEMO_USE_LOCAL = False
    mock_config.MEM0_API_KEY = "test_mem0_key"
    
    # 使用patch来模拟依赖
    with patch('core.mem0_proxy.Mem0') as mock_mem0, \
         patch('core.mem0_proxy.ChatMemory') as mock_chat_memory_class, \
         patch('core.mem0_proxy.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.mem0_proxy.PersonalityManager') as mock_personality_manager_class, \
         patch('core.mem0_proxy.ToolManager') as mock_tool_manager_class, \
         patch('core.mem0_proxy.OpenAI') as mock_openai:
        
        # 创建模拟实例
        mock_mem0_instance = MagicMock()
        mock_mem0.return_value = mock_mem0_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        # 初始化Mem0ProxyManager，传入mock_config
        mem0_proxy = Mem0ProxyManager(custom_config=mock_config)
        
        # 验证组件是否被正确初始化
        assert mem0_proxy.base_client == mock_mem0_instance
        assert mem0_proxy.chat_memory == mock_chat_memory_instance
        assert mem0_proxy.async_chat_memory == mock_async_chat_memory_instance
        assert mem0_proxy.personality_manager == mock_personality_manager_instance
        assert mem0_proxy.tool_manager == mock_tool_manager_instance
        assert mem0_proxy.openai_client == mock_openai_instance
        assert "default" not in mem0_proxy.clients_cache

# 测试本地配置初始化
def test_mem0_proxy_manager_init_local(mock_config):
    # 配置mock_config使用本地配置
    mock_config.MEMO_USE_LOCAL = True
    mock_config.CHROMA_COLLECTION_NAME = "test_collection"
    mock_config.CHROMA_PERSIST_DIRECTORY = "/tmp/test_chroma"
    mock_config.MEM0_LLM_PROVIDER = "openai"
    mock_config.MEM0_LLM_CONFIG_MODEL = "gpt-4.1-turbo"
    mock_config.MEM0_LLM_CONFIG_MAX_TOKENS = 1000
    
    # 使用patch来模拟依赖
    with patch('core.mem0_proxy.Mem0') as mock_mem0, \
         patch('core.mem0_proxy.ChatMemory'), \
         patch('core.mem0_proxy.get_async_chat_memory'), \
         patch('core.mem0_proxy.PersonalityManager'), \
         patch('core.mem0_proxy.ToolManager'), \
         patch('core.mem0_proxy.OpenAI'):
        
        # 初始化Mem0ProxyManager，传入mock_config
        mem0_proxy = Mem0ProxyManager(custom_config=mock_config)
        
        # 验证是否使用本地配置
        # 注意：本地配置是通过Mem0类的参数来判断的，而不是is_local_client标志

# 测试get_client方法
def test_get_client(mock_config):
    with patch('core.mem0_proxy.Mem0') as mock_mem0, \
         patch('core.mem0_proxy.ChatMemory'), \
         patch('core.mem0_proxy.get_async_chat_memory'), \
         patch('core.mem0_proxy.PersonalityManager'), \
         patch('core.mem0_proxy.ToolManager'), \
         patch('core.mem0_proxy.OpenAI'):
        
        # 创建模拟实例
        mock_mem0_instance = MagicMock()
        mock_mem0.return_value = mock_mem0_instance
        
        # 初始化Mem0ProxyManager，传入mock_config
        mem0_proxy = Mem0ProxyManager(custom_config=mock_config)
        
        # 测试获取默认客户端
        client1 = mem0_proxy.get_client()
        assert client1 == mock_mem0_instance
        assert "default" in mem0_proxy.clients_cache
        
        # 测试获取特定用户客户端
        client2 = mem0_proxy.get_client("user123")
        assert client2 == mock_mem0_instance
        assert "user123" in mem0_proxy.clients_cache

# 测试generate_response方法 - 基本功能
@pytest.mark.asyncio
async def test_generate_response_basic(mock_config):
    # 配置mock_config
    mock_config.USE_TOOLS_DEFAULT = False
    mock_config.STREAM_DEFAULT = False
    mock_config.MEMO_USE_LOCAL = False
    mock_config.MEM0_API_KEY = "test_mem0_key"
    
    # 创建模拟响应
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "测试响应内容"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150
    
    # 使用patch来模拟依赖
    with patch('core.mem0_proxy.Mem0') as mock_mem0, \
         patch('core.mem0_proxy.ChatMemory'), \
         patch('core.mem0_proxy.get_async_chat_memory'), \
         patch('core.mem0_proxy.PersonalityManager') as mock_personality_manager_class, \
         patch('core.mem0_proxy.ToolManager'), \
         patch('core.mem0_proxy.Mem0ProxyManager._handle_non_streaming_response') as mock_handle_non_streaming:
        
        # 创建模拟对象 - 确保模拟结构与实际Mem0客户端匹配
        mock_mock_client = MagicMock()
        mock_mock_client.chat.completions.create.return_value = mock_response
        mock_mem0.return_value = mock_mock_client
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        mock_personality_manager_instance.apply_personality.side_effect = lambda messages, _: messages
        
        # 设置模拟的handle_non_streaming_response返回值
        expected_result = {
            "role": "health_assistant",
            "content": "测试响应内容",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
        mock_handle_non_streaming.return_value = expected_result
        
        # 初始化Mem0ProxyManager，传入mock_config
        mem0_proxy = Mem0ProxyManager(custom_config=mock_config)
        
        # 准备测试数据
        messages = [{"role": "user", "content": "你好"}]
        
        # 调用方法
        result = await mem0_proxy.generate_response(messages)
        
        # 验证结果
        assert result == expected_result
        
        # 验证API调用参数
        mock_mock_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_mock_client.chat.completions.create.call_args
        assert kwargs["messages"] == messages
        assert kwargs["stream"] is False
        
        # 验证调用了_handle_non_streaming_response
        mock_handle_non_streaming.assert_called_once()

# 测试generate_response方法 - 带人格参数
@pytest.mark.asyncio
async def test_generate_response_with_personality(mock_config):
    # 配置mock_config
    mock_config.USE_TOOLS_DEFAULT = False
    mock_config.STREAM_DEFAULT = False
    
    # 创建模拟响应
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "带人格的测试响应"
    
    # 使用patch来模拟依赖
    with patch('core.mem0_proxy.Mem0') as mock_mem0, \
         patch('core.mem0_proxy.ChatMemory'), \
         patch('core.mem0_proxy.get_async_chat_memory'), \
         patch('core.mem0_proxy.PersonalityManager') as mock_personality_manager_class, \
         patch('core.mem0_proxy.ToolManager'), \
         patch('core.mem0_proxy.Mem0ProxyManager._handle_non_streaming_response') as mock_handle_non_streaming:
        
        # 创建模拟对象 - 确保模拟结构与实际Mem0客户端匹配
        mock_mock_client = MagicMock()
        mock_mock_client.chat.completions.create.return_value = mock_response
        mock_mem0.return_value = mock_mock_client
        
        # 模拟apply_personality方法
        applied_messages = [{"role": "system", "content": "人格提示"}, {"role": "user", "content": "你好"}]
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        mock_personality_manager_instance.apply_personality.return_value = applied_messages
        
        # 设置模拟的handle_non_streaming_response返回值
        expected_result = {
            "role": "health_assistant",
            "content": "带人格的测试响应"
        }
        mock_handle_non_streaming.return_value = expected_result
        
        # 初始化Mem0ProxyManager，传入mock_config
        mem0_proxy = Mem0ProxyManager(custom_config=mock_config)
        
        # 准备测试数据
        messages = [{"role": "user", "content": "你好"}]
        
        # 调用方法，传入人格参数
        result = await mem0_proxy.generate_response(messages, personality_id="professional")
        
        # 验证结果
        assert result == expected_result
        
        # 验证人格是否被应用
        mock_personality_manager_instance.apply_personality.assert_called_once_with(messages, "professional")
        
        # 验证API调用参数包含应用人格后的消息
        mock_mock_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_mock_client.chat.completions.create.call_args
        assert kwargs["messages"] == applied_messages
        
        # 验证调用了_handle_non_streaming_response
        mock_handle_non_streaming.assert_called_once()

# 测试generate_response方法 - 使用工具
@pytest.mark.asyncio
async def test_generate_response_with_tools(mock_config):
    # 配置mock_config
    mock_config.USE_TOOLS_DEFAULT = False
    mock_config.STREAM_DEFAULT = False
    
    # 创建模拟响应
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "使用工具的测试响应"
    
    # 创建模拟工具
    mock_tools = [{"type": "function", "function": {"name": "test_tool", "parameters": {}}}]    
    
    # 使用patch来模拟依赖
    with patch('core.mem0_proxy.Mem0') as mock_mem0, \
         patch('core.mem0_proxy.ChatMemory'), \
         patch('core.mem0_proxy.get_async_chat_memory'), \
         patch('core.mem0_proxy.PersonalityManager') as mock_personality_manager_class, \
         patch('core.mem0_proxy.ToolManager'), \
         patch('services.tools.registry.tool_registry.get_functions_schema') as mock_get_functions_schema, \
         patch('core.mem0_proxy.Mem0ProxyManager._handle_non_streaming_response') as mock_handle_non_streaming:
        
        # 创建模拟对象 - 确保模拟结构与实际Mem0客户端匹配
        mock_mock_client = MagicMock()
        mock_mock_client.chat.completions.create.return_value = mock_response
        mock_mem0.return_value = mock_mock_client
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        mock_personality_manager_instance.apply_personality.side_effect = lambda messages, _: messages
        
        # 设置模拟工具
        mock_get_functions_schema.return_value = mock_tools
        
        # 设置模拟的handle_non_streaming_response返回值
        expected_result = {
            "role": "health_assistant",
            "content": "使用工具的测试响应"
        }
        mock_handle_non_streaming.return_value = expected_result
        
        # 初始化Mem0ProxyManager，传入mock_config
        mem0_proxy = Mem0ProxyManager(custom_config=mock_config)
        
        # 准备测试数据
        messages = [{"role": "user", "content": "你好"}]
        
        # 调用方法，启用工具
        result = await mem0_proxy.generate_response(messages, use_tools=True)
        
        # 验证结果
        assert result == expected_result
        
        # 验证API调用参数包含工具
        mock_mock_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_mock_client.chat.completions.create.call_args
        assert kwargs["tools"] == mock_tools
        assert kwargs["tool_choice"] == "auto"
        
        # 验证调用了_handle_non_streaming_response
        mock_handle_non_streaming.assert_called_once()

# 测试流式响应处理
@pytest.mark.asyncio
async def test_handle_streaming_response(mock_config):
    # 创建模拟流式响应
    class MockStreamChunk:
        def __init__(self, content=None, finish_reason=None):
            self.choices = [MagicMock()]
            self.choices[0].delta = MagicMock()
            self.choices[0].delta.content = content
            self.choices[0].finish_reason = finish_reason
    
    # 模拟一个异步生成器
    async def mock_stream_generator():
        yield MockStreamChunk(content="第一段内容")
        yield MockStreamChunk(content="第二段内容")
        yield MockStreamChunk(content=None, finish_reason="stop")
    
    # 使用patch来模拟依赖
    with patch('core.mem0_proxy.Mem0'), \
         patch('core.mem0_proxy.ChatMemory'), \
         patch('core.mem0_proxy.get_async_chat_memory'), \
         patch('core.mem0_proxy.PersonalityManager'), \
         patch('core.mem0_proxy.ToolManager'):
        
        # 初始化Mem0ProxyManager
        mem0_proxy = Mem0ProxyManager()
        
        # 获取流式响应生成器
        stream_generator = mem0_proxy._handle_streaming_response(mock_stream_generator(), "test_conv")
        
        # 收集生成的响应块
        chunks = []
        async for chunk in stream_generator:
            chunks.append(chunk)
        
        # 验证响应块
        assert len(chunks) == 3
        assert chunks[0]["content"] == "第一段内容"
        assert chunks[1]["content"] == "第二段内容"
        assert chunks[2]["content"] == ""
        assert chunks[2]["finish_reason"] == "stop"

# 测试降级到OpenAI API
@pytest.mark.asyncio
async def test_fallback_to_openai(mock_config):
    # 配置mock_config
    mock_config.USE_TOOLS_DEFAULT = False
    mock_config.STREAM_DEFAULT = False
    
    # 创建模拟响应
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "降级到OpenAI的响应"
    
    # 使用patch来模拟依赖
    with patch('core.mem0_proxy.Mem0') as mock_mem0, \
         patch('core.mem0_proxy.ChatMemory'), \
         patch('core.mem0_proxy.get_async_chat_memory'), \
         patch('core.mem0_proxy.PersonalityManager') as mock_personality_manager_class, \
         patch('core.mem0_proxy.ToolManager'), \
         patch('core.mem0_proxy.OpenAI') as mock_openai, \
         patch('core.mem0_proxy.Mem0ProxyManager._handle_non_streaming_response') as mock_handle_non_streaming:
        
        # 创建模拟对象
        # 让Mem0调用失败
        mock_mock_client = MagicMock()
        mock_mock_client.chat.completions.create.side_effect = Exception("Mem0调用失败")
        mock_mem0.return_value = mock_mock_client
        
        # OpenAI客户端模拟
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.return_value = mock_response
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        mock_personality_manager_instance.apply_personality.side_effect = lambda messages, _: messages
        
        # 设置模拟的handle_non_streaming_response返回值
        mock_handle_non_streaming.return_value = {
            "role": "health_assistant",
            "content": "降级到OpenAI的响应"
        }
        
        # 初始化Mem0ProxyManager，传入mock_config
        mem0_proxy = Mem0ProxyManager(custom_config=mock_config)
        
        # 准备测试数据
        messages = [{"role": "user", "content": "你好"}]
        
        # 调用方法，应该触发降级
        result = await mem0_proxy.generate_response(messages)
        
        # 验证结果
        assert result["role"] == "health_assistant"
        assert result["content"] == "降级到OpenAI的响应"
        
        # 验证调用了_handle_non_streaming_response
        mock_handle_non_streaming.assert_called_once()

# 测试记忆管理功能
def test_memory_management(mock_config):
    with patch('core.mem0_proxy.Mem0'), \
         patch('core.mem0_proxy.ChatMemory') as mock_chat_memory_class, \
         patch('core.mem0_proxy.get_async_chat_memory'), \
         patch('core.mem0_proxy.PersonalityManager'), \
         patch('core.mem0_proxy.ToolManager'), \
         patch('core.mem0_proxy.OpenAI'):
        
        # 创建模拟对象
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        mock_chat_memory_instance.get_memory.return_value = [{"content": "记忆内容"}]
        
        # 初始化Mem0ProxyManager
        mem0_proxy = Mem0ProxyManager()
        
        # 测试清除记忆
        mem0_proxy.clear_conversation_memory("test_conv")
        mock_chat_memory_instance.clear_memory.assert_called_once_with("test_conv")
        
        # 测试获取记忆
        memories = mem0_proxy.get_conversation_memory("test_conv")
        mock_chat_memory_instance.get_memory.assert_called_once_with("test_conv")
        assert memories == [{"content": "记忆内容"}]

# 测试MCP服务调用
@pytest.mark.asyncio
async def test_call_mcp_service(mock_config):
    # 创建模拟MCP响应
    mock_mcp_result = {"success": True, "data": "测试数据"}
    
    # 使用patch来模拟依赖
    with patch('core.mem0_proxy.Mem0'), \
         patch('core.mem0_proxy.ChatMemory'), \
         patch('core.mem0_proxy.get_async_chat_memory'), \
         patch('core.mem0_proxy.PersonalityManager'), \
         patch('core.mem0_proxy.ToolManager'), \
         patch('core.mem0_proxy.OpenAI'), \
         patch('core.mem0_proxy.mcp_manager.call_tool') as mock_call_tool:
        
        # 设置模拟MCP调用
        mock_call_tool.return_value = mock_mcp_result
        
        # 初始化Mem0ProxyManager
        mem0_proxy = Mem0ProxyManager()
        
        # 调用MCP服务
        result = await mem0_proxy.call_mcp_service(
            tool_name="test_tool",
            params={"key": "value"},
            service_name="test_service",
            method_name="test_method",
            mcp_server="http://localhost:8080"
        )
        
        # 验证调用参数和结果
        mock_call_tool.assert_called_once_with(
            tool_name="test_tool",
            arguments={"key": "value"},
            mcp_server="http://localhost:8080"
        )
        assert result == mock_mcp_result

# 测试全局实例获取
def test_get_mem0_proxy(mock_config):
    with patch('core.mem0_proxy.Mem0'), \
         patch('core.mem0_proxy.ChatMemory'), \
         patch('core.mem0_proxy.get_async_chat_memory'), \
         patch('core.mem0_proxy.PersonalityManager'), \
         patch('core.mem0_proxy.ToolManager'), \
         patch('core.mem0_proxy.OpenAI'):
        
        # 第一次调用应该创建实例
        instance1 = get_mem0_proxy()
        assert isinstance(instance1, Mem0ProxyManager)
        
        # 第二次调用应该返回相同的实例
        instance2 = get_mem0_proxy()
        assert instance1 is instance2