"""
Branch coverage tests for core/chat_memory.py using pure mocks
"""
import pytest
from unittest.mock import MagicMock

from core.chat_memory import ChatMemory


class TestChatMemoryBranches:
    def test_get_relevant_memory_empty_and_errors(self):
        m = ChatMemory()
        m.memory = MagicMock()
        # empty result
        m.memory.search.return_value = []
        assert m.get_relevant_memory("u", "q") == []
        # None result
        m.memory.search.return_value = None
        assert m.get_relevant_memory("u", "q") == []
        # error result
        m.memory.search.side_effect = Exception("x")
        assert m.get_relevant_memory("u", "q") == []

    def test_cache_key_variation(self):
        m = ChatMemory()
        m.memory = MagicMock()
        # ensure non-empty to avoid early returns masking calls
        m.memory.search.return_value = [{"content":"a"}]
        # use different queries to avoid cache hit
        r1 = m.get_relevant_memory("u1","q1")
        r2 = m.get_relevant_memory("u1","q2")
        assert isinstance(r1, list)
        assert isinstance(r2, list)


