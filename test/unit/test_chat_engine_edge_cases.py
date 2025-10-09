"""
ChatEngine edge cases and error paths
Covers remaining uncovered branches to push coverage to 62%+
"""
import pytest
import types
from unittest.mock import AsyncMock, patch, MagicMock

from core.chat_engine import ChatEngine


@pytest.mark.asyncio
class TestChatEngineEdgeCases:
    async def test_generate_response_empty_messages_list(self):
        engine = ChatEngine()
        with patch.object(engine.client, "create_chat", new=AsyncMock(return_value=types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Hello"))]
        ))):
            out = await engine.generate_response([], conversation_id="empty", stream=False)
            assert isinstance(out, dict)

    async def test_generate_response_invalid_message_format(self):
        engine = ChatEngine()
        # Test with message missing 'role' field
        invalid_messages = [{"content": "test"}]
        with patch.object(engine.client, "create_chat", new=AsyncMock(return_value=types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Hello"))]
        ))):
            out = await engine.generate_response(invalid_messages, conversation_id="invalid", stream=False)
            assert isinstance(out, dict)

    async def test_generate_response_missing_content_field(self):
        engine = ChatEngine()
        # Test with message missing 'content' field
        invalid_messages = [{"role": "user"}]
        with patch.object(engine.client, "create_chat", new=AsyncMock(return_value=types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Hello"))]
        ))):
            out = await engine.generate_response(invalid_messages, conversation_id="missing_content", stream=False)
            assert isinstance(out, dict)

    async def test_streaming_error_handling(self):
        engine = ChatEngine()
        # Mock create_chat_stream to raise an exception
        with patch.object(engine.client, "create_chat_stream", side_effect=Exception("Stream error")):
            msgs = [{"role": "user", "content": "test"}]
            gen = await engine.generate_response(msgs, conversation_id="stream_error", stream=True)
            collected = []
            async for part in gen:
                collected.append(part)
            # Should have error response
            assert len(collected) > 0
            assert any("error" in str(part) for part in collected)

    async def test_non_streaming_error_handling(self):
        engine = ChatEngine()
        # Mock create_chat to raise an exception
        with patch.object(engine.client, "create_chat", side_effect=Exception("API error")):
            msgs = [{"role": "user", "content": "test"}]
            out = await engine.generate_response(msgs, conversation_id="api_error", stream=False)
            assert isinstance(out, dict)
            assert "error" in str(out)

    async def test_memory_retrieval_timeout(self):
        engine = ChatEngine()
        # Mock memory retrieval to timeout
        with patch.object(engine.async_chat_memory, "get_relevant_memory", 
                         side_effect=Exception("Timeout")), \
             patch.object(engine.client, "create_chat", new=AsyncMock(return_value=types.SimpleNamespace(
                 choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Hello"))]
             ))):
            msgs = [{"role": "user", "content": "test"}]
            out = await engine.generate_response(msgs, conversation_id="memory_timeout", stream=False)
            assert isinstance(out, dict)

    async def test_personality_manager_error(self):
        engine = ChatEngine()
        # Mock personality manager to raise an exception
        with patch.object(engine.personality_manager, "get_personality", 
                         side_effect=Exception("Personality error")), \
             patch.object(engine.client, "create_chat", new=AsyncMock(return_value=types.SimpleNamespace(
                 choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Hello"))]
             ))):
            msgs = [{"role": "user", "content": "test"}]
            out = await engine.generate_response(msgs, conversation_id="personality_error", 
                                               personality_id="invalid", stream=False)
            assert isinstance(out, dict)

    async def test_tool_registry_error(self):
        engine = ChatEngine()
        # Mock tool registry to raise an exception
        with patch("core.chat_engine.tool_registry.get_functions_schema", 
                  side_effect=Exception("Tool registry error")), \
             patch.object(engine.client, "create_chat", new=AsyncMock(return_value=types.SimpleNamespace(
                 choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="Hello"))]
             ))):
            msgs = [{"role": "user", "content": "test"}]
            out = await engine.generate_response(msgs, conversation_id="tool_registry_error", 
                                               use_tools=True, stream=False)
            assert isinstance(out, dict)

    async def test_streaming_large_content_chunking(self):
        engine = ChatEngine()
        
        class Choice:
            def __init__(self, content=None, finish_reason=None):
                self.delta = types.SimpleNamespace(content=content)
                self.finish_reason = finish_reason

        class Chunk:
            def __init__(self, choice):
                self.choices = [choice]

        # Create large content to test chunking
        large_content = "A" * 200  # Large content to trigger chunking
        
        async def fake_stream(_params):
            yield Chunk(Choice(content=large_content))
            yield Chunk(Choice(finish_reason="stop"))

        with patch.object(engine.client, "create_chat_stream", side_effect=fake_stream):
            msgs = [{"role": "user", "content": "test"}]
            gen = await engine.generate_response(msgs, conversation_id="large_content", stream=True)
            collected = []
            async for part in gen:
                collected.append(part)
            assert len(collected) > 0

    async def test_async_save_message_to_memory_error(self):
        engine = ChatEngine()
        # Mock async_chat_memory to raise an exception
        with patch.object(engine.async_chat_memory, "add_message", 
                         side_effect=Exception("Memory save error")):
            # This should not raise an exception, just log the error
            await engine._async_save_message_to_memory("test_conv", [{"role": "user", "content": "test"}])
            # Test passes if no exception is raised

    async def test_get_allowed_tools_schema_personality_error(self):
        engine = ChatEngine()
        # Mock personality manager to raise an exception
        with patch.object(engine.personality_manager, "get_personality", 
                         side_effect=Exception("Personality error")):
            result = await engine.get_allowed_tools_schema("invalid_personality")
            assert result == []  # Should return empty list on error

    async def test_get_allowed_tools_schema_tool_registry_error(self):
        engine = ChatEngine()
        # Mock tool registry to raise an exception
        with patch("core.chat_engine.tool_registry.get_functions_schema", 
                  side_effect=Exception("Tool registry error")):
            result = await engine.get_allowed_tools_schema("friendly")
            assert result == []  # Should return empty list on error
