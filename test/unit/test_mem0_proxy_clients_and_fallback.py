import asyncio
import types
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


def test_mem0_client_init_local_with_filters_patch(monkeypatch):
    # Patch Mem0 class used in core.mem0_proxy
    import core.mem0_proxy as mp

    class FakeInnerClient:
        def __init__(self):
            self.called_with_filters = False
        def add(self, *args, **kwargs):
            # if filters is present after patching, this would fail; track flag
            if 'filters' in kwargs:
                self.called_with_filters = True
            return 'ok'

    class FakeMem0:
        def __init__(self, config=None, api_key=None):
            self.config = config
            self.api_key = api_key
            self.mem0_client = FakeInnerClient()

    monkeypatch.setattr(mp, 'Mem0', FakeMem0)

    # Force local mode
    cfg = mp.get_config()
    cfg.MEMO_USE_LOCAL = True

    c = mp.Mem0Client(cfg)
    client = c.get_client()

    # After init, mem0_client.add should be patched to drop 'filters'
    # Call with filters to ensure it does not raise and does not mark flag
    client.mem0_client.add(x=1, filters={'k': 'v'})
    assert client.mem0_client.called_with_filters is False


def test_mem0_client_init_api_mode(monkeypatch):
    import core.mem0_proxy as mp

    class FakeMem0:
        def __init__(self, config=None, api_key=None):
            self.config = config
            self.api_key = api_key

    monkeypatch.setattr(mp, 'Mem0', FakeMem0)

    cfg = mp.get_config()
    cfg.MEMO_USE_LOCAL = False
    cfg.MEM0_API_KEY = 'k'

    c = mp.Mem0Client(cfg)
    client = c.get_client()
    assert isinstance(client, FakeMem0)
    assert client.api_key == 'k'


def test_get_client_caching(monkeypatch):
    from core.mem0_proxy import Mem0ChatEngine
    engine = Mem0ChatEngine()
    first = engine.get_client('u1')
    second = engine.get_client('u1')
    assert first is second


@pytest.mark.asyncio
async def test_response_handler_non_iterable_error_branch(monkeypatch):
    from core.mem0_proxy import ResponseHandler
    from config.config import get_config

    rh = ResponseHandler(get_config())

    # Return a non-iterable, non-async-iterable object from API
    class NotIterable:
        pass

    client = type('Client', (), {'chat': type('Ch', (), {'completions': type('Co', (), {'create': lambda **kw: NotIterable()})()})()})()

    outs = []
    async for item in rh.handle_streaming_response(client, {}, 'cid', [{'role':'user','content':'q'}]):
        outs.append(item)
    assert outs and outs[-1]['finish_reason'] == 'error'


@pytest.mark.asyncio
async def test_fallback_handler_use_tools_non_stream(monkeypatch):
    from core.mem0_proxy import Mem0ChatEngine
    engine = Mem0ChatEngine()

    # Make Mem0 raise to trigger fallback
    engine.get_client = MagicMock(side_effect=Exception('no mem0'))

    # Mock OpenAI client to return simple non-stream response
    resp = type('R', (), {'choices':[type('C', (), {'message': type('M', (), {'content':'ok', 'tool_calls': None})()})()]})()

    client = type('X', (), {})()
    co = type('Co', (), {})()
    co.create = (lambda **kw: resp)
    ch = type('Ch', (), {})()
    ch.completions = co
    client.chat = ch
    engine.fallback_handler.openai_client.get_client = MagicMock(return_value=client)

    # Tools allowed: ensure handler sets them and still returns content
    engine.fallback_handler.tool_handler.get_allowed_tools = AsyncMock(return_value=[{'function': {'name':'a'}}])

    out = await engine.generate_response([{'role':'user','content':'q'}], 'cid', use_tools=True, stream=False)
    assert out.get('content') == 'ok'


