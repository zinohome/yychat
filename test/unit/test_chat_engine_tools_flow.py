"""
ChatEngine tools flow tests
Covers _handle_tool_calls JSON error handling and non-streaming tool request building
"""
import pytest
from unittest.mock import AsyncMock, patch

from core.chat_engine import ChatEngine


@pytest.mark.asyncio
class TestChatEngineToolsFlow:
    async def test_handle_tool_calls_invalid_json_args(self):
        engine = ChatEngine()
        # mock tool_manager to avoid real tool execution
        engine.tool_manager.execute_tools_concurrently = AsyncMock(return_value=[{
            "tool_name": "calc",
            "success": True,
            "result": {"ok": 1}
        }])
        # Build a normalized tool call with invalid JSON arguments
        tool_calls = [{
            "id": "t1",
            "type": "function",
            "function": {"name": "calc", "arguments": "{invalid json"}
        }]
        original_messages = [{"role": "user", "content": "compute"}]
        # Mock recursive generate_response to stop at one level
        with patch.object(engine, "generate_response", new=AsyncMock(return_value={"role": "assistant", "content": "done"})):
            out = await engine._handle_tool_calls(tool_calls, "conv_tools", original_messages, personality_id=None)
        assert isinstance(out, dict)
        assert out.get("content") == "done"

    async def test_non_streaming_with_tools_and_allowed_filter(self):
        engine = ChatEngine()
        messages = [{"role": "user", "content": "现在几点?"}]
        # Force use_tools True and mock tool schema/manager
        with patch("core.chat_engine.tool_registry.get_functions_schema", return_value=[{"function": {"name": "gettime"}}, {"function": {"name": "other"}}]):
            # Mock OpenAI wrapper create_chat once to return a simple response without tool_calls
            fake_response = type("R", (), {"choices": [type("C", (), {"message": type("M", (), {"content": "ok", "tool_calls": None})()})()]})()
            with patch.object(engine.client, "create_chat", new=AsyncMock(return_value=fake_response)):
                out = await engine.generate_response(messages, conversation_id="conv_nonstream", personality_id="friendly", use_tools=True, stream=False)
        assert isinstance(out, dict)
        assert "content" in out
