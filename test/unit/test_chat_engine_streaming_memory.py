"""
ChatEngine streaming and memory tests
Covers streaming memory save on finish_reason and non-streaming tool calls recursion
"""
import pytest
import types
from unittest.mock import AsyncMock, patch

from core.chat_engine import ChatEngine


@pytest.mark.asyncio
class TestChatEngineStreamingMemory:
    async def test_streaming_finish_reason_saves_memory(self):
        engine = ChatEngine()
        
        class Choice:
            def __init__(self, content=None, tool_calls=None, finish_reason=None):
                self.delta = types.SimpleNamespace(content=content, tool_calls=tool_calls)
                self.finish_reason = finish_reason

        class Chunk:
            def __init__(self, choice):
                self.choices = [choice]

        async def fake_stream(_params):
            yield Chunk(Choice(content="Hello"))
            yield Chunk(Choice(content=" World"))
            yield Chunk(Choice(content=None, finish_reason="stop"))

        with patch.object(engine.client, "create_chat_stream", side_effect=fake_stream), \
             patch.object(engine, "_async_save_message_to_memory", new=AsyncMock()) as mock_save:
            msgs = [{"role": "user", "content": "hi"}]
            gen = await engine.generate_response(msgs, conversation_id="stream_mem", stream=True)
            collected = []
            async for part in gen:
                collected.append(part)
            # Should have called _async_save_message_to_memory on finish_reason
            mock_save.assert_called_once()

    async def test_non_streaming_tool_calls_recursion(self):
        engine = ChatEngine()
        
        # Mock tool_manager to return results
        engine.tool_manager.execute_tools_concurrently = AsyncMock(return_value=[{
            "tool_name": "gettime",
            "success": True,
            "result": {"time": "2024-01-01 12:00:00"}
        }])
        
        # Create a response with tool_calls
        class Message:
            def __init__(self):
                self.content = None
                self.tool_calls = [{
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "gettime", "arguments": "{}"}
                }]
        
        class Choice:
            def __init__(self):
                self.message = Message()
        
        class Response:
            def __init__(self):
                self.choices = [Choice()]
        
        fake_response = Response()
        
        with patch.object(engine.client, "create_chat", new=AsyncMock(return_value=fake_response)), \
             patch.object(engine, "_handle_tool_calls", new=AsyncMock(return_value={"content": "Tool result"})) as mock_handle:
            msgs = [{"role": "user", "content": "what time is it?"}]
            out = await engine.generate_response(msgs, conversation_id="tool_recursion", use_tools=True, stream=False)
            # Should have called _handle_tool_calls
            mock_handle.assert_called_once()
            assert out == {"content": "Tool result"}

    async def test_streaming_tool_calls_handling(self):
        engine = ChatEngine()
        
        class Choice:
            def __init__(self, content=None, tool_calls=None, finish_reason=None):
                self.delta = types.SimpleNamespace(content=content, tool_calls=tool_calls)
                self.finish_reason = finish_reason

        class Chunk:
            def __init__(self, choice):
                self.choices = [choice]

        # Mock tool_calls in streaming response
        tool_call_obj = types.SimpleNamespace(
            id="call_456",
            function=types.SimpleNamespace(name="gettime", arguments="{}")
        )
        
        async def fake_stream(_params):
            yield Chunk(Choice(content="Let me check"))
            yield Chunk(Choice(tool_calls=[tool_call_obj]))
            yield Chunk(Choice(finish_reason="stop"))

        # Mock tool_manager to return results
        engine.tool_manager.execute_tools_concurrently = AsyncMock(return_value=[{
            "tool_name": "gettime",
            "success": True,
            "result": {"time": "2024-01-01 12:00:00"}
        }])

        with patch.object(engine.client, "create_chat_stream", side_effect=fake_stream), \
             patch.object(engine.client, "create_chat", new=AsyncMock(return_value=types.SimpleNamespace(
                 choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Time is 12:00"))]
             ))):
            msgs = [{"role": "user", "content": "time please"}]
            gen = await engine.generate_response(msgs, conversation_id="stream_tools", use_tools=True, stream=True)
            collected = []
            async for part in gen:
                collected.append(part)
            # Should have collected streaming parts including tool execution
            assert len(collected) > 0
