def test_chat_memory_get_relevant_memory_exception_returns_empty(monkeypatch):
    from core.chat_memory import ChatMemory

    class ErrMem:
        def get_relevant(self, *a, **k):
            raise RuntimeError('err')

    cm = ChatMemory(memory=ErrMem())
    out = cm.get_relevant_memory('c', 'q', limit=3)
    assert out == []


