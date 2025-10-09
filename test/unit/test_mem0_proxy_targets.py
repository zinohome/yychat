import asyncio
import types
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_mem0_health_check_collection_missing():
    from core.mem0_proxy import Mem0ChatEngine

    engine = Mem0ChatEngine()
    client = MagicMock()
    engine.mem0_client.get_client = MagicMock(return_value=client)

    # search raises collection missing error
    client.search.side_effect = Exception("Collection does not exists")

    result = await engine.health_check()
    assert result["details"]["mem0_collection"] is False
    assert any("Collection不存在" in e for e in result["errors"]) or result["errors"]


@pytest.mark.asyncio
async def test_handle_streaming_tool_calls_success_and_error():
    from core.mem0_proxy import ToolHandler
    from config.config import get_config

    th = ToolHandler(get_config())

    # First, success path
    th.handle_tool_calls = AsyncMock(return_value={"content": "abcdef"})
    chunks = []
    async for c in th.handle_streaming_tool_calls([{"f":1}], "cid", [{"role":"user","content":"q"}]) :
        chunks.append(c)
    assert ''.join(x['content'] for x in chunks) == 'abcdef'

    # Error path
    th.handle_tool_calls = AsyncMock(side_effect=Exception("boom"))
    chunks = []
    async for c in th.handle_streaming_tool_calls([{"f":1}], "cid", [{"role":"user","content":"q"}]) :
        chunks.append(c)
    assert chunks[-1]["finish_reason"] == "error"


