"""
Branch coverage tests for core/mem0_proxy.py using pure mocks
"""
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from core.mem0_proxy import Mem0ChatEngine


class TestMem0ProxyBranches:
    def test_init_calls_collection_check(self):
        with patch.object(Mem0ChatEngine, "_ensure_collection_exists") as mock_check:
            Mem0ChatEngine()
            assert mock_check.called

    @pytest.mark.asyncio
    async def test_handle_tool_calls_error_guard(self):
        eng = Mem0ChatEngine()
        # replace handler with mocked behavior raising
        eng.tool_handler = MagicMock()
        eng.tool_handler.tool_manager = MagicMock()
        eng.tool_handler.tool_manager.execute_tools_concurrently = AsyncMock(side_effect=Exception("boom"))
        # directly import internal handler for simplicity via engine forward
        from core.mem0_proxy import ToolHandler
        handler = ToolHandler(MagicMock())
        handler.tool_manager = MagicMock()
        handler.tool_manager.execute_tools_concurrently = AsyncMock(side_effect=Exception("boom"))
        res = await handler.handle_tool_calls([{"id":"1","function":{"name":"x","arguments":"{}"}}], "cid", [])
        assert "出错" in res["content"]

    @pytest.mark.asyncio
    async def test_health_check_collection_false(self):
        eng = Mem0ChatEngine()
        eng.mem0_client = MagicMock()
        client = MagicMock()
        client.search.side_effect = Exception("Collection does not exists")
        eng.mem0_client.get_client.return_value = client
        hc = await eng.health_check()
        assert isinstance(hc, dict)


