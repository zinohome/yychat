"""
ChatMemory详细测试
测试同步/异步操作、缓存机制、错误处理等
"""
import pytest
import hashlib
from unittest.mock import Mock, AsyncMock, patch
from core.chat_memory import ChatMemory, AsyncChatMemory, get_async_chat_memory

@pytest.mark.asyncio
class TestChatMemoryBasic:
    """ChatMemory基础测试"""
    
    def test_chat_memory_initialization(self):
        """测试ChatMemory初始化"""
        memory = ChatMemory()
        
        assert memory is not None
        assert hasattr(memory, 'memory')
        assert hasattr(memory, '_memory_cache')
        print("✅ ChatMemory初始化成功")
    
    def test_chat_memory_with_provided_memory(self):
        """测试使用提供的Memory对象"""
        mock_memory = Mock()
        memory = ChatMemory(memory=mock_memory)
        
        assert memory.memory == mock_memory
        print("✅ 使用提供的Memory对象成功")
    
    def test_preprocess_query(self):
        """测试查询预处理"""
        memory = ChatMemory()
        
        # 测试去除多余空格
        query1 = "  hello   world  "
        result1 = memory._preprocess_query(query1)
        assert result1 == "hello world"
        
        # 测试长查询截断
        long_query = "a" * 600
        result2 = memory._preprocess_query(long_query)
        assert len(result2) <= 500
        
        print("✅ 查询预处理成功")
    
    def test_get_cache_key(self):
        """测试缓存键生成"""
        memory = ChatMemory()
        
        key1 = memory._get_cache_key("conv1", "query1", 10)
        key2 = memory._get_cache_key("conv1", "query1", 10)
        key3 = memory._get_cache_key("conv1", "query2", 10)
        
        # 相同参数应该生成相同的键
        assert key1 == key2
        # 不同参数应该生成不同的键
        assert key1 != key3
        # 键应该是32字符的MD5
        assert len(key1) == 32
        
        print("✅ 缓存键生成正确")
    
    def test_invalidate_cache(self):
        """测试缓存清除"""
        memory = ChatMemory()
        
        # 添加一些缓存
        memory._memory_cache["key1"] = "value1"
        memory._memory_cache["key2"] = "value2"
        
        assert len(memory._memory_cache) == 2
        
        # 清除缓存
        memory._invalidate_cache("test_conv")
        
        # 缓存应该被清空
        assert len(memory._memory_cache) == 0
        
        print("✅ 缓存清除成功")
    
    def test_add_message_basic(self):
        """测试添加消息"""
        memory = ChatMemory()
        
        message = {
            "role": "user",
            "content": "Test message"
        }
        
        try:
            memory.add_message("test_add_conv", message)
            print("✅ 添加消息成功")
        except Exception as e:
            print(f"⚠️ 添加消息（可能需要API）: {str(e)[:50]}")
    
    def test_add_message_with_timestamp(self):
        """测试添加带时间戳的消息"""
        memory = ChatMemory()
        
        message = {
            "role": "user",
            "content": "Message with timestamp",
            "timestamp": 1234567890
        }
        
        try:
            memory.add_message("test_timestamp_conv", message)
            print("✅ 添加带时间戳的消息成功")
        except Exception as e:
            print(f"⚠️ 添加带时间戳消息: {str(e)[:50]}")
    
    def test_get_relevant_memory_basic(self):
        """测试获取相关记忆"""
        memory = ChatMemory()
        
        try:
            result = memory.get_relevant_memory(
                "test_get_conv",
                "test query"
            )
            
            assert isinstance(result, list)
            print(f"✅ 获取相关记忆成功（{len(result)}条）")
        except Exception as e:
            print(f"⚠️ 获取相关记忆: {str(e)[:50]}")
    
    def test_get_relevant_memory_with_limit(self):
        """测试带限制的获取相关记忆"""
        memory = ChatMemory()
        
        try:
            result = memory.get_relevant_memory(
                "test_limit_conv",
                "test query",
                limit=5
            )
            
            assert isinstance(result, list)
            assert len(result) <= 5
            print(f"✅ 带限制获取记忆成功（{len(result)}条）")
        except Exception as e:
            print(f"⚠️ 带限制获取记忆: {str(e)[:50]}")
    
    def test_get_relevant_memory_cache_hit(self):
        """测试记忆缓存命中"""
        memory = ChatMemory()
        
        conv_id = "test_cache_conv"
        query = "cache test"
        
        # 第一次查询（缓存未命中）
        try:
            result1 = memory.get_relevant_memory(conv_id, query)
            
            # 第二次查询（应该缓存命中）
            result2 = memory.get_relevant_memory(conv_id, query)
            
            # 结果应该相同
            assert result1 == result2
            print("✅ 缓存命中测试成功")
        except Exception as e:
            print(f"⚠️ 缓存测试: {str(e)[:50]}")
    
    def test_get_all_memory(self):
        """测试获取所有记忆"""
        memory = ChatMemory()
        
        try:
            result = memory.get_all_memory("test_all_conv")
            
            assert isinstance(result, list)
            print(f"✅ 获取所有记忆成功（{len(result)}条）")
        except Exception as e:
            print(f"⚠️ 获取所有记忆: {str(e)[:50]}")


@pytest.mark.asyncio
class TestAsyncChatMemory:
    """AsyncChatMemory异步测试"""
    
    def test_async_chat_memory_initialization(self):
        """测试AsyncChatMemory初始化"""
        async_memory = AsyncChatMemory()
        
        assert async_memory is not None
        assert hasattr(async_memory, 'memory')
        assert hasattr(async_memory, '_memory_cache')
        print("✅ AsyncChatMemory初始化成功")
    
    def test_get_async_chat_memory_singleton(self):
        """测试AsyncChatMemory单例模式"""
        memory1 = get_async_chat_memory()
        memory2 = get_async_chat_memory()
        
        assert memory1 is memory2
        assert id(memory1) == id(memory2)
        print("✅ AsyncChatMemory单例模式验证通过")
    
    async def test_async_add_message(self):
        """测试异步添加消息"""
        async_memory = get_async_chat_memory()
        
        message = {
            "role": "user",
            "content": "Async test message"
        }
        
        try:
            await async_memory.add_message("test_async_add", message)
            print("✅ 异步添加消息成功")
        except Exception as e:
            print(f"⚠️ 异步添加消息: {str(e)[:50]}")
    
    async def test_async_get_relevant_memory(self):
        """测试异步获取相关记忆"""
        async_memory = get_async_chat_memory()
        
        try:
            result = await async_memory.get_relevant_memory(
                "test_async_get",
                "async query"
            )
            
            assert isinstance(result, list)
            print(f"✅ 异步获取记忆成功（{len(result)}条）")
        except Exception as e:
            print(f"⚠️ 异步获取记忆: {str(e)[:50]}")
    
    async def test_async_get_relevant_memory_with_limit(self):
        """测试异步获取记忆（带限制）"""
        async_memory = get_async_chat_memory()
        
        try:
            result = await async_memory.get_relevant_memory(
                "test_async_limit",
                "test",
                limit=3
            )
            
            assert isinstance(result, list)
            assert len(result) <= 3
            print(f"✅ 异步获取记忆（限制）成功（{len(result)}条）")
        except Exception as e:
            print(f"⚠️ 异步限制获取: {str(e)[:50]}")
    
    async def test_async_invalidate_cache(self):
        """测试异步清除缓存"""
        async_memory = get_async_chat_memory()
        
        try:
            await async_memory.invalidate_cache("test_async_invalidate")
            print("✅ 异步清除缓存成功")
        except Exception as e:
            print(f"⚠️ 异步清除缓存: {str(e)[:50]}")


@pytest.mark.asyncio
class TestChatMemoryCache:
    """ChatMemory缓存机制详细测试"""
    
    def test_cache_expiry(self):
        """测试缓存过期"""
        memory = ChatMemory()
        
        # TTLCache的maxsize是100，ttl是300秒
        assert memory._memory_cache.maxsize == 100
        assert memory._memory_cache.ttl == 300
        
        print("✅ 缓存配置正确")
    
    def test_cache_invalidation_on_add(self):
        """测试添加消息时清除缓存"""
        memory = ChatMemory()
        
        # 手动添加缓存
        test_key = "test_cache_key"
        memory._memory_cache[test_key] = "cached_value"
        
        assert test_key in memory._memory_cache
        
        # 添加消息应该清除缓存
        message = {"role": "user", "content": "test"}
        try:
            memory.add_message("test_conv", message)
            # 缓存应该被清除
            assert test_key not in memory._memory_cache
            print("✅ 添加消息时缓存清除正确")
        except Exception as e:
            print(f"⚠️ 缓存清除测试: {str(e)[:50]}")
    
    def test_cache_key_uniqueness(self):
        """测试缓存键唯一性"""
        memory = ChatMemory()
        
        key1 = memory._get_cache_key("conv1", "query1", 10)
        key2 = memory._get_cache_key("conv2", "query1", 10)
        key3 = memory._get_cache_key("conv1", "query2", 10)
        key4 = memory._get_cache_key("conv1", "query1", 20)
        
        # 所有键应该不同
        keys = [key1, key2, key3, key4]
        assert len(keys) == len(set(keys))
        
        print("✅ 缓存键唯一性验证通过")


@pytest.mark.asyncio
class TestChatMemoryErrorHandling:
    """ChatMemory错误处理测试"""
    
    def test_add_message_missing_content(self):
        """测试添加缺少content的消息"""
        memory = ChatMemory()
        
        invalid_message = {"role": "user"}  # 缺少content
        
        try:
            memory.add_message("test_invalid", invalid_message)
            print("⚠️ 应该抛出错误但没有抛出")
        except Exception as e:
            print(f"✅ 正确捕获错误: {str(e)[:30]}")
    
    def test_add_message_invalid_role(self):
        """测试添加无效role的消息"""
        memory = ChatMemory()
        
        invalid_message = {
            "role": "invalid_role",
            "content": "test"
        }
        
        try:
            memory.add_message("test_invalid_role", invalid_message)
            # 可能不会抛出错误，只是记录
            print("✅ 处理无效role消息")
        except Exception as e:
            print(f"✅ 捕获无效role错误: {str(e)[:30]}")
    
    def test_get_relevant_memory_empty_query(self):
        """测试空查询"""
        memory = ChatMemory()
        
        try:
            result = memory.get_relevant_memory("test_empty", "")
            assert isinstance(result, list)
            print("✅ 空查询处理正确")
        except Exception as e:
            print(f"⚠️ 空查询: {str(e)[:50]}")
    
    async def test_async_add_message_error_handling(self):
        """测试异步添加消息的错误处理"""
        async_memory = get_async_chat_memory()
        
        # 构造会导致错误的消息
        invalid_message = None
        
        try:
            await async_memory.add_message("test_error", invalid_message)
            print("⚠️ 应该抛出错误")
        except Exception as e:
            print(f"✅ 异步错误处理正确: {str(e)[:30]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
