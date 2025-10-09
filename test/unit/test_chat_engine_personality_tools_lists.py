import pytest
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_get_supported_personalities_transform():
    from core.chat_engine import ChatEngine
    engine = ChatEngine()
    engine.personality_manager.get_all_personalities = MagicMock(return_value={
        'p1': {'name': 'N1', 'system_prompt': 'desc', 'allowed_tools': [{'tool_name':'a'}]},
        'p2': {'system_prompt': ''}
    })
    res = await engine.get_supported_personalities()
    assert {r['id'] for r in res} == {'p1','p2'}


@pytest.mark.asyncio
async def test_get_allowed_tools_schema_no_restriction_returns_all(monkeypatch):
    from core.chat_engine import ChatEngine, tool_registry
    engine = ChatEngine()
    monkeypatch.setattr(tool_registry, 'get_functions_schema', lambda: [
        {'function': {'name': 'a'}}, {'function': {'name': 'b'}}
    ])
    engine.personality_manager.get_personality = MagicMock(return_value=type('P', (), {'allowed_tools': []})())
    res = await engine.get_allowed_tools_schema('p')
    assert len(res) == 2


