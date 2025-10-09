import types
import pytest


@pytest.mark.asyncio
async def test_streaming_small_content_pass_through():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()
    chunk = types.SimpleNamespace(choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content='ok'))])

    async def gen():
        yield chunk

    engine.client.create_chat_stream = lambda *a, **k: gen()

    outs = []
    async for item in engine._generate_streaming_response({'messages':[{'role':'user','content':'q'}]}, 'cid', [{'role':'user','content':'q'}]):
        outs.append(item)
    assert any(i.get('content') == 'ok' for i in outs)
