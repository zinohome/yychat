import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_mem0_proxy_get_supported_personalities_transform():
    from core.mem0_proxy import Mem0ChatEngine
    engine = Mem0ChatEngine()
    pm = engine.personality_handler.personality_manager
    pm.get_all_personalities = MagicMock(return_value={
        'p1': {'name': 'N1', 'system_prompt': 'desc', 'allowed_tools': [{'tool_name':'a'}]},
        'p2': {'system_prompt': ''}
    })
    res = await engine.get_supported_personalities()
    assert {r['id'] for r in res} == {'p1','p2'}


@pytest.mark.asyncio
async def test_mem0_proxy_get_available_tools_transform_with_personality():
    from core.mem0_proxy import Mem0ChatEngine
    engine = Mem0ChatEngine()
    engine.tool_handler.get_allowed_tools = AsyncMock(return_value=[
        {'function': {'name': 'a', 'description': 'da', 'parameters': {}}},
        {'function': {'name': 'b', 'description': 'db', 'parameters': {}}}
    ])
    out = await engine.get_available_tools('p')
    assert [t['name'] for t in out] == ['a','b']


