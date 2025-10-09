import pytest
from unittest.mock import MagicMock, AsyncMock, patch


def test_get_allowed_tools_schema_no_personality(monkeypatch):
    from core.chat_engine import ChatEngine, tool_registry
    engine = ChatEngine()
    # tool registry returns two schemas
    monkeypatch.setattr(tool_registry, 'get_functions_schema', lambda: [
        {'function': {'name': 'a'}}, {'function': {'name': 'b'}}
    ])

    # no personality -> return all
    res = asyncio_run(engine.get_allowed_tools_schema(None))
    assert len(res) == 2


def asyncio_run(coro):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)


def test_get_allowed_tools_schema_with_personality_filter(monkeypatch):
    from core.chat_engine import ChatEngine, tool_registry
    engine = ChatEngine()
    monkeypatch.setattr(tool_registry, 'get_functions_schema', lambda: [
        {'function': {'name': 'a'}}, {'function': {'name': 'b'}}, {'function': {'name': 'c'}}
    ])
    personality = MagicMock()
    personality.allowed_tools = [{'tool_name': 'b'}]
    engine.personality_manager.get_personality = MagicMock(return_value=personality)

    res = asyncio_run(engine.get_allowed_tools_schema('p'))
    assert [t['function']['name'] for t in res] == ['b']


def test_get_allowed_tools_schema_malformed_allowed_tools(monkeypatch):
    from core.chat_engine import ChatEngine, tool_registry
    engine = ChatEngine()
    monkeypatch.setattr(tool_registry, 'get_functions_schema', lambda: [
        {'function': {'name': 'a'}}, {'function': {'name': 'b'}}
    ])
    personality = MagicMock()
    personality.allowed_tools = [{}]  # malformed
    engine.personality_manager.get_personality = MagicMock(return_value=personality)

    res = asyncio_run(engine.get_allowed_tools_schema('p'))
    # fallback to all tools
    assert len(res) == 2


def test_get_allowed_tools_schema_exception_returns_empty(monkeypatch):
    from core.chat_engine import ChatEngine, tool_registry
    engine = ChatEngine()
    def boom():
        raise RuntimeError('x')
    monkeypatch.setattr(tool_registry, 'get_functions_schema', boom)
    res = asyncio_run(engine.get_allowed_tools_schema('p'))
    assert res == []


@pytest.mark.asyncio
async def test_health_check_errors(monkeypatch):
    from core.chat_engine import ChatEngine, tool_registry
    engine = ChatEngine()
    # force tool_registry.list_tools to raise
    monkeypatch.setattr(tool_registry, 'list_tools', lambda: (_ for _ in ()).throw(RuntimeError('t')))
    # personality manager get_all_personalities raises
    engine.personality_manager.get_all_personalities = MagicMock(side_effect=Exception('p'))
    res = await engine.health_check()
    assert res['details']['tool_system'] is False
    assert res['details']['personality_system'] is False


@pytest.mark.asyncio
async def test_call_mcp_service_error_paths(monkeypatch):
    from core.chat_engine import ChatEngine, mcp_manager
    engine = ChatEngine()
    # server not found
    from services.mcp import exceptions as ex
    with patch.object(mcp_manager, 'call_tool', side_effect=ex.MCPServerNotFoundError('s')):
        out = await engine.call_mcp_service(tool_name='x')
        assert out['success'] is False
    # tool not found
    with patch.object(mcp_manager, 'call_tool', side_effect=ex.MCPToolNotFoundError('t')):
        out = await engine.call_mcp_service(tool_name='x')
        assert out['success'] is False
    # service error
    with patch.object(mcp_manager, 'call_tool', side_effect=ex.MCPServiceError('e')):
        out = await engine.call_mcp_service(tool_name='x')
        assert out['success'] is False
    # unexpected
    with patch.object(mcp_manager, 'call_tool', side_effect=Exception('u')):
        out = await engine.call_mcp_service(tool_name='x')
        assert out['success'] is False


