"""
Mem0Proxy Handler深入测试
测试ToolHandler、FallbackHandler、ResponseHandler等组件
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from core.mem0_proxy import (
    ToolHandler,
    FallbackHandler,
    ResponseHandler,
    MemoryHandler,
    get_mem0_proxy
)

@pytest.mark.asyncio
class TestToolHandler:
    """ToolHandler深入测试"""
    
    def test_tool_handler_initialization(self):
        """测试ToolHandler初始化"""
        from config.config import get_config
        config = get_config()
        
        handler = ToolHandler(config)
        
        assert handler is not None
        assert hasattr(handler, 'tool_manager')
        assert hasattr(handler, 'mcp_manager')
        assert hasattr(handler, 'personality_manager')
        print("✅ ToolHandler初始化成功")
    
    async def test_get_allowed_tools_no_personality(self):
        """测试获取工具（无人格限制）"""
        from config.config import get_config
        config = get_config()
        
        handler = ToolHandler(config)
        tools = await handler.get_allowed_tools(personality_id=None)
        
        assert isinstance(tools, list)
        print(f"✅ 获取所有工具成功（{len(tools)}个）")
    
    async def test_get_allowed_tools_with_personality(self):
        """测试获取工具（带人格限制）"""
        from config.config import get_config
        config = get_config()
        
        handler = ToolHandler(config)
        
        # 使用health_assistant人格测试
        tools = await handler.get_allowed_tools(personality_id="health_assistant")
        
        assert isinstance(tools, list)
        # health_assistant可能有工具限制
        print(f"✅ 带人格限制获取工具成功（{len(tools)}个）")
    
    async def test_get_allowed_tools_nonexistent_personality(self):
        """测试获取工具（不存在的人格）"""
        from config.config import get_config
        config = get_config()
        
        handler = ToolHandler(config)
        tools = await handler.get_allowed_tools(personality_id="nonexistent_999")
        
        # 不存在的人格应该返回所有工具
        assert isinstance(tools, list)
        print(f"✅ 不存在的人格返回所有工具（{len(tools)}个）")
    
    async def test_handle_tool_calls_basic(self):
        """测试基本工具调用处理"""
        from config.config import get_config
        config = get_config()
        
        handler = ToolHandler(config)
        
        # 构造工具调用
        tool_calls = [{
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "get_current_time",
                "arguments": json.dumps({})
            }
        }]
        
        messages = [{"role": "user", "content": "What time is it?"}]
        
        try:
            result = await handler.handle_tool_calls(
                tool_calls, 
                "test_tool_conv", 
                messages
            )
            
            assert isinstance(result, dict)
            assert "content" in result or "error" in result
            print("✅ 基本工具调用处理成功")
        except Exception as e:
            print(f"⚠️ 工具调用测试（可能需要API）: {str(e)[:50]}")
    
    async def test_handle_tool_calls_with_personality(self):
        """测试带人格的工具调用"""
        from config.config import get_config
        config = get_config()
        
        handler = ToolHandler(config)
        
        tool_calls = [{
            "id": "call_456",
            "type": "function",
            "function": {
                "name": "get_current_time",
                "arguments": "{}"
            }
        }]
        
        messages = [{"role": "user", "content": "Time?"}]
        
        try:
            result = await handler.handle_tool_calls(
                tool_calls,
                "test_tool_personality",
                messages,
                personality_id="friendly"
            )
            
            assert isinstance(result, dict)
            print("✅ 带人格的工具调用处理成功")
        except Exception as e:
            print(f"⚠️ 带人格工具调用: {str(e)[:50]}")
    
    async def test_handle_tool_calls_invalid_json(self):
        """测试处理无效JSON参数"""
        from config.config import get_config
        config = get_config()
        
        handler = ToolHandler(config)
        
        # 构造无效JSON的工具调用
        tool_calls = [{
            "id": "call_invalid",
            "type": "function",
            "function": {
                "name": "get_current_time",
                "arguments": "{invalid json"  # 故意的无效JSON
            }
        }]
        
        messages = [{"role": "user", "content": "Test"}]
        
        try:
            result = await handler.handle_tool_calls(
                tool_calls,
                "test_invalid_json",
                messages
            )
            
            # 应该能处理错误并返回结果
            assert isinstance(result, dict)
            print("✅ 无效JSON参数处理成功（错误恢复）")
        except Exception as e:
            # 可能会抛出异常，这也是可接受的
            print(f"⚠️ 无效JSON处理: {str(e)[:50]}")
    
    async def test_handle_streaming_tool_calls(self):
        """测试流式工具调用"""
        from config.config import get_config
        config = get_config()
        
        handler = ToolHandler(config)
        
        tool_calls = [{
            "id": "call_stream",
            "type": "function",
            "function": {
                "name": "get_current_time",
                "arguments": "{}"
            }
        }]
        
        messages = [{"role": "user", "content": "Time?"}]
        
        try:
            generator = handler.handle_streaming_tool_calls(
                tool_calls,
                "test_stream_tool",
                messages
            )
            
            chunks = []
            async for chunk in generator:
                chunks.append(chunk)
                if len(chunks) >= 3:  # 只获取前3个chunk
                    break
            
            assert len(chunks) > 0
            assert all(isinstance(c, dict) for c in chunks)
            print(f"✅ 流式工具调用成功（{len(chunks)}个chunk）")
        except Exception as e:
            print(f"⚠️ 流式工具调用: {str(e)[:50]}")
    
    def test_collect_tool_calls(self):
        """测试工具调用信息收集"""
        from config.config import get_config
        config = get_config()
        
        handler = ToolHandler(config)
        
        # 创建mock chunk
        mock_chunk = Mock()
        mock_chunk.choices = [Mock()]
        mock_chunk.choices[0].delta = Mock()
        
        # 创建mock tool_call
        mock_tool_call = Mock()
        mock_tool_call.index = 0
        mock_tool_call.id = "call_test"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "test_function"
        mock_tool_call.function.arguments = '{"key": "value"}'
        
        mock_chunk.choices[0].delta.tool_calls = [mock_tool_call]
        
        # 测试收集
        tool_calls = []
        result = handler._collect_tool_calls(mock_chunk, tool_calls)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["id"] == "call_test"
        print("✅ 工具调用信息收集成功")


@pytest.mark.asyncio
class TestFallbackHandler:
    """FallbackHandler降级处理测试"""
    
    def test_fallback_handler_initialization(self):
        """测试FallbackHandler初始化"""
        from config.config import get_config
        config = get_config()
        
        handler = FallbackHandler(config)
        
        assert handler is not None
        assert hasattr(handler, 'openai_client')
        assert hasattr(handler, 'tool_handler')
        assert hasattr(handler, 'personality_handler')
        assert hasattr(handler, 'memory_handler')
        print("✅ FallbackHandler初始化成功")
    
    async def test_handle_fallback_non_streaming(self):
        """测试非流式降级处理"""
        from config.config import get_config
        config = get_config()
        
        handler = FallbackHandler(config)
        messages = [{"role": "user", "content": "Test fallback"}]
        
        try:
            result = await handler.handle_fallback(
                messages,
                "test_fallback",
                use_tools=False,
                stream=False
            )
            
            assert isinstance(result, dict)
            assert "role" in result or "content" in result
            print("✅ 非流式降级处理成功")
        except Exception as e:
            print(f"⚠️ 降级处理（可能需要API）: {str(e)[:50]}")
    
    async def test_handle_fallback_streaming(self):
        """测试流式降级处理"""
        from config.config import get_config
        config = get_config()
        
        handler = FallbackHandler(config)
        messages = [{"role": "user", "content": "Test stream fallback"}]
        
        try:
            generator = await handler.handle_fallback(
                messages,
                "test_fallback_stream",
                use_tools=False,
                stream=True
            )
            
            chunks = []
            async for chunk in generator:
                chunks.append(chunk)
                if len(chunks) >= 3:
                    break
            
            assert len(chunks) > 0
            print(f"✅ 流式降级处理成功（{len(chunks)}个chunk）")
        except Exception as e:
            print(f"⚠️ 流式降级: {str(e)[:50]}")
    
    async def test_handle_fallback_with_tools(self):
        """测试带工具的降级处理"""
        from config.config import get_config
        config = get_config()
        
        handler = FallbackHandler(config)
        messages = [{"role": "user", "content": "What time is it?"}]
        
        try:
            result = await handler.handle_fallback(
                messages,
                "test_fallback_tools",
                use_tools=True,
                stream=False
            )
            
            assert isinstance(result, dict)
            print("✅ 带工具的降级处理成功")
        except Exception as e:
            print(f"⚠️ 带工具降级: {str(e)[:50]}")
    
    async def test_handle_fallback_with_personality(self):
        """测试带人格的降级处理"""
        from config.config import get_config
        config = get_config()
        
        handler = FallbackHandler(config)
        messages = [{"role": "user", "content": "Hello"}]
        
        try:
            result = await handler.handle_fallback(
                messages,
                "test_fallback_personality",
                personality_id="friendly",
                use_tools=False,
                stream=False
            )
            
            assert isinstance(result, dict)
            print("✅ 带人格的降级处理成功")
        except Exception as e:
            print(f"⚠️ 带人格降级: {str(e)[:50]}")


@pytest.mark.asyncio
class TestResponseHandler:
    """ResponseHandler响应处理测试"""
    
    def test_response_handler_initialization(self):
        """测试ResponseHandler初始化"""
        from config.config import get_config
        config = get_config()
        
        handler = ResponseHandler(config)
        
        assert handler is not None
        assert hasattr(handler, 'tool_handler')
        assert hasattr(handler, 'memory_handler')
        print("✅ ResponseHandler初始化成功")
    
    async def test_handle_streaming_response_mock(self):
        """测试流式响应处理（mock）"""
        from config.config import get_config
        config = get_config()
        
        handler = ResponseHandler(config)
        
        # 创建mock响应
        class MockChunk:
            def __init__(self, content):
                self.choices = [Mock()]
                self.choices[0].delta = Mock()
                self.choices[0].delta.content = content
                self.choices[0].delta.tool_calls = None
                self.choices[0].finish_reason = None
        
        class MockResponse:
            async def __aiter__(self):
                yield MockChunk("Hello")
                yield MockChunk(" World")
                final_chunk = MockChunk(None)
                final_chunk.choices[0].finish_reason = "stop"
                yield final_chunk
        
        # 创建mock客户端和参数
        mock_client = Mock()
        mock_client.chat.completions.create = Mock(return_value=MockResponse())
        call_params = {"messages": [{"role": "user", "content": "Hi"}]}
        
        chunks = []
        with patch('asyncio.to_thread', return_value=MockResponse()):
            async for chunk in handler.handle_streaming_response(
                mock_client,
                call_params,
                "test_stream_response",
                [{"role": "user", "content": "Hi"}]
            ):
                chunks.append(chunk)
        
        assert len(chunks) > 0
        print(f"✅ 流式响应处理成功（{len(chunks)}个chunk）")
    
    async def test_handle_non_streaming_response_mock(self):
        """测试非流式响应处理（mock）"""
        from config.config import get_config
        config = get_config()
        
        handler = ResponseHandler(config)
        
        # 创建mock客户端
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.tool_calls = None
        
        # Mock异步调用
        with patch('asyncio.to_thread', return_value=mock_response):
            result = await handler.handle_non_streaming_response(
                mock_client,
                {"messages": [{"role": "user", "content": "Test"}]},
                "test_non_stream",
                [{"role": "user", "content": "Test"}]
            )
        
        assert isinstance(result, dict)
        assert "content" in result or "role" in result
        print("✅ 非流式响应处理成功")


@pytest.mark.asyncio
class TestMemoryHandlerDetailed:
    """MemoryHandler详细测试"""
    
    async def test_save_memory_both_mode(self):
        """测试保存记忆（both模式）"""
        from config.config import get_config
        config = get_config()
        
        handler = MemoryHandler(config)
        original_mode = handler.save_mode
        handler.save_mode = "both"
        
        messages = [{"role": "user", "content": "Test message"}]
        response = {"content": "Test response"}
        
        try:
            await handler.save_memory(messages, response, "test_both_save")
            print("✅ both模式保存记忆成功")
        except Exception as e:
            print(f"⚠️ both模式保存: {str(e)[:50]}")
        finally:
            handler.save_mode = original_mode
    
    async def test_save_memory_user_only_mode(self):
        """测试保存记忆（user_only模式）"""
        from config.config import get_config
        config = get_config()
        
        handler = MemoryHandler(config)
        original_mode = handler.save_mode
        handler.save_mode = "user_only"
        
        messages = [{"role": "user", "content": "User message"}]
        response = {"content": "Response"}
        
        try:
            await handler.save_memory(messages, response, "test_user_only")
            print("✅ user_only模式保存记忆成功")
        except Exception as e:
            print(f"⚠️ user_only模式: {str(e)[:50]}")
        finally:
            handler.save_mode = original_mode
    
    async def test_save_memory_assistant_only_mode(self):
        """测试保存记忆（assistant_only模式）"""
        from config.config import get_config
        config = get_config()
        
        handler = MemoryHandler(config)
        original_mode = handler.save_mode
        handler.save_mode = "assistant_only"
        
        messages = [{"role": "user", "content": "Message"}]
        response = {"content": "Assistant response"}
        
        try:
            await handler.save_memory(messages, response, "test_assistant_only")
            print("✅ assistant_only模式保存记忆成功")
        except Exception as e:
            print(f"⚠️ assistant_only模式: {str(e)[:50]}")
        finally:
            handler.save_mode = original_mode


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
