"""
ChatEngine deep tests
Covers streaming flow (mocked), param validation, memory toggle, and engine info APIs
"""
import pytest
import types
from unittest.mock import patch, Mock, AsyncMock

from core.chat_engine import ChatEngine


@pytest.mark.asyncio
class TestChatEngineDeep:
    async def test_param_validation_errors(self):
        engine = ChatEngine()
        # messages must be list
        out = await engine.generate_response(None, conversation_id="c1", stream=False)
        assert isinstance(out, dict) and "content" in out
        # message item must be dict
        out2 = await engine.generate_response(["bad"], conversation_id="c1", stream=False)
        assert isinstance(out2, dict) and "content" in out2
        # missing fields
        out3 = await engine.generate_response([{"role": "user"}], conversation_id="c1", stream=False)
        assert isinstance(out3, dict) and "content" in out3

    async def test_streaming_basic_mock(self):
        engine = ChatEngine()

        class Choice:
            def __init__(self, content=None, tool_calls=None, finish_reason=None):
                self.delta = types.SimpleNamespace(content=content, tool_calls=tool_calls)
                self.finish_reason = finish_reason

        class Chunk:
            def __init__(self, choice):
                self.choices = [choice]

        async def fake_stream(_params):
            # emit two content chunks then a stop
            yield Chunk(Choice(content="Hello "))
            yield Chunk(Choice(content="World"))
            yield Chunk(Choice(content=None, finish_reason="stop"))

        with patch.object(engine.client, "create_chat_stream", side_effect=fake_stream):
            msgs = [{"role": "user", "content": "hi"}]
            gen = await engine.generate_response(msgs, conversation_id="c1", stream=True)
            collected = []
            async for part in gen:
                collected.append(part)
            # Should have emitted at least two content parts and a stop
            assert any(p.get("content") for p in collected)
            assert any(p.get("finish_reason") == "stop" for p in collected)

    async def test_memory_toggle_should_include_memory_false(self):
        engine = ChatEngine()
        msgs = [{"role": "user", "content": "Ask"}]
        with patch("core.chat_engine.should_include_memory", return_value=False):
            out = await engine.generate_response(msgs, conversation_id="mem_test", stream=False)
            assert isinstance(out, dict)

    async def test_engine_info_and_health(self):
        engine = ChatEngine()
        info = await engine.get_engine_info()
        assert isinstance(info, dict) and info.get("name")
        health = await engine.health_check()
        assert isinstance(health, dict) and "healthy" in health

    async def test_available_tools_and_personalities(self):
        engine = ChatEngine()
        tools = await engine.get_available_tools()
        assert isinstance(tools, list)
        personalities = await engine.get_supported_personalities()
        assert isinstance(personalities, list)

    async def test_clear_and_get_memory_interface(self):
        engine = ChatEngine()
        # Clear should return dict with success
        res = await engine.clear_conversation_memory("conv_x")
        assert isinstance(res, dict) and "success" in res
        mem = await engine.get_conversation_memory("conv_x", limit=5)
        assert isinstance(mem, dict) and "success" in mem
