import pytest
from unittest.mock import MagicMock


def test_chat_memory_get_all_memory_mixed_types():
    from core.chat_memory import ChatMemory
    mem = MagicMock()
    mem.get_all = MagicMock(return_value=[{"content":"a"}, "b", 123])
    cm = ChatMemory(memory=mem)
    out = cm.get_all_memory('cid')
    assert out == ["a", "b", "123"]


def test_chat_memory_add_memory_and_delete_error_paths():
    from core.chat_memory import ChatMemory
    mem = MagicMock()
    mem.add.side_effect = Exception('add')
    mem.delete_all.side_effect = Exception('del')
    cm = ChatMemory(memory=mem)
    # should not raise
    cm.add_memory('cid', 'u', 'a')
    cm.delete_memory('cid')


