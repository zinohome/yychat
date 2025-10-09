"""
More branch coverage for core/chat_engine.py (pure mocks)
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from core.chat_engine import ChatEngine


class TestChatEngineMoreBranches:
    @pytest.mark.asyncio
    async def test_invalid_message_type_non_stream(self):
        engine = ChatEngine()
        res = await engine.generate_response(None, stream=False)
        assert isinstance(res, dict)
        assert "消息列表不能为空" in res.get("content", "")

    @pytest.mark.asyncio
    async def test_message_item_not_dict(self):
        engine = ChatEngine()
        res = await engine.generate_response(["bad"], stream=False)
        assert isinstance(res, dict)
        assert "必须是字典类型" in res.get("content", "")

    @pytest.mark.asyncio
    async def test_memory_included_path(self):
        engine = ChatEngine()
        # mock memory with one item
        engine.async_chat_memory = MagicMock()
        engine.async_chat_memory.get_relevant_memory = AsyncMock(return_value=["memo1"])
        # force include memory
        def fake_compose(base, msgs, mem, tools=None):
            # return a valid OpenAI messages list including a system message
            return [{"role":"system","content":"sys"}] + msgs

        with patch("core.chat_engine.should_include_memory", return_value=True), \
             patch("core.chat_engine.compose_system_prompt", side_effect=fake_compose):
            engine.client = MagicMock()
            engine.client.create_chat = AsyncMock(return_value={"role":"assistant","content":"ok"})
            res = await engine.generate_response([{"role":"user","content":"hi"}], conversation_id="c1", stream=False)
            assert res.get("content") == "ok"
            engine.client.create_chat.assert_called()


