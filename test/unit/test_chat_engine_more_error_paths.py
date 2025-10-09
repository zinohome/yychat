import types
import json
import pytest


@pytest.mark.asyncio
async def test_non_streaming_json_decode_error():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()

    class FakeResp:
        pass

    async def bad(*a, **k):
        raise json.JSONDecodeError('x', 'y', 0)

    engine.client.create_chat = bad
    res = await engine._generate_non_streaming_response({"messages":[{"role":"user","content":"q"}]}, 'cid', [{"role":"user","content":"q"}])
    assert 'API返回内容格式错误' in res['content']


@pytest.mark.asyncio
async def test_non_streaming_missing_content_branch():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()
    msg = types.SimpleNamespace(content=None)
    resp = types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])
    async def ok(*a, **k):
        return resp
    engine.client.create_chat = ok
    res = await engine._generate_non_streaming_response({"messages":[{"role":"user","content":"q"}]}, 'cid', [{"role":"user","content":"q"}])
    assert 'AI响应内容为空' in res['content']


