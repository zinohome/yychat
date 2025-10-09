import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_handle_tool_calls_followup_variant():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()

    tool_calls = [{
        'id': 'id1',
        'type': 'function',
        'function': {'name': 'calc', 'arguments': '{"x":1}'}
    }]

    with patch('core.chat_engine.normalize_tool_calls', return_value=tool_calls):
        engine.tool_manager.execute_tools_concurrently = AsyncMock(return_value=[{'content':'ok'}])
        with patch('core.chat_engine.build_tool_response_messages', return_value=[{'role':'tool','content':'ok','tool_call_id':'id1'}]):
            engine.generate_response = AsyncMock(return_value={'role':'assistant','content':'final2'})
            out = await engine._handle_tool_calls(tool_calls, 'cid', [{'role':'user','content':'q'}])

    assert out['content'] == 'final2'
