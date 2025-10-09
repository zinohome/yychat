import types
import sys
import pytest
from unittest.mock import MagicMock


def test_chat_memory_init_local_and_api_modes(monkeypatch):
    import core.chat_memory as cm
    from core.chat_memory import ChatMemory

    # Prepare fake mem0 modules for local mode
    fake_mem0 = types.ModuleType("mem0")
    class FakeMemory:
        def __init__(self, config=None):
            self.config = config
    fake_mem0.Memory = FakeMemory

    fake_configs_base = types.ModuleType("mem0.configs.base")
    class FakeMemoryConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
    fake_configs_base.MemoryConfig = FakeMemoryConfig

    sys.modules["mem0"] = fake_mem0
    sys.modules["mem0.configs.base"] = fake_configs_base

    # Local mode config
    local_cfg = type("C", (), {
        "MEMO_USE_LOCAL": True,
        "MEM0_LLM_PROVIDER": "openai",
        "MEM0_LLM_CONFIG_MODEL": "gpt",
        "MEM0_LLM_CONFIG_MAX_TOKENS": 256,
        "CHROMA_COLLECTION_NAME": "c",
        "CHROMA_PERSIST_DIRECTORY": "/tmp"
    })()
    monkeypatch.setattr(cm, "get_config", lambda: local_cfg)

    cm_local = ChatMemory()
    assert cm_local.is_local is True
    assert hasattr(cm_local, "memory")

    # Prepare fake mem0 modules for API mode
    class FakeMemoryClient:
        def __init__(self, api_key=None):
            self.api_key = api_key
    fake_mem0.MemoryClient = FakeMemoryClient

    api_cfg = type("C", (), {
        "MEMO_USE_LOCAL": False,
        "MEM0_API_KEY": "k"
    })()
    monkeypatch.setattr(cm, "get_config", lambda: api_cfg)

    cm_api = ChatMemory()
    assert cm_api.is_local is False
    assert hasattr(cm_api, "memory")


def test_chat_memory_cache_key_variation():
    from core.chat_memory import ChatMemory
    cm = ChatMemory(memory=MagicMock())
    k1 = cm._get_cache_key("c1", "q", 3)
    k2 = cm._get_cache_key("c1", "q ", 3)
    assert k1 != cm._get_cache_key("c1", "q", 4)
    assert isinstance(k1, str) and isinstance(k2, str)


