import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_handle_tool_calls_recurses_and_returns_final_result():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()

    # normalized tool_calls
    tool_calls = [{
        "id": "id1",
        "type": "function",
        "function": {"name": "calc", "arguments": "{\"x\":1}"}
    }]

    # Patch normalize to avoid JSON parsing differences
    with patch("core.chat_engine.normalize_tool_calls", return_value=tool_calls):
        # Tools return
        engine.tool_manager.execute_tools_concurrently = AsyncMock(return_value=[{"content": "ok"}])

        # Build tool response messages passthrough
        with patch("core.chat_engine.build_tool_response_messages", return_value=[{"role":"tool","content":"ok","tool_call_id":"id1"}]):
            # When _handle_tool_calls calls generate_response again, return final dict
            with patch.object(engine, "generate_response", new=AsyncMock(return_value={"role":"assistant","content":"final"})):
                out = await engine._handle_tool_calls(
                    tool_calls,
                    conversation_id="cid",
                    original_messages=[{"role":"user","content":"q"}],
                    personality_id=None
                )

    assert out.get("content") == "final"


