import pytest
from unittest.mock import patch, MagicMock
import os
from core.chat_memory import ChatMemory
from config.config import get_config

# 移除重复的mock_config fixture定义
@pytest.fixture
def mock_config():
    with patch('core.chat_memory.get_config') as mock_get_config:
        mock_config = MagicMock()
        mock_config.CHROMA_COLLECTION_NAME = 'test_collection'
        mock_config.CHROMA_PERSIST_DIRECTORY = '/tmp/test_chroma_db'
        mock_get_config.return_value = mock_config
        yield mock_config

# 移除不必要的 async 标记，因为这些测试不需要异步执行
@pytest.fixture
def chat_memory_instance(mock_config, mock_memory):
    # 创建ChatMemory实例，传递mock_memory
    return ChatMemory(memory=mock_memory)

def test_chat_memory_initialization(mock_config, mock_memory):
    # 测试ChatMemory的初始化
    chat_memory = ChatMemory(memory=mock_memory)
    # 验证初始化
    # 不再需要断言mock_memory被调用，因为我们直接传递了实例
    
    # 单独测试os.makedirs调用
    with patch('os.makedirs') as mock_makedirs:
        # 重新创建ChatMemory实例，使用真实配置
        # 不要直接调用get_config()，而是使用mock_config
        chat_memory = ChatMemory()
        # 验证初始化
        # 使用mock_config中的CHROMA_PERSIST_DIRECTORY值
        mock_makedirs.assert_called_once_with(mock_config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)

def test_add_memory(mock_memory, chat_memory_instance):
    # 测试添加记忆
    conversation_id = "test-conversation-123"
    user_message = "你好"
    assistant_message = "你好！我是AI助手"
    chat_memory_instance.add_memory(conversation_id, user_message, assistant_message)
    
    # 验证调用
    mock_memory.add.assert_called_once()
    args, kwargs = mock_memory.add.call_args
    assert kwargs['user_id'] == conversation_id
    # 修改这一行，检查content是否在args中
    assert args[0] == f"User: {user_message}\nAssistant: {assistant_message}"

# 移除async关键字，使测试成为同步函数
def test_add_message(mock_memory):
    # 测试添加消息到记忆
    # 创建ChatMemory实例，传递mock_memory
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 调用添加消息方法
    conversation_id = "test-conversation-123"
    message = {
        "role": "user",
        "content": "你好",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    chat_memory.add_message(conversation_id, message)
    
    # 验证调用
    # 修改验证逻辑，检查是否调用了正确的参数
    mock_memory.add.assert_called_once_with(
        "你好",
        user_id=conversation_id,
        metadata={
            "role": "user",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )

# 移除async关键字，使测试成为同步函数
def test_get_relevant_memory(mock_memory):
    # 测试获取相关记忆
    # 设置模拟返回值
    mock_memory.get_relevant.return_value = [
        {"content": "记忆1", "score": 0.9},
        {"content": "记忆2", "score": 0.8}
    ]
    
    # 创建ChatMemory实例，传递mock_memory
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 调用获取相关记忆方法
    conversation_id = "test-conversation-123"
    query = "相关问题"
    memories = chat_memory.get_relevant_memory(conversation_id, query, limit=5)
    
    # 后续代码保持不变
    # 验证结果
    assert memories == ["记忆1", "记忆2"]
    # 增加对方法调用的验证
    mock_memory.get_relevant.assert_called_once_with(
        query,
        user_id=conversation_id,
        limit=5
    )

@pytest.mark.asyncio
async def test_get_all_memory(mock_memory):
    # 测试获取所有记忆
    # 设置模拟返回值
    mock_memory.get_all.return_value = [
        {"content": "记忆1"},
        {"content": "记忆2"}
    ]
    
    # 创建ChatMemory实例，传递mock_memory
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 调用获取所有记忆方法
    conversation_id = "test-conversation-123"
    memories = chat_memory.get_all_memory(conversation_id)
    
    # 验证结果
    assert memories == ["记忆1", "记忆2"]
    # 增加对方法调用的验证
    mock_memory.get_all.assert_called_once_with(user_id=conversation_id)

@pytest.mark.asyncio
async def test_get_all_memory_exception(mock_memory):
    # 测试获取所有记忆抛出异常
    # 设置模拟抛出异常
    mock_memory.get_all.side_effect = Exception("Get all error")
    
    # 创建ChatMemory实例，传递mock_memory
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 调用获取所有记忆方法
    conversation_id = "test-conversation-123"
    memories = chat_memory.get_all_memory(conversation_id)
    
    # 验证结果（异常情况下应返回空列表）
    assert memories == []

@pytest.mark.asyncio
async def test_delete_memory(mock_memory):
    # 测试删除记忆
    # 创建ChatMemory实例，传递mock_memory
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 调用删除记忆方法
    conversation_id = "test-conversation-123"
    chat_memory.delete_memory(conversation_id)
    
    # 验证调用
    mock_memory.delete_all.assert_called_once_with(user_id=conversation_id)

@pytest.mark.asyncio
async def test_delete_memory_exception(mock_memory):
    # 测试删除记忆抛出异常
    # 设置模拟抛出异常
    mock_memory.delete_all.side_effect = Exception("Delete error")
    
    # 创建ChatMemory实例，传递mock_memory
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 调用删除记忆方法
    conversation_id = "test-conversation-123"
    # 不应该抛出异常
    chat_memory.delete_memory(conversation_id)