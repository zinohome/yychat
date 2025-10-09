import pytest
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_mem0_proxy_fallback_openai_stream_and_non_stream(monkeypatch):
    from core.mem0_proxy import Mem0ChatEngine

    engine = Mem0ChatEngine()
    # Make mem0 client None to trigger fallback
    engine.get_client = MagicMock(return_value=None)

    # Mock fallback openai client streaming/non-streaming
    fh = engine.fallback_handler

    class SimpleChunk:
        def __init__(self, text):
            self.choices = [type('C', (), {'delta': type('D', (), {'content': text})(), 'finish_reason': None})()]

    async def stream_gen():
        yield SimpleChunk('a')
        yield SimpleChunk('b')

    fh.openai_client.get_client = MagicMock(return_value=type('X', (), {'chat': type('Ch', (), {'completions': type('Co', (), {'create': lambda **kw: stream_gen()})()})()})())

    # Stream true -> returns async generator
    gen = await engine.generate_response([{"role":"user","content":"q"}], "cid", stream=True)
    outs = []
    async for x in gen:
        outs.append(x)
    assert ''.join(i['content'] for i in outs if i['content']) == 'ab'

    # Non-stream -> returns dict
    fh.openai_client.get_client = MagicMock(return_value=type('X', (), {'chat': type('Ch', (), {'completions': type('Co', (), {'create': lambda **kw: type('R', (), {'choices':[type('M', (), {'message': type('Msg', (), {'content':'ok'})()})()]})()})()})()})())
    res = await engine.generate_response([{"role":"user","content":"q"}], "cid", stream=False)
    assert res.get('content') == 'ok'


