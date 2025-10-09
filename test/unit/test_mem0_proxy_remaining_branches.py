import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


def test_ensure_collection_exists_unexpected_error_raises(monkeypatch):
    from core.mem0_proxy import Mem0ChatEngine

    engine = Mem0ChatEngine()
    client = MagicMock()
    # unexpected error (not collection missing keywords) -> should raise
    client.search.side_effect = ValueError('boom')
    engine.mem0_client.get_client = MagicMock(return_value=client)

    with pytest.raises(ValueError):
        engine._ensure_collection_exists()


def test_openai_client_init_failure_sets_none(monkeypatch):
    import core.mem0_proxy as mp

    class BrokenOpenAI:
        def __init__(self, *a, **k):
            raise RuntimeError('bad')

    monkeypatch.setattr(mp, 'OpenAI', BrokenOpenAI)
    oc = mp.OpenAIClient(mp.get_config())
    assert oc.get_client() is None


@pytest.mark.asyncio
async def test_response_handler_non_stream_tool_calls_error_path(monkeypatch):
    from core.mem0_proxy import ResponseHandler
    from config.config import get_config

    rh = ResponseHandler(get_config())
    # message includes tool_calls but handler raises
    msg = type('M', (), {'tool_calls': [{}], 'content': None})()
    resp = type('R', (), {'choices':[type('C', (), {'message': msg})()]})()

    rh.tool_handler.handle_tool_calls = AsyncMock(side_effect=Exception('tool fail'))

    out = await rh.handle_non_streaming_response(
        client=type('Client', (), {'chat': type('Ch', (), {'completions': type('Co', (), {'create': lambda **kw: resp})()})()})(),
        call_params={},
        conversation_id='cid',
        original_messages=[{'role':'user','content':'q'}]
    )
    assert '发生内部错误' in out.get('content', '')


@pytest.mark.asyncio
async def test_fallback_handler_streaming_with_tool_calls(monkeypatch):
    from core.mem0_proxy import Mem0ChatEngine

    engine = Mem0ChatEngine()
    # cause Mem0 path to fail and fallback
    engine.get_client = MagicMock(side_effect=Exception('mem0 fail'))

    # OpenAI stream chunks: first with tool_calls, then finish
    class ToolCall:
        def __init__(self):
            self.index = 0
            self.id = None
            self.function = type('F', (), {'name':'calc', 'arguments':'{"x":1}'})()

    class Choice:
        def __init__(self, delta, finish_reason=None):
            self.delta = delta
            self.finish_reason = finish_reason

    class Delta:
        def __init__(self, tool_calls=None, content=None):
            self.tool_calls = tool_calls
            self.content = content

    async def stream_gen():
        yield type('Chunk', (), {'choices':[Choice(Delta([ToolCall()]))]})()
        yield type('Chunk', (), {'choices':[Choice(Delta(None), finish_reason='stop')]})()

    co = type('Co', (), {})()
    co.create = (lambda **kw: stream_gen())
    client = type('X', (), {})()
    client.chat = type('Ch', (), {'completions': co})()
    engine.fallback_handler.openai_client.get_client = MagicMock(return_value=client)

    # make streaming tool handler return a couple chunks
    async def tool_stream(*a, **k):
        yield {'role':'assistant','content':'t1','finish_reason':None,'stream':True}
        yield {'role':'assistant','content':'','finish_reason':'stop','stream':True}

    engine.fallback_handler.tool_handler.handle_streaming_tool_calls = tool_stream

    gen = await engine.generate_response([{'role':'user','content':'q'}], 'cid', stream=True)
    outs = []
    async for item in gen:
        outs.append(item)
    assert any(i.get('content') == 't1' for i in outs)
    assert any(i.get('finish_reason') == 'stop' for i in outs)


@pytest.mark.asyncio
async def test_response_handler_streaming_save_path(monkeypatch):
    from core.mem0_proxy import ResponseHandler
    from config.config import get_config

    rh = ResponseHandler(get_config())
    # stream content delta then finish without tools -> save and stop
    class Choice:
        def __init__(self, delta, finish_reason=None):
            self.delta = delta
            self.finish_reason = finish_reason

    class Delta:
        def __init__(self, tool_calls=None, content=None):
            self.tool_calls = tool_calls
            self.content = content

    async def stream_gen():
        yield type('Chunk', (), {'choices':[Choice(Delta(None, 'abc'))]})()
        yield type('Chunk', (), {'choices':[Choice(Delta(None), finish_reason='stop')]})()

    rh.memory_handler.save_memory = AsyncMock()

    co = type('Co', (), {})()
    co.create = (lambda **kw: stream_gen())
    client = type('X', (), {})()
    client.chat = type('Ch', (), {'completions': co})()

    outs = []
    async for item in rh.handle_streaming_response(client, {}, 'cid', [{'role':'user','content':'q'}]):
        outs.append(item)
    assert outs and outs[-1]['finish_reason'] == 'stop'
    rh.memory_handler.save_memory.assert_awaited()


@pytest.mark.asyncio
async def test_health_check_all_healthy_paths(monkeypatch):
    from core.mem0_proxy import Mem0ChatEngine
    engine = Mem0ChatEngine()

    # mem0 client exists and collection search ok
    mc = MagicMock()
    mc.search = MagicMock(return_value=None)
    engine.mem0_client.get_client = MagicMock(return_value=mc)

    # openai healthy
    engine.openai_client.get_client = MagicMock(return_value=object())

    # tools healthy
    engine.tool_handler.get_allowed_tools = AsyncMock(return_value=[{'function': {'name':'a'}}])

    # personalities healthy
    pm = engine.personality_handler.personality_manager
    pm.get_all_personalities = MagicMock(return_value={'p':{}})

    res = await engine.health_check()
    assert res['healthy'] is True
    assert all(res['details'].values())


