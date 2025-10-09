import pytest


@pytest.mark.asyncio
async def test_async_chat_memory_cache_hit(monkeypatch):
    import core.chat_memory as cm

    m = cm.AsyncChatMemory()

    async def fake_retrieve(conversation_id, query, limit):
        return ['m1','m2']

    # Patch internal retrieve to a deterministic result
    m._retrieve_memory = fake_retrieve
    m.config.MEMORY_RETRIEVAL_TIMEOUT = 1

    first = await m.get_relevant_memory('c','q',limit=5)
    assert first == ['m1','m2']

    # Second call should come from cache (same key)
    second = await m.get_relevant_memory('c','q',limit=5)
    assert second == ['m1','m2']


