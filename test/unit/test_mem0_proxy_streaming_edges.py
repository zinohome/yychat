import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_response_handler_stream_multiple_finish_and_none_content_chunks():
    from core.mem0_proxy import ResponseHandler
    from config.config import get_config

    rh = ResponseHandler(get_config())

    class Choice:
        def __init__(self, delta, finish_reason=None):
            self.delta = delta
            self.finish_reason = finish_reason

    class Delta:
        def __init__(self, tool_calls=None, content=None):
            self.tool_calls = tool_calls
            self.content = content

    async def stream_gen():
        # None content chunk
        yield type('Chunk', (), {'choices':[Choice(Delta(None, None))]})()
        # content chunk
        yield type('Chunk', (), {'choices':[Choice(Delta(None, 'x'))]})()
        # extra finish before final
        yield type('Chunk', (), {'choices':[Choice(Delta(None), finish_reason=None)]})()
        # final stop
        yield type('Chunk', (), {'choices':[Choice(Delta(None), finish_reason='stop')]})()

    co = type('Co', (), {})()
    co.create = (lambda **kw: stream_gen())
    client = type('X', (), {})()
    client.chat = type('Ch', (), {'completions': co})()

    rh.memory_handler.save_memory = AsyncMock()

    outs = []
    async for item in rh.handle_streaming_response(client, {}, 'cid', [{'role':'user','content':'q'}]):
        outs.append(item)
    assert any(i.get('content') == 'x' for i in outs)
    assert outs[-1]['finish_reason'] == 'stop'


