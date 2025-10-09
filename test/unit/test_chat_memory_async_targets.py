import asyncio
import pytest
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_async_get_relevant_memory_timeout_and_exception(monkeypatch):
    import core.chat_memory as cm

    m = cm.AsyncChatMemory()

    # set very small timeout
    m.config.MEMORY_RETRIEVAL_TIMEOUT = 0.01

    async def slow(*a, **k):
        await asyncio.sleep(0.2)
        return []

    # force path to use memory.get_relevant
    m.memory = MagicMock()
    m.memory.get_relevant = slow

    res_timeout = await m.get_relevant_memory('cid', 'q')
    assert res_timeout == []

    async def raise_err(*a, **k):
        raise RuntimeError('boom')

    m.config.MEMORY_RETRIEVAL_TIMEOUT = 1
    m.memory.get_relevant = raise_err

    res_err = await m.get_relevant_memory('cid', 'q')
    assert res_err == []


