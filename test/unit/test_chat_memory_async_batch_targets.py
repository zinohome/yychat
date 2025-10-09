import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_async_add_messages_batch_local_and_api_modes(monkeypatch):
    import core.chat_memory as cm

    m = cm.AsyncChatMemory()
    # Fake memory with add as async
    class F:
        async def add(self, *a, **k):
            return 'ok'

    m.memory = F()

    # Local mode: use content directly
    m.is_local = True
    await m.add_messages_batch('cid', [
        {"role": "user", "content": "u", "timestamp": None},
        {"role": "assistant", "content": "a", "timestamp": 1}
    ])

    # API mode: uses messages list path
    m.is_local = False
    await m.add_messages_batch('cid', [
        {"role": "user", "content": "u"},
        {"role": "assistant", "content": "a"}
    ])


