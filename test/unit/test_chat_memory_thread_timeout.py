import threading
import time


def test_chat_memory_get_relevant_memory_thread_timeout(monkeypatch):
    from core.chat_memory import ChatMemory

    class SlowMem:
        def get_relevant(self, *a, **k):
            time.sleep(0.2)
            return [{'content':'z'}]

    cm = ChatMemory(memory=SlowMem())
    cm.config.MEMORY_RETRIEVAL_TIMEOUT = 0.05

    res = cm.get_relevant_memory('c', 'q', limit=5)
    # timeout -> empty list
    assert res == []


