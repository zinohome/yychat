import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_response_handler_non_stream_no_tools_saves_memory():
    from core.mem0_proxy import ResponseHandler
    from config.config import get_config

    rh = ResponseHandler(get_config())

    # Fake client returning non-stream response with content and no tools
    msg = type('M', (), {'content': 'hello', 'tool_calls': None})()
    resp = type('R', (), {'choices': [type('C', (), {'message': msg})()]})()

    # Avoid real memory; just spy
    rh.memory_handler.save_memory = AsyncMock()

    # Build instance graph with instance-level create
    co = type('Co', (), {})()
    co.create = (lambda **kw: resp)
    ch = type('Ch', (), {})()
    ch.completions = co
    client = type('Client', (), {})()
    client.chat = ch

    out = await rh.handle_non_streaming_response(
        client=client,
        call_params={},
        conversation_id='cid',
        original_messages=[{'role':'user','content':'q'}]
    )

    assert out.get('content') == 'hello'
    rh.memory_handler.save_memory.assert_awaited()


@pytest.mark.asyncio
async def test_health_check_mixed_unhealthy_states():
    from core.mem0_proxy import Mem0ChatEngine

    engine = Mem0ChatEngine()
    # Mem0 client ok but collection unhealthy
    mc = MagicMock()
    engine.mem0_client.get_client = MagicMock(return_value=mc)
    mc.search.side_effect = Exception('Collection not found')

    # OpenAI client unhealthy
    engine.openai_client.get_client = MagicMock(return_value=None)

    # Tool handler unhealthy
    engine.tool_handler.get_allowed_tools = AsyncMock(side_effect=Exception('tool'))

    # Personality manager unhealthy
    pm = engine.personality_handler.personality_manager
    pm.get_all_personalities = MagicMock(side_effect=Exception('p'))

    res = await engine.health_check()
    assert res['details']['mem0_collection'] is False
    assert res['details']['openai_client'] is False
    assert res['details']['tool_system'] is False
    assert res['details']['personality_system'] is False


