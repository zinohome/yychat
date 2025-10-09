"""
More branch coverage for core/mem0_proxy.py (pure mocks)
"""
import pytest
from unittest.mock import MagicMock

from core.mem0_proxy import Mem0ChatEngine


class TestMem0ProxyMoreBranches:
    @pytest.mark.asyncio
    async def test_get_engine_info_shape(self):
        eng = Mem0ChatEngine()
        info = await eng.get_engine_info()
        assert isinstance(info, dict)
        assert "name" in info and "features" in info

    @pytest.mark.asyncio
    async def test_get_supported_personalities(self):
        eng = Mem0ChatEngine()
        eng.personality_handler = MagicMock()
        eng.personality_handler.personality_manager = MagicMock()
        eng.personality_handler.personality_manager.list_personalities.return_value = [{"id":"p1"}]
        ps = await eng.get_supported_personalities()
        assert isinstance(ps, list)


