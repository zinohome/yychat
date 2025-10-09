import types
import pytest


@pytest.mark.asyncio
async def test_streaming_mid_iteration_error_yields_error():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()

    async def gen():
        # first normal chunk
        yield types.SimpleNamespace(choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content='x'))])
        # then raise
        raise RuntimeError('mid fail')

    engine.client.create_chat_stream = lambda *a, **k: gen()

    outs = []
    async for item in engine._generate_streaming_response({'messages':[{'role':'user','content':'q'}]}, 'cid', [{'role':'user','content':'q'}]):
        outs.append(item)
    # The last emitted should be error finish_reason
    assert outs[-1]['finish_reason'] == 'error'


