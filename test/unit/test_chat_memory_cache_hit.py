import time


def test_chat_memory_get_relevant_memory_cache_hit(monkeypatch):
    from core.chat_memory import ChatMemory

    class FakeMem:
        def __init__(self):
            self.calls = 0
        def get(self, query, user_id=None):
            self.calls += 1
            return [{'content': 'a'}, {'content': 'b'}]

    cm = ChatMemory(memory=FakeMem())
    cm.config.MEMORY_RETRIEVAL_TIMEOUT = 1

    # First call populates cache
    r1 = cm.get_relevant_memory('c1', 'hello world', limit=5)
    assert r1 == ['a', 'b']

    # Second call should hit cache (no additional memory.get call)
    before = cm.memory.calls
    r2 = cm.get_relevant_memory('c1', 'hello world', limit=5)
    after = cm.memory.calls
    assert r2 == ['a', 'b']
    assert after == before


