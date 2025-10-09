import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_fallback_nonstream_with_tool_calls():
    from core.mem0_proxy import Mem0ChatEngine

    engine = Mem0ChatEngine()
    engine.get_client = MagicMock(side_effect=Exception('mem0 down'))

    # OpenAI response with tool_calls triggers tool_handler path
    msg = type('M', (), {'tool_calls': [{}], 'content': None})()
    resp = type('R', (), {'choices':[type('C', (), {'message': msg})()]})()

    client = type('X', (), {})()
    co = type('Co', (), {})()
    co.create = (lambda **kw: resp)
    client.chat = type('Ch', (), {'completions': co})()
    engine.fallback_handler.openai_client.get_client = MagicMock(return_value=client)

    engine.fallback_handler.tool_handler.handle_tool_calls = AsyncMock(return_value={'role':'assistant','content':'after tool'})

    out = await engine.generate_response([{'role':'user','content':'q'}], 'cid', use_tools=True, stream=False)
    assert out.get('content') == 'after tool'
