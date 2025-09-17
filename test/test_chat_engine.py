import pytest
from unittest.mock import patch, MagicMock
from core.chat_engine import ChatEngine
from services.mcp.models import MCPRequest

@pytest.mark.asyncio
async def test_chat_engine_initialization():
    # 测试ChatEngine的初始化
    with patch('core.chat_engine.OpenAI') as mock_openai, \
         patch('core.chat_engine.ChatMemory') as mock_memory, \
         patch('core.chat_engine.PersonalityManager') as mock_personality, \
         patch('core.chat_engine.ToolManager') as mock_tool:
        
        # 创建ChatEngine实例
        chat_engine = ChatEngine()
        
        # 验证组件初始化
        mock_openai.assert_called_once()
        mock_memory.assert_called_once()
        mock_personality.assert_called_once()
        mock_tool.assert_called_once()

@pytest.mark.asyncio
async def test_call_mcp_service_success():
    # 测试成功调用MCP服务
    with patch('core.chat_engine.mcp_client') as mock_mcp_client:
        # 设置模拟返回值
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.result = {"data": "success"}
        # 修改这里，模拟异步调用返回值
        mock_mcp_client.call.return_value = mock_response
        
        # 创建ChatEngine实例
        chat_engine = ChatEngine()
        
        # 调用服务
        result = await chat_engine.call_mcp_service("test_service", "test_method", {"param": "value"})
        
        # 验证结果
        assert result["success"] is True
        assert result["result"] == {"data": "success"}
        assert result["error"] is None
        
        # 验证调用参数
        mock_mcp_client.call.assert_called_once()
        args, _ = mock_mcp_client.call.call_args
        request = args[0]
        assert isinstance(request, MCPRequest)
        assert request.service_name == "test_service"
        assert request.method_name == "test_method"
        assert request.params == {"param": "value"}

@pytest.mark.asyncio
async def test_call_mcp_service_failure():
    # 测试MCP服务调用失败
    with patch('core.chat_engine.mcp_client') as mock_mcp_client:
        # 设置模拟返回值
        mock_response = MagicMock()
        mock_response.success = False
        mock_response.error = "Service error"
        mock_mcp_client.call.return_value = mock_response
        
        # 创建ChatEngine实例
        chat_engine = ChatEngine()
        
        # 调用服务
        result = await chat_engine.call_mcp_service("test_service", "test_method", {"param": "value"})
        
        # 验证结果
        assert result["success"] is False
        assert result["result"] is None
        assert result["error"] == "Service error"

@pytest.mark.asyncio
async def test_call_mcp_service_exception():
    # 测试MCP服务调用抛出异常
    with patch('core.chat_engine.mcp_client') as mock_mcp_client:
        # 设置模拟抛出异常
        mock_mcp_client.call.side_effect = Exception("Connection error")
        
        # 创建ChatEngine实例
        chat_engine = ChatEngine()
        
        # 调用服务
        result = await chat_engine.call_mcp_service("test_service", "test_method", {"param": "value"})
        
        # 验证结果
        assert result["success"] is False
        assert "Connection error" in result["error"]

@pytest.mark.asyncio
async def test_clear_conversation_memory():
    # 测试清除会话记忆
    with patch('core.chat_engine.ChatMemory') as mock_memory_class:
        # 设置模拟记忆对象
        mock_memory = MagicMock()
        mock_memory_class.return_value = mock_memory
        
        # 创建ChatEngine实例
        chat_engine = ChatEngine()
        
        # 调用清除记忆方法
        chat_engine.clear_conversation_memory("test-conversation-123")
        
        # 验证调用
        mock_memory.delete_memory.assert_called_once_with("test-conversation-123")

@pytest.mark.asyncio
async def test_get_conversation_memory():
    # 测试获取会话记忆
    with patch('core.chat_engine.ChatMemory') as mock_memory_class:
        # 设置模拟记忆对象和返回值
        mock_memory = MagicMock()
        mock_memory.get_all_memory.return_value = ["记忆1", "记忆2"]
        mock_memory_class.return_value = mock_memory
        
        # 创建ChatEngine实例
        chat_engine = ChatEngine()
        
        # 调用获取记忆方法
        memories = chat_engine.get_conversation_memory("test-conversation-123")
        
        # 验证结果
        assert memories == ["记忆1", "记忆2"]
        mock_memory.get_all_memory.assert_called_once_with("test-conversation-123")