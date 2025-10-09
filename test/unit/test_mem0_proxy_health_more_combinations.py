import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_health_check_mem0_healthy_openai_unhealthy_tools_ok_personas_ok():
    from core.mem0_proxy import Mem0ChatEngine
    engine = Mem0ChatEngine()

    mc = MagicMock()
    mc.search = MagicMock(return_value=None)
    engine.mem0_client.get_client = MagicMock(return_value=mc)

    engine.openai_client.get_client = MagicMock(return_value=None)

    engine.tool_handler.get_allowed_tools = AsyncMock(return_value=[{'function': {'name':'a'}}])
    pm = engine.personality_handler.personality_manager
    pm.get_all_personalities = MagicMock(return_value={'p':{}})

    res = await engine.health_check()
    assert res['details']['mem0_client'] is True
    assert res['details']['openai_client'] is False
    assert res['details']['tool_system'] is True
    assert res['details']['personality_system'] is True
