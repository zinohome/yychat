import types
import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_non_streaming_response_exception_with_response_text():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()

    class Err(Exception):
        def __init__(self):
            self.response = type('R', (), {'text': 'bad json'})()

    async def boom(*a, **k):
        raise Err()

    engine.client.create_chat = boom

    res = await engine._generate_non_streaming_response(
        {"messages": [{"role": "user", "content": "hi"}]},
        "cid",
        [{"role":"user","content":"hi"}],
    )
    assert '抱歉，我现在无法为您提供帮助' in res['content']
    assert 'bad json' in res['content']


@pytest.mark.asyncio
async def test_generate_response_streaming_error_generator():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()

    # Force an exception before returning stream
    async def broken(*a, **k):
        raise RuntimeError('fail')
    engine.client.create_chat_stream = broken

    gen = await engine.generate_response(messages=[{"role":"user","content":"q"}], conversation_id='cid', stream=True)

    outs = []
    async for item in gen:
        outs.append(item)
    assert outs and outs[0]['finish_reason'] == 'error'


