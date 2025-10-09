import types
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_non_streaming_general_exception_without_response_text():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()

    class E(Exception):
        pass

    async def boom(*a, **k):
        raise E('oops')

    engine.client.create_chat = boom

    res = await engine._generate_non_streaming_response(
        {"messages": [{"role": "user", "content": "q"}]},
        "cid",
        [{"role": "user", "content": "q"}],
    )
    assert '抱歉，我现在无法为您提供帮助' in res['content']
    assert 'oops' in res['content']


@pytest.mark.asyncio
async def test_handle_tool_calls_recurses_with_empty_parameters():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()

    # tool_calls where arguments is empty string => parsed to {}
    tool_calls = [{
        "id": "id1",
        "type": "function",
        "function": {"name": "calc", "arguments": ""}
    }]

    with patch('core.chat_engine.normalize_tool_calls', return_value=tool_calls):
        engine.tool_manager.execute_tools_concurrently = AsyncMock(return_value=[{"content": "ok"}])
        with patch('core.chat_engine.build_tool_response_messages', return_value=[{"role": "tool", "content": "ok", "tool_call_id": "id1"}]):
            engine.generate_response = AsyncMock(return_value={"role": "assistant", "content": "done"})
            out = await engine._handle_tool_calls(tool_calls, 'cid', [{"role":"user","content":"q"}])

    assert out.get('content') == 'done'


