import pytest
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_get_available_tools_with_and_without_personality(monkeypatch):
    from core.chat_engine import ChatEngine, tool_registry
    engine = ChatEngine()

    class T:
        def __init__(self, name):
            self.name = name
            self.description = name
            self.parameters = {}
    # registry list_tools returns dict of classes
    class ToolA:
        def __init__(self):
            self.name = 'a'; self.description = 'a'; self.parameters = {}
    class ToolB:
        def __init__(self):
            self.name = 'b'; self.description = 'b'; self.parameters = {}

    monkeypatch.setattr(tool_registry, 'list_tools', lambda: {'a': ToolA, 'b': ToolB})

    # no personality: returns all
    res_all = await engine.get_available_tools()
    assert {t['name'] for t in res_all} == {'a','b'}

    # with personality filter
    engine.personality_manager.get_personality = MagicMock(return_value={
        'allowed_tools': [{'tool_name': 'b'}]
    })
    res_f = await engine.get_available_tools('p')
    assert [t['name'] for t in res_f] == ['b']


@pytest.mark.asyncio
async def test_async_clear_and_get_conversation_memory_success_and_error(monkeypatch):
    from core.chat_engine import ChatEngine
    from unittest.mock import AsyncMock
    engine = ChatEngine()
    # success path
    engine.async_chat_memory.get_all_memory = AsyncMock(return_value=[{'content': 'x'}])
    engine.async_chat_memory.clear_conversation = MagicMock()
    ok = await engine.clear_conversation_memory('cid')
    assert ok['success'] is True and ok['deleted_count'] == 1

    # error path
    engine.async_chat_memory.get_all_memory = AsyncMock(side_effect=Exception('err'))
    bad = await engine.clear_conversation_memory('cid')
    assert bad['success'] is False

    # get_conversation_memory limit
    engine.async_chat_memory.get_all_memory = AsyncMock(return_value=[1,2,3])
    got = await engine.get_conversation_memory('cid', limit=2)
    assert got['returned_count'] == 2

    # get_conversation_memory error
    engine.async_chat_memory.get_all_memory = AsyncMock(side_effect=Exception('e'))
    got_err = await engine.get_conversation_memory('cid')
    assert got_err['success'] is False


