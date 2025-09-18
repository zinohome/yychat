import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock, Mock
import asyncio
from core.chat_engine import ChatEngine

# 测试ChatEngine初始化
def test_chat_engine_init(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    mock_config.OPENAI_MODEL = "gpt-4.1-turbo-2024-04-09"
    mock_config.OPENAI_TEMPERATURE = 0.7
    mock_config.OPENAI_MAX_TOKENS = 16384
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class:
        
        # 创建模拟实例
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 验证组件是否被正确初始化
        assert chat_engine.client == mock_openai_instance
        assert chat_engine.chat_memory == mock_chat_memory_instance
        assert chat_engine.async_chat_memory == mock_async_chat_memory_instance
        assert chat_engine.personality_manager == mock_personality_manager_instance
        assert chat_engine.tool_manager == mock_tool_manager_instance

# 测试generate_response方法 - 基本功能
@pytest.mark.asyncio
async def test_generate_response_basic(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    mock_config.OPENAI_MODEL = "gpt-4.1-turbo-2024-04-09"
    mock_config.OPENAI_TEMPERATURE = 0.7
    mock_config.OPENAI_MAX_TOKENS = 16384
    
    # 创建模拟响应
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "测试响应内容"
    mock_response.model = "gpt-4.1-turbo-2024-04-09"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class, \
         patch('core.chat_engine.tool_registry.get_functions_schema') as mock_get_functions_schema, \
         patch('asyncio.create_task') as mock_create_task:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.return_value = mock_response
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        mock_chat_memory_instance.get_relevant_memory.return_value = []
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        mock_personality_manager_instance.apply_personality.side_effect = lambda messages, _: messages
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        mock_get_functions_schema.return_value = []
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 准备测试数据
        messages = [{"role": "user", "content": "你好"}]
        
        # 调用方法
        result = await chat_engine.generate_response(messages)
        
        # 验证结果
        assert result["role"] == "assistant"
        assert result["content"] == "测试响应内容"
        assert result["model"] == "gpt-4.1-turbo-2024-04-09"
        assert result["usage"]["prompt_tokens"] == 100
        assert result["usage"]["completion_tokens"] == 50
        assert result["usage"]["total_tokens"] == 150
        
        # 验证异步任务被创建用于保存消息
        mock_create_task.assert_called_once()

# 测试generate_response方法 - 添加记忆
@pytest.mark.asyncio
async def test_generate_response_with_memory(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    mock_config.OPENAI_MODEL = "gpt-4.1-turbo-2024-04-09"
    mock_config.OPENAI_TEMPERATURE = 0.7
    mock_config.OPENAI_MAX_TOKENS = 16384  # 设置足够大的max_tokens，确保能添加记忆
    
    # 创建模拟响应
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "带记忆的测试响应"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class, \
         patch('core.chat_engine.tool_registry.get_functions_schema') as mock_get_functions_schema:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.return_value = mock_response
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        mock_chat_memory_instance.get_relevant_memory.return_value = ["记忆内容1", "记忆内容2"]
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        mock_personality_manager_instance.apply_personality.side_effect = lambda messages, _: messages
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        mock_get_functions_schema.return_value = []
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 准备测试数据
        messages = [{"role": "user", "content": "简短查询"}]
        
        # 调用方法
        await chat_engine.generate_response(messages, conversation_id="test_conv")
        
        # 验证API调用参数中包含记忆
        args, kwargs = mock_openai_instance.chat.completions.create.call_args
        assert any(msg["role"] == "system" and "参考记忆" in msg["content"] for msg in kwargs["messages"])

# 测试generate_response方法 - 避免超出token限制
@pytest.mark.asyncio
async def test_generate_response_avoid_token_limit(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    mock_config.OPENAI_MODEL = "gpt-4.1-turbo-2024-04-09"
    mock_config.OPENAI_TEMPERATURE = 0.7
    mock_config.OPENAI_MAX_TOKENS = 100  # 设置很小的max_tokens，触发token限制检查
    
    # 创建模拟响应
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "测试响应"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class, \
         patch('core.chat_engine.tool_registry.get_functions_schema') as mock_get_functions_schema, \
         patch('core.chat_engine.logger.warning') as mock_logger_warning:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.return_value = mock_response
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        # 提供一个很长的记忆内容，触发token限制
        mock_chat_memory_instance.get_relevant_memory.return_value = ["x" * 1000]
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        mock_personality_manager_instance.apply_personality.side_effect = lambda messages, _: messages
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        mock_get_functions_schema.return_value = []
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 准备测试数据
        messages = [{"role": "user", "content": "简短查询"}]
        
        # 调用方法
        await chat_engine.generate_response(messages, conversation_id="test_conv")
        
        # 验证日志警告被记录
        mock_logger_warning.assert_called_once()
        assert "避免超出模型token限制" in mock_logger_warning.call_args[0][0]

# 测试generate_response方法 - 应用人格和工具过滤
@pytest.mark.asyncio
async def test_generate_response_with_personality(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    mock_config.OPENAI_MODEL = "gpt-4.1-turbo-2024-04-09"
    mock_config.OPENAI_TEMPERATURE = 0.7
    
    # 创建模拟响应
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = "带人格的测试响应"
    
    # 模拟人格对象
    mock_personality = MagicMock()
    mock_personality.allowed_tools = [{"tool_name": "allowed_tool"}]
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class, \
         patch('core.chat_engine.tool_registry.get_functions_schema') as mock_get_functions_schema:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.return_value = mock_response
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        mock_chat_memory_instance.get_relevant_memory.return_value = []
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        mock_personality_manager_instance.apply_personality.side_effect = lambda messages, _: messages
        mock_personality_manager_instance.get_personality.return_value = mock_personality
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 模拟工具schema列表，包含allowed_tool和其他工具
        mock_get_functions_schema.return_value = [
            {"function": {"name": "allowed_tool"}},
            {"function": {"name": "other_tool"}}
        ]
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 准备测试数据
        messages = [{"role": "user", "content": "你好"}]
        
        # 调用方法，指定人格ID
        await chat_engine.generate_response(messages, personality_id="test_personality")
        
        # 验证API调用参数中只包含允许的工具
        args, kwargs = mock_openai_instance.chat.completions.create.call_args
        assert "tools" in kwargs
        assert len(kwargs["tools"]) == 1
        assert kwargs["tools"][0]["function"]["name"] == "allowed_tool"

# 测试_generate_streaming_response方法
@pytest.mark.asyncio
async def test_generate_streaming_response(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 创建模拟流式响应
    class MockDelta:
        def __init__(self, content=None):
            self.content = content

    class MockChoice:
        def __init__(self, content=None):
            self.delta = MockDelta(content)

    class MockStreamChunk:
        def __init__(self, content=None):
            self.choices = [MockChoice(content)]
    
    mock_stream_chunks = [
        MockStreamChunk("响应部分1"),
        MockStreamChunk("响应部分2"),
        MockStreamChunk("响应部分3")
    ]
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class, \
         patch('asyncio.create_task') as mock_create_task:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.return_value = mock_stream_chunks
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        mock_openai_instance.chat.completions.create.return_value = mock_stream_chunks
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 准备测试数据
        request_params = {"model": "gpt-4.1-turbo-2024-04-09", "messages": [{"role": "user", "content": "你好"}]}
        
        # 调用方法
        stream = chat_engine._generate_streaming_response(request_params, "test_conv", [{"role": "user", "content": "你好"}])
        
        # 收集流响应
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        
        # 验证流响应包含正确的内容
        assert len(chunks) == 4  # 3个内容块 + 1个结束标志
        assert chunks[0]["content"] == "响应部分1"
        assert chunks[1]["content"] == "响应部分2"
        assert chunks[2]["content"] == "响应部分3"
        assert chunks[3]["content"] == "" and chunks[3]["finish_reason"] == "stop"

# 测试_handle_tool_calls方法
@pytest.mark.asyncio
async def test_handle_tool_calls(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 创建模拟工具调用和响应
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "test_tool"
    mock_tool_call.function.arguments = json.dumps({"param": "value"})
    mock_tool_call.id = "tool_call_id"
    
    mock_tool_results = [{"success": True, "result": "工具调用结果", "tool_name": "test_tool"}]
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 修复：使用asyncio.Future来模拟异步方法的返回值
        future = asyncio.Future()
        future.set_result(mock_tool_results)
        mock_tool_manager_instance.execute_tools_concurrently.return_value = future
        
        # 模拟generate_response方法
        mock_response = {"role": "assistant", "content": "基于工具结果的响应"}
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        chat_engine.generate_response = AsyncMock(return_value=mock_response)
        
        # 调用方法
        result = await chat_engine._handle_tool_calls([mock_tool_call], "test_conv", [{"role": "user", "content": "你好"}])
        
        # 验证结果
        assert result == mock_response
        mock_tool_manager_instance.execute_tools_concurrently.assert_called_once_with([{"name": "test_tool", "parameters": {"param": "value"}}])
        chat_engine.generate_response.assert_called_once()

# 测试call_mcp_service方法 - 成功场景
@pytest.mark.asyncio
async def test_call_mcp_service_success(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class, \
         patch('core.chat_engine.mcp_manager.call_tool') as mock_call_tool:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 设置mcp_manager.call_tool返回值
        mock_call_tool.return_value = "MCP服务调用结果"
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 调用方法
        result = await chat_engine.call_mcp_service(
            service_name="test_service",
            method_name="test_method",
            params={"key": "value"}
        )
        
        # 验证结果
        assert result["success"] is True
        assert result["result"] == "MCP服务调用结果"
        
        # 验证mcp_manager.call_tool被正确调用
        mock_call_tool.assert_called_once_with("test_service__test_method", {"key": "value"}, None)

# 测试call_mcp_service方法 - 直接指定tool_name
@pytest.mark.asyncio
async def test_call_mcp_service_with_tool_name(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class, \
         patch('core.chat_engine.mcp_manager.call_tool') as mock_call_tool:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 设置mcp_manager.call_tool返回值
        mock_call_tool.return_value = "直接调用工具结果"
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 调用方法，直接指定tool_name
        result = await chat_engine.call_mcp_service(
            tool_name="direct_tool",
            params={"key": "value"}
        )
        
        # 验证结果
        assert result["success"] is True
        assert result["result"] == "直接调用工具结果"
        
        # 验证mcp_manager.call_tool被正确调用
        mock_call_tool.assert_called_once_with("direct_tool", {"key": "value"}, None)

# 测试call_mcp_service方法 - MCP服务错误
@pytest.mark.asyncio
async def test_call_mcp_service_mcp_error(mock_config):
    from services.mcp.exceptions import MCPServiceError
    
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class, \
         patch('core.chat_engine.mcp_manager.call_tool') as mock_call_tool, \
         patch('core.chat_engine.logger.error') as mock_logger_error:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 设置mcp_manager.call_tool抛出MCPServiceError
        mock_call_tool.side_effect = MCPServiceError("MCP服务错误")
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 调用方法
        result = await chat_engine.call_mcp_service(
            service_name="test_service",
            method_name="test_method",
            params={"key": "value"}
        )
        
        # 验证结果
        assert result["success"] is False
        assert "MCP服务调用失败" in result["error"]
        
        # 验证日志错误被记录
        mock_logger_error.assert_called_once()

# 测试clear_conversation_memory方法
def test_clear_conversation_memory(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 调用方法
        chat_engine.clear_conversation_memory("test_conv")
        
        # 验证chat_memory.delete_memory被正确调用
        mock_chat_memory_instance.delete_memory.assert_called_once_with("test_conv")

# 测试get_conversation_memory方法
def test_get_conversation_memory(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        mock_chat_memory_instance.get_all_memory.return_value = ["记忆1", "记忆2"]
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 调用方法
        result = chat_engine.get_conversation_memory("test_conv")
        
        # 验证结果
        assert result == ["记忆1", "记忆2"]
        # 验证chat_memory.get_all_memory被正确调用
        mock_chat_memory_instance.get_all_memory.assert_called_once_with("test_conv")

# 测试_async_save_message_to_memory方法
@pytest.mark.asyncio
async def test_async_save_message_to_memory(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 准备测试数据
        messages = [{"role": "assistant", "content": "测试响应"}, {"role": "user", "content": "测试问题"}]
        
        # 调用方法
        await chat_engine._async_save_message_to_memory("test_conv", messages)
        
        # 验证async_chat_memory.add_messages_batch被正确调用
        mock_async_chat_memory_instance.add_messages_batch.assert_called_once_with("test_conv", messages)

# 测试_save_message_to_memory_async方法（向后兼容）
@pytest.mark.asyncio
async def test_save_message_to_memory_async(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 使用patch来捕获对_async_save_message_to_memory的调用
        with patch.object(chat_engine, '_async_save_message_to_memory') as mock_async_save:
            # 准备测试数据
            message = {"role": "assistant", "content": "测试响应"}
            
            # 调用方法
            await chat_engine._save_message_to_memory_async("test_conv", message)
            
            # 验证_async_save_message_to_memory被正确调用
            mock_async_save.assert_called_once_with("test_conv", [message])

# 测试_generate_streaming_response方法
@pytest.mark.asyncio
async def test_generate_streaming_response(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 创建模拟流式响应
    class MockStreamChunk:
        def __init__(self, content=None):
            self.choices = [Mock()]
            self.choices[0].delta = Mock()
            self.choices[0].delta.content = content
    
    mock_stream_chunks = [
        MockStreamChunk("响应部分1"),
        MockStreamChunk("响应部分2"),
        MockStreamChunk("响应部分3")
    ]
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class, \
         patch('asyncio.create_task') as mock_create_task:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 准备测试数据
        request_params = {"model": "gpt-4.1-turbo-2024-04-09", "messages": [{"role": "user", "content": "你好"}]}
        
        # 调用方法
        stream = chat_engine._generate_streaming_response(request_params, "test_conv", [{"role": "user", "content": "你好"}])
        
        # 收集流响应
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        
        # 验证流响应包含正确的内容
        assert len(chunks) == 4  # 3个内容块 + 1个结束标志
        assert chunks[0]["content"] == "响应部分1"
        assert chunks[1]["content"] == "响应部分2"
        assert chunks[2]["content"] == "响应部分3"
        assert chunks[3]["content"] == "" and chunks[3]["finish_reason"] == "stop"

# 测试_handle_tool_calls方法
@pytest.mark.asyncio
async def test_handle_tool_calls(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 创建模拟工具调用和响应
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "test_tool"
    mock_tool_call.function.arguments = json.dumps({"param": "value"})
    mock_tool_call.id = "tool_call_id"
    
    mock_tool_results = [{"success": True, "result": "工具调用结果", "tool_name": "test_tool"}]
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 修复：使用asyncio.Future来模拟异步方法的返回值
        future = asyncio.Future()
        future.set_result(mock_tool_results)
        mock_tool_manager_instance.execute_tools_concurrently.return_value = future
        
        # 模拟generate_response方法
        mock_response = {"role": "assistant", "content": "基于工具结果的响应"}
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        chat_engine.generate_response = AsyncMock(return_value=mock_response)
        
        # 调用方法
        result = await chat_engine._handle_tool_calls([mock_tool_call], "test_conv", [{"role": "user", "content": "你好"}])
        
        # 验证结果
        assert result == mock_response
        mock_tool_manager_instance.execute_tools_concurrently.assert_called_once_with([{"name": "test_tool", "parameters": {"param": "value"}}])
        chat_engine.generate_response.assert_called_once()

# 测试call_mcp_service方法 - 成功场景
@pytest.mark.asyncio
async def test_call_mcp_service_success(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class, \
         patch('core.chat_engine.mcp_manager.call_tool') as mock_call_tool:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 设置mcp_manager.call_tool返回值
        mock_call_tool.return_value = "MCP服务调用结果"
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 调用方法
        result = await chat_engine.call_mcp_service(
            service_name="test_service",
            method_name="test_method",
            params={"key": "value"}
        )
        
        # 验证结果
        assert result["success"] is True
        assert result["result"] == "MCP服务调用结果"
        
        # 验证mcp_manager.call_tool被正确调用
        mock_call_tool.assert_called_once_with("test_service__test_method", {"key": "value"}, None)

# 测试call_mcp_service方法 - 直接指定tool_name
@pytest.mark.asyncio
async def test_call_mcp_service_with_tool_name(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class, \
         patch('core.chat_engine.mcp_manager.call_tool') as mock_call_tool:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 设置mcp_manager.call_tool返回值
        mock_call_tool.return_value = "直接调用工具结果"
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 调用方法，直接指定tool_name
        result = await chat_engine.call_mcp_service(
            tool_name="direct_tool",
            params={"key": "value"}
        )
        
        # 验证结果
        assert result["success"] is True
        assert result["result"] == "直接调用工具结果"
        
        # 验证mcp_manager.call_tool被正确调用
        mock_call_tool.assert_called_once_with("direct_tool", {"key": "value"}, None)

# 测试call_mcp_service方法 - MCP服务错误
@pytest.mark.asyncio
async def test_call_mcp_service_mcp_error(mock_config):
    from services.mcp.exceptions import MCPServiceError
    
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class, \
         patch('core.chat_engine.mcp_manager.call_tool') as mock_call_tool, \
         patch('core.chat_engine.logger.error') as mock_logger_error:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 设置mcp_manager.call_tool抛出MCPServiceError
        mock_call_tool.side_effect = MCPServiceError("MCP服务错误")
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 调用方法
        result = await chat_engine.call_mcp_service(
            service_name="test_service",
            method_name="test_method",
            params={"key": "value"}
        )
        
        # 验证结果
        assert result["success"] is False
        assert "MCP服务调用失败" in result["error"]
        
        # 验证日志错误被记录
        mock_logger_error.assert_called_once()

# 测试clear_conversation_memory方法
def test_clear_conversation_memory(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 调用方法
        chat_engine.clear_conversation_memory("test_conv")
        
        # 验证chat_memory.delete_memory被正确调用
        mock_chat_memory_instance.delete_memory.assert_called_once_with("test_conv")

# 测试get_conversation_memory方法
def test_get_conversation_memory(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        mock_chat_memory_instance.get_all_memory.return_value = ["记忆1", "记忆2"]
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 调用方法
        result = chat_engine.get_conversation_memory("test_conv")
        
        # 验证结果
        assert result == ["记忆1", "记忆2"]
        # 验证chat_memory.get_all_memory被正确调用
        mock_chat_memory_instance.get_all_memory.assert_called_once_with("test_conv")

# 测试_async_save_message_to_memory方法
@pytest.mark.asyncio
async def test_async_save_message_to_memory(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 准备测试数据
        messages = [{"role": "assistant", "content": "测试响应"}, {"role": "user", "content": "测试问题"}]
        
        # 调用方法
        await chat_engine._async_save_message_to_memory("test_conv", messages)
        
        # 验证async_chat_memory.add_messages_batch被正确调用
        mock_async_chat_memory_instance.add_messages_batch.assert_called_once_with("test_conv", messages)

# 测试_save_message_to_memory_async方法（向后兼容）
@pytest.mark.asyncio
async def test_save_message_to_memory_async(mock_config):
    # 配置mock_config
    mock_config.OPENAI_API_KEY = "test_key"
    mock_config.OPENAI_BASE_URL = "https://api.example.com"
    
    # 使用patch来模拟依赖
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_chat_memory_class, \
         patch('core.chat_engine.get_async_chat_memory') as mock_get_async_chat_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality_manager_class, \
         patch('core.chat_engine.ToolManager') as mock_tool_manager_class:
        
        # 设置模拟对象
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        mock_chat_memory_instance = MagicMock()
        mock_chat_memory_class.return_value = mock_chat_memory_instance
        
        mock_async_chat_memory_instance = AsyncMock()
        mock_get_async_chat_memory.return_value = mock_async_chat_memory_instance
        
        mock_personality_manager_instance = MagicMock()
        mock_personality_manager_class.return_value = mock_personality_manager_instance
        
        mock_tool_manager_instance = MagicMock()
        mock_tool_manager_class.return_value = mock_tool_manager_instance
        
        # 初始化ChatEngine
        chat_engine = ChatEngine()
        
        # 使用patch来捕获对_async_save_message_to_memory的调用
        with patch.object(chat_engine, '_async_save_message_to_memory') as mock_async_save:
            # 准备测试数据
            message = {"role": "assistant", "content": "测试响应"}
            
            # 调用方法
            await chat_engine._save_message_to_memory_async("test_conv", message)
            
            # 验证_async_save_message_to_memory被正确调用
            mock_async_save.assert_called_once_with("test_conv", [message])