import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_mem0_proxy_get_available_tools_transform():
    from core.mem0_proxy import Mem0ChatEngine

    engine = Mem0ChatEngine()
    # Tool handler returns OpenAI schema
    engine.tool_handler.get_allowed_tools = AsyncMock(return_value=[
        {'function': {'name': 'calc', 'description': 'd', 'parameters': {'type': 'object'}}},
        {'function': {'name': 'time', 'description': 't', 'parameters': {}}}
    ])

    out = await engine.get_available_tools()
    assert out == [
        {'name': 'calc', 'description': 'd', 'parameters': {'type': 'object'}},
        {'name': 'time', 'description': 't', 'parameters': {}}
    ]


