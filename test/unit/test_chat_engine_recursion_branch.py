"""
测试 ChatEngine 的递归分支 (468-497行)
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
from core.chat_engine import ChatEngine


class TestChatEngineRecursionBranch:
    """测试ChatEngine递归分支处理"""

    @pytest.fixture
    def chat_engine(self):
        """创建ChatEngine实例"""
        with patch('core.chat_engine.OpenAI'), \
             patch('core.chat_engine.ToolManager'), \
             patch('core.chat_engine.PersonalityManager'), \
             patch('core.chat_engine.get_async_chat_memory'):
            return ChatEngine()

    @pytest.mark.asyncio
    async def test_handle_tool_calls_recursion_468_497(self, chat_engine):
        """测试468-497行的递归分支处理"""
        # Mock tool_manager.execute_tools_concurrently 返回工具结果
        mock_tool_result = {
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "test_tool",
                        "arguments": '{"param": "value"}'
                    }
                }
            ]
        }
        
        chat_engine.tool_manager.execute_tools_concurrently = AsyncMock(return_value=[mock_tool_result])
        
        # Mock sync_client.chat.completions.create 返回递归调用的响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Tool executed successfully"
        mock_response.choices[0].message.tool_calls = None
        
        chat_engine.sync_client.chat.completions.create.return_value = mock_response
        
        # Mock generate_response 递归调用
        async def mock_generate_response(messages, conversation_id, **kwargs):
            return {"content": "Recursive response", "finish_reason": "stop"}
        
        chat_engine.generate_response = AsyncMock(side_effect=mock_generate_response)
        
        # 准备工具调用消息
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "arguments": '{"param": "value"}'
                }
            }
        ]
        
        messages = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": None, "tool_calls": tool_calls}
        ]
        
        # 测试递归处理
        result = await chat_engine._handle_tool_calls(tool_calls, "test_conversation", messages)
        
        # 验证递归调用发生
        assert chat_engine.tool_manager.execute_tools_concurrently.called
        assert chat_engine.generate_response.called

    @pytest.mark.asyncio
    async def test_handle_tool_calls_recursion_with_follow_up(self, chat_engine):
        """测试递归分支中的后续处理"""
        # Mock tool_manager.execute_tools_concurrently 返回工具结果
        mock_tool_result = {
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "test_tool",
                        "arguments": '{"param": "value"}'
                    }
                }
            ]
        }
        
        chat_engine.tool_manager.execute_tools_concurrently = AsyncMock(return_value=[mock_tool_result])
        
        # Mock generate_response 递归调用返回流式响应
        async def mock_generate_response_stream(messages, conversation_id, **kwargs):
            async def stream_generator():
                yield {"content": "Recursive", "finish_reason": None}
                yield {"content": " response", "finish_reason": "stop"}
            return stream_generator()
        
        chat_engine.generate_response = AsyncMock(side_effect=mock_generate_response_stream)
        
        # 准备工具调用消息
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "arguments": '{"param": "value"}'
                }
            }
        ]
        
        messages = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": None, "tool_calls": tool_calls}
        ]
        
        # 测试递归处理
        result = await chat_engine._handle_tool_calls(tool_calls, "test_conversation", messages)
        
        # 验证递归调用发生
        assert chat_engine.tool_manager.execute_tools_concurrently.called
        assert chat_engine.generate_response.called

    @pytest.mark.asyncio
    async def test_handle_tool_calls_recursion_error_handling(self, chat_engine):
        """测试递归分支中的错误处理"""
        # Mock tool_manager.execute_tools_concurrently 抛出异常
        chat_engine.tool_manager.execute_tools_concurrently = AsyncMock(side_effect=Exception("Tool execution failed"))
        
        # 准备工具调用消息
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "arguments": '{"param": "value"}'
                }
            }
        ]
        
        messages = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": None, "tool_calls": tool_calls}
        ]
        
        # 测试递归处理中的错误处理
        with pytest.raises(Exception, match="Tool execution failed"):
            await chat_engine._handle_tool_calls(tool_calls, "test_conversation", messages)

    @pytest.mark.asyncio
    async def test_handle_tool_calls_recursion_empty_results(self, chat_engine):
        """测试递归分支中空结果的处理"""
        # Mock tool_manager.execute_tools_concurrently 返回空结果
        chat_engine.tool_manager.execute_tools_concurrently = AsyncMock(return_value=[])
        
        # Mock generate_response 递归调用
        async def mock_generate_response(messages, conversation_id, **kwargs):
            return {"content": "No tools executed", "finish_reason": "stop"}
        
        chat_engine.generate_response = AsyncMock(side_effect=mock_generate_response)
        
        # 准备工具调用消息
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "arguments": '{"param": "value"}'
                }
            }
        ]
        
        messages = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": None, "tool_calls": tool_calls}
        ]
        
        # 测试递归处理
        result = await chat_engine._handle_tool_calls(tool_calls, "test_conversation", messages)
        
        # 验证递归调用发生
        assert chat_engine.tool_manager.execute_tools_concurrently.called
        assert chat_engine.generate_response.called

    @pytest.mark.asyncio
    async def test_handle_tool_calls_recursion_multiple_tools(self, chat_engine):
        """测试递归分支中多个工具的处理"""
        # Mock tool_manager.execute_tools_concurrently 返回多个工具结果
        mock_tool_results = [
            {
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "tool1",
                            "arguments": '{"param1": "value1"}'
                        }
                    }
                ]
            },
            {
                "tool_calls": [
                    {
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "tool2",
                            "arguments": '{"param2": "value2"}'
                        }
                    }
                ]
            }
        ]
        
        chat_engine.tool_manager.execute_tools_concurrently = AsyncMock(return_value=mock_tool_results)
        
        # Mock generate_response 递归调用
        async def mock_generate_response(messages, conversation_id, **kwargs):
            return {"content": "Multiple tools executed", "finish_reason": "stop"}
        
        chat_engine.generate_response = AsyncMock(side_effect=mock_generate_response)
        
        # 准备多个工具调用消息
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "tool1",
                    "arguments": '{"param1": "value1"}'
                }
            },
            {
                "id": "call_2",
                "type": "function",
                "function": {
                    "name": "tool2",
                    "arguments": '{"param2": "value2"}'
                }
            }
        ]
        
        messages = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": None, "tool_calls": tool_calls}
        ]
        
        # 测试递归处理
        result = await chat_engine._handle_tool_calls(tool_calls, "test_conversation", messages)
        
        # 验证递归调用发生
        assert chat_engine.tool_manager.execute_tools_concurrently.called
        assert chat_engine.generate_response.called
