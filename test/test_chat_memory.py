import pytest
import os
import core  # 添加导入
import json
from unittest.mock import patch, MagicMock
from core.chat_memory import ChatMemory, AsyncChatMemory, get_memory_config, get_async_chat_memory
from mem0.configs.base import MemoryConfig
from config.config import get_config  # 添加导入

# 测试ChatMemory初始化
def test_chat_memory_init(mock_config, mock_memory):
    # 测试使用提供的memory对象初始化
    chat_memory = ChatMemory(memory=mock_memory)
    assert chat_memory.memory == mock_memory

    # 测试不提供memory对象的初始化
    with patch('core.chat_memory.Memory') as mock_memory_class:
        mock_memory_instance = MagicMock()
        mock_memory_class.return_value = mock_memory_instance

        # 配置mock_config以包含llm相关配置
        mock_config.MEM0_LLM_PROVIDER = "openai"
        mock_config.MEM0_LLM_CONFIG_MODEL = "gpt-4.1"
        mock_config.MEM0_LLM_CONFIG_MAX_TOKENS = 32768
        mock_config.CHROMA_COLLECTION_NAME = "test_collection"
        mock_config.CHROMA_PERSIST_DIRECTORY = "/tmp/test_chroma"

        # 使用makedirs的patch，避免实际创建目录
        with patch('os.makedirs') as mock_makedirs:
            # 添加对get_config的patch，使其返回mock_config
            with patch('core.chat_memory.get_config') as mock_get_config:
                mock_get_config.return_value = mock_config
                
                chat_memory = ChatMemory()

                # 验证MemoryConfig是否正确创建并使用
                args, kwargs = mock_memory_class.call_args
                assert isinstance(kwargs['config'], MemoryConfig)
                # 使用点表示法访问LlmConfig对象的属性
                assert kwargs['config'].llm.provider == "openai"
                # llm.config是字典，使用字典下标访问
                assert kwargs['config'].llm.config['model'] == "gpt-4.1"
                assert kwargs['config'].llm.config['max_tokens'] == 32768
                assert kwargs['config'].vector_store.provider == "chroma"
                # vector_store.config是对象，使用点表示法访问
                assert kwargs['config'].vector_store.config.collection_name == "test_collection"
                assert kwargs['config'].vector_store.config.path == "/tmp/test_chroma"

                # 验证makedirs是否被正确调用
                mock_makedirs.assert_called_once_with("/tmp/test_chroma", exist_ok=True)

# 测试get_memory_config函数
def test_get_memory_config(mock_config):
    # 配置mock_config
    mock_config.MEM0_LLM_PROVIDER = "openai"
    mock_config.MEM0_LLM_CONFIG_MODEL = "gpt-4.1"
    mock_config.MEM0_LLM_CONFIG_MAX_TOKENS = 32768
    mock_config.CHROMA_COLLECTION_NAME = "test_collection"
    mock_config.CHROMA_PERSIST_DIRECTORY = "/tmp/test_chroma"
    
    # 获取配置 - 传递mock_config参数
    config = get_memory_config(mock_config)
    
    # 验证配置
    assert isinstance(config, MemoryConfig)
    # 根据实际对象结构使用正确的访问方式
    assert config.llm.provider == "openai"
    # config.llm.config 是字典，使用字典下标访问
    assert config.llm.config['model'] == "gpt-4.1"
    assert config.llm.config['max_tokens'] == 32768
    assert config.vector_store.provider == "chroma"
    # config.vector_store.config 是 ChromaDbConfig 对象，使用点表示法访问
    assert config.vector_store.config.collection_name == "test_collection"
    assert config.vector_store.config.path == "/tmp/test_chroma"

# 测试add_message方法
def test_add_message(mock_config, mock_memory):
    chat_memory = ChatMemory(memory=mock_memory)
    message = {"role": "user", "content": "你好", "timestamp": "2023-01-01T12:00:00"}
    
    chat_memory.add_message("conversation_1", message)
    
    # 验证memory.add被正确调用
    mock_memory.add.assert_called_once_with(
        "你好",
        user_id="conversation_1",
        metadata={"role": "user", "timestamp": "2023-01-01T12:00:00"}
    )

# 测试add_message方法(不含timestamp)
def test_add_message_without_timestamp(mock_config, mock_memory):
    chat_memory = ChatMemory(memory=mock_memory)
    message = {"role": "user", "content": "你好"}
    
    chat_memory.add_message("conversation_1", message)
    
    # 验证memory.add被正确调用
    mock_memory.add.assert_called_once_with(
        "你好",
        user_id="conversation_1",
        metadata={"role": "user"}
    )

# 测试add_message方法 - 异常处理
def test_add_message_exception(mock_config, mock_memory):
    chat_memory = ChatMemory(memory=mock_memory)
    message = {"role": "user", "content": "你好"}
    
    # 设置模拟抛出异常
    mock_memory.add.side_effect = Exception("测试异常")
    
    # 调用方法，不应该抛出异常
    chat_memory.add_message("conversation_1", message)

# 测试get_relevant_memory方法 - 使用get_relevant
def test_get_relevant_memory_get_relevant(mock_config, mock_memory):
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 设置模拟返回值
    mock_memory.get_relevant.return_value = [
        {"content": "记忆1"}, {"content": "记忆2"}
    ]
    
    # 调用方法
    result = chat_memory.get_relevant_memory("conversation_1", "查询", limit=5)
    
    # 验证结果
    assert result == ["记忆1", "记忆2"]
    mock_memory.get_relevant.assert_called_once_with("查询", limit=5, user_id="conversation_1")

# 测试get_relevant_memory方法 - 使用search
def test_get_relevant_memory_search(mock_config):
    # 创建一个没有get_relevant但有search的mock memory
    mock_memory = MagicMock()
    delattr(mock_memory, 'get_relevant')
    mock_memory.search.return_value = [
        {"content": "记忆1"}, {"content": "记忆2"}
    ]
    
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 调用方法
    result = chat_memory.get_relevant_memory("conversation_1", "查询", limit=5)
    
    # 验证结果
    assert result == ["记忆1", "记忆2"]
    mock_memory.search.assert_called_once_with("查询", limit=5, user_id="conversation_1")

# 测试get_relevant_memory方法 - 使用get和结果截取
def test_get_relevant_memory_get(mock_config):
    # 创建一个没有get_relevant和search但有get的mock memory
    mock_memory = MagicMock()
    delattr(mock_memory, 'get_relevant')
    delattr(mock_memory, 'search')
    mock_memory.get.return_value = [
        {"content": "记忆1"}, {"content": "记忆2"}, {"content": "记忆3"}, {"content": "记忆4"}, {"content": "记忆5"}, {"content": "记忆6"}
    ]
    
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 调用方法，limit=5但返回6个结果
    result = chat_memory.get_relevant_memory("conversation_1", "查询", limit=5)
    
    # 验证结果被截取到5个
    assert result == ["记忆1", "记忆2", "记忆3", "记忆4", "记忆5"]
    mock_memory.get.assert_called_once_with("查询", user_id="conversation_1")

# 测试get_relevant_memory方法 - 处理字典格式结果
def test_get_relevant_memory_dict_result(mock_config, mock_memory):
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 设置模拟返回值为字典格式
    mock_memory.get_relevant.return_value = {
        "results": [{"content": "记忆1"}, {"content": "记忆2"}]
    }
    
    # 调用方法
    result = chat_memory.get_relevant_memory("conversation_1", "查询", limit=5)
    
    # 验证结果
    assert result == ["记忆1", "记忆2"]

# 测试get_relevant_memory方法 - 异常处理
def test_get_relevant_memory_exception(mock_config, mock_memory):
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 设置模拟抛出异常
    mock_memory.get_relevant.side_effect = Exception("测试异常")
    
    # 调用方法
    result = chat_memory.get_relevant_memory("conversation_1", "查询", limit=5)
    
    # 验证异常被捕获并返回空列表
    assert result == []

# 测试get_all_memory方法 - 列表格式结果
def test_get_all_memory_list_result(mock_config, mock_memory):
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 设置模拟返回值
    mock_memory.get_all.return_value = [
        {"content": "记忆1"}, "记忆2", 123
    ]
    
    # 调用方法
    result = chat_memory.get_all_memory("conversation_1")
    
    # 验证结果
    assert result == ["记忆1", "记忆2", "123"]
    mock_memory.get_all.assert_called_once_with(user_id="conversation_1")

# 测试get_all_memory方法 - 非列表格式结果
def test_get_all_memory_non_list_result(mock_config, mock_memory):
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 设置模拟返回值为非列表
    mock_memory.get_all.return_value = "单一记忆"
    
    # 调用方法
    result = chat_memory.get_all_memory("conversation_1")
    
    # 验证结果
    assert result == ["单一记忆"]

# 测试get_all_memory方法 - None结果
def test_get_all_memory_none_result(mock_config, mock_memory):
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 设置模拟返回值为None
    mock_memory.get_all.return_value = None
    
    # 调用方法
    result = chat_memory.get_all_memory("conversation_1")
    
    # 验证结果
    assert result == []

# 测试get_all_memory方法 - 异常处理
def test_get_all_memory_exception(mock_config, mock_memory):
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 设置模拟抛出异常
    mock_memory.get_all.side_effect = Exception("测试异常")
    
    # 调用方法
    result = chat_memory.get_all_memory("conversation_1")
    
    # 验证异常被捕获并返回空列表
    assert result == []

# 测试delete_memory方法
def test_delete_memory(mock_config, mock_memory):
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 调用方法
    chat_memory.delete_memory("conversation_1")
    
    # 验证memory.delete_all被正确调用
    mock_memory.delete_all.assert_called_once_with(user_id="conversation_1")

# 测试add_memory方法
def test_add_memory(mock_config, mock_memory):
    chat_memory = ChatMemory(memory=mock_memory)
    
    # 调用方法
    chat_memory.add_memory("conversation_1", "用户消息", "助手消息")
    
    # 验证memory.add被正确调用
    mock_memory.add.assert_called_once_with(
        "User: 用户消息\nAssistant: 助手消息",
        user_id="conversation_1",
        metadata={"type": "conversation"}
    )

# 测试AsyncChatMemory初始化
@pytest.mark.asyncio
async def test_async_chat_memory_init(mock_config, mock_async_memory):
    # 测试使用提供的async_memory对象初始化
    async_chat_memory = AsyncChatMemory(async_memory=mock_async_memory)
    assert async_chat_memory.async_memory == mock_async_memory
    
    # 测试不提供async_memory对象的初始化
    with patch('core.chat_memory.AsyncMemory') as mock_async_memory_class:
        mock_async_memory_instance = MagicMock()
        mock_async_memory_class.return_value = mock_async_memory_instance
        
        # 配置mock_config
        mock_config.MEM0_LLM_PROVIDER = "openai"
        mock_config.MEM0_LLM_CONFIG_MODEL = "gpt-4.1"
        mock_config.MEM0_LLM_CONFIG_MAX_TOKENS = 32768
        mock_config.CHROMA_COLLECTION_NAME = "test_collection"
        mock_config.CHROMA_PERSIST_DIRECTORY = "/tmp/test_chroma"
        
        # 使用makedirs的patch
        with patch('os.makedirs') as mock_makedirs:
            async_chat_memory = AsyncChatMemory(config=mock_config)
            
            # 验证AsyncMemory是否正确创建
            mock_async_memory_class.assert_called_once()
            
            # 验证makedirs被调用
            mock_makedirs.assert_called_once_with("/tmp/test_chroma", exist_ok=True)

# 测试AsyncChatMemory.add_message方法
@pytest.mark.asyncio
async def test_async_chat_memory_add_message(mock_config, mock_async_memory):
    async_chat_memory = AsyncChatMemory(async_memory=mock_async_memory)
    message = {"role": "user", "content": "你好", "timestamp": "2023-01-01T12:00:00"}
    
    await async_chat_memory.add_message("conversation_1", message)
    
    # 验证async_memory.add被正确调用
    mock_async_memory.add.assert_called_once_with(
        "你好",
        user_id="conversation_1",
        metadata={"role": "user", "timestamp": "2023-01-01T12:00:00"}
    )

# 测试AsyncChatMemory.add_message方法 - 异常处理
@pytest.mark.asyncio
async def test_async_chat_memory_add_message_exception(mock_config, mock_async_memory):
    async_chat_memory = AsyncChatMemory(async_memory=mock_async_memory)
    message = {"role": "user", "content": "你好"}
    
    # 设置模拟抛出异常
    mock_async_memory.add.side_effect = Exception("测试异常")
    
    # 调用方法，不应该抛出异常
    await async_chat_memory.add_message("conversation_1", message)

# 测试AsyncChatMemory.add_messages_batch方法
@pytest.mark.asyncio
async def test_async_chat_memory_add_messages_batch(mock_config, mock_async_memory):
    async_chat_memory = AsyncChatMemory(async_memory=mock_async_memory)
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮助你的？"}
    ]
    
    await async_chat_memory.add_messages_batch("conversation_1", messages)
    
    # 验证async_memory.add被调用了两次
    assert mock_async_memory.add.call_count == 2
    mock_async_memory.add.assert_any_call(
        "你好",
        user_id="conversation_1",
        metadata={"role": "user"}
    )
    mock_async_memory.add.assert_any_call(
        "你好，有什么可以帮助你的？",
        user_id="conversation_1",
        metadata={"role": "assistant"}
    )

# 测试AsyncChatMemory.add_messages_batch方法 - 异常处理
@pytest.mark.asyncio
async def test_async_chat_memory_add_messages_batch_exception(mock_config, mock_async_memory):
    async_chat_memory = AsyncChatMemory(async_memory=mock_async_memory)
    messages = [
        {"role": "user", "content": "你好"}
    ]
    
    # 设置模拟抛出异常
    mock_async_memory.add.side_effect = Exception("测试异常")
    
    # 调用方法，不应该抛出异常
    await async_chat_memory.add_messages_batch("conversation_1", messages)

# 测试AsyncChatMemory.get_relevant_memory方法
@pytest.mark.asyncio
async def test_async_chat_memory_get_relevant_memory(mock_config, mock_async_memory):
    async_chat_memory = AsyncChatMemory(async_memory=mock_async_memory)
    
    # 设置模拟返回值
    mock_async_memory.search.return_value = {
        "results": [{"memory": "记忆1"}, {"memory": "记忆2"}]
    }
    
    # 调用方法
    result = await async_chat_memory.get_relevant_memory("conversation_1", "查询", limit=5)
    
    # 验证结果
    assert result == ["记忆1", "记忆2"]
    mock_async_memory.search.assert_called_once_with("查询", limit=5, user_id="conversation_1")

# 测试AsyncChatMemory.get_relevant_memory方法 - 异常处理
@pytest.mark.asyncio
async def test_async_chat_memory_get_relevant_memory_exception(mock_config, mock_async_memory):
    async_chat_memory = AsyncChatMemory(async_memory=mock_async_memory)
    
    # 设置模拟抛出异常
    mock_async_memory.search.side_effect = Exception("测试异常")
    
    # 调用方法
    result = await async_chat_memory.get_relevant_memory("conversation_1", "查询", limit=5)
    
    # 验证异常被捕获并返回空列表
    assert result == []

# 测试AsyncChatMemory.get_all_memory方法
@pytest.mark.asyncio
async def test_async_chat_memory_get_all_memory(mock_config, mock_async_memory):
    async_chat_memory = AsyncChatMemory(async_memory=mock_async_memory)
    
    # 设置模拟返回值
    mock_async_memory.get_all.return_value = [
        {"content": "记忆1"}, "记忆2", 123
    ]
    
    # 调用方法
    result = await async_chat_memory.get_all_memory("conversation_1")
    
    # 验证结果
    assert result == ["记忆1", "记忆2", "123"]
    mock_async_memory.get_all.assert_called_once_with(user_id="conversation_1")

# 测试AsyncChatMemory.get_all_memory方法 - 异常处理
@pytest.mark.asyncio
async def test_async_chat_memory_get_all_memory_exception(mock_config, mock_async_memory):
    async_chat_memory = AsyncChatMemory(async_memory=mock_async_memory)
    
    # 设置模拟抛出异常
    mock_async_memory.get_all.side_effect = Exception("测试异常")
    
    # 调用方法
    result = await async_chat_memory.get_all_memory("conversation_1")
    
    # 验证异常被捕获并返回空列表
    assert result == []

# 测试AsyncChatMemory.delete_memory方法
@pytest.mark.asyncio
async def test_async_chat_memory_delete_memory(mock_config, mock_async_memory):
    async_chat_memory = AsyncChatMemory(async_memory=mock_async_memory)
    
    # 调用方法
    await async_chat_memory.delete_memory("conversation_1")
    
    # 验证async_memory.delete_all被正确调用
    mock_async_memory.delete_all.assert_called_once_with(user_id="conversation_1")

# 测试get_async_chat_memory函数
def test_get_async_chat_memory():
    # 清除全局实例（如果存在）
    if hasattr(core.chat_memory, '_async_chat_memory'):
        delattr(core.chat_memory, '_async_chat_memory')
    
    # 使用patch模拟AsyncChatMemory类
    with patch('core.chat_memory.AsyncChatMemory') as mock_async_chat_memory_class:
        mock_instance = MagicMock()
        mock_async_chat_memory_class.return_value = mock_instance
        
        # 第一次调用应该创建新实例
        result1 = get_async_chat_memory()
        mock_async_chat_memory_class.assert_called_once()
        assert result1 == mock_instance
        
        # 重置mock
        mock_async_chat_memory_class.reset_mock()
        
        # 第二次调用应该返回相同实例，不再创建新实例
        result2 = get_async_chat_memory()
        mock_async_chat_memory_class.assert_not_called()
        assert result2 == mock_instance
        assert result1 is result2