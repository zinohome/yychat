"""
Branch coverage tests for core/chat_engine.py using pure mocks
"""
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock

from core.chat_engine import ChatEngine


class TestChatEngineBranches:
    @pytest.mark.asyncio
    async def test_invalid_messages_streaming_generator(self):
        engine = ChatEngine()
        # streaming with invalid messages (not list)
        result = await engine.generate_response(None, stream=True)
        assert hasattr(result, "__aiter__")  # async generator
        chunks = []
        async for c in result:
            chunks.append(c)
        assert chunks[0]["finish_reason"] == "error"

    @pytest.mark.asyncio
    async def test_missing_fields_message_streaming(self):
        engine = ChatEngine()
        bad_messages = [{"role": "user"}]  # missing content
        gen = await engine.generate_response(bad_messages, stream=True)
        out = []
        async for c in gen:
            out.append(c)
        assert out and out[0]["finish_reason"] == "error"

    @pytest.mark.asyncio
    async def test_defaults_apply_when_none(self):
        engine = ChatEngine()
        # mock client to avoid real call
        engine.client = MagicMock()
        engine.client.create_chat = AsyncMock(return_value={"role": "assistant", "content": "ok"})
        engine.async_chat_memory = MagicMock()
        engine.async_chat_memory.get_relevant_memory = AsyncMock(return_value=[])

        res = await engine.generate_response([{"role": "user", "content": "hi"}], conversation_id="c1",
                                             personality_id=None, use_tools=None, stream=False)
        assert isinstance(res, dict)
        assert "content" in res

    @pytest.mark.asyncio
    async def test_stream_follow_up_after_tool_calls(self):
        engine = ChatEngine()

        # First stream yields a tool call
        async def first_stream():
            yield {"tool_calls": [{"id": "t1", "function": {"name": "calc", "arguments": "{}"}}]}

        # Second stream yields final content
        async def second_stream():
            yield {"content": "done"}

        engine.client = MagicMock()
        engine.client.create_chat_stream = AsyncMock()
        engine.client.create_chat_stream.side_effect = [first_stream(), second_stream()]

        engine.tool_manager = MagicMock()
        engine.tool_manager.execute_tools_concurrently = AsyncMock(return_value=[{"success": True, "tool_name": "calc", "result": 1}])
        engine.async_chat_memory = MagicMock()
        engine.async_chat_memory.get_relevant_memory = AsyncMock(return_value=[])

        msgs = [{"role": "user", "content": "use tool"}]
        chunks = []
        async for c in engine._generate_streaming_response(msgs, "c1", original_messages=msgs):
            chunks.append(c)
        assert any("content" in c for c in chunks)


