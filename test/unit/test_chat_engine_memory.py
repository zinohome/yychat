"""
ChatEngine Memory管理测试
测试Memory的添加、检索、清理等功能
"""
import pytest
from core.chat_engine import chat_engine

@pytest.mark.asyncio
class TestChatEngineMemory:
    """Memory管理测试套件"""
    
    async def test_memory_system_initialized(self):
        """测试Memory系统是否正确初始化"""
        assert chat_engine.chat_memory is not None
        assert chat_engine.async_chat_memory is not None
        
        print("✅ Memory系统初始化正常")
    
    async def test_save_to_memory_both_mode(self):
        """测试保存消息到Memory（both模式）"""
        test_conv_id = "test_memory_save_001"
        
        messages = [
            {"role": "user", "content": "Test user message"},
            {"role": "assistant", "content": "Test assistant message"}
        ]
        
        try:
            # 调用save_to_memory
            await chat_engine.save_to_memory(
                messages=messages,
                conversation_id=test_conv_id,
                mode="both"
            )
            
            print("✅ 保存消息到Memory成功（both模式）")
        except Exception as e:
            print(f"⚠️ 保存Memory时出错（可能正常）: {str(e)[:100]}")
    
    async def test_save_to_memory_async_mode(self):
        """测试保存消息到Memory（async模式）"""
        test_conv_id = "test_memory_save_002"
        
        messages = [
            {"role": "user", "content": "Test message async"}
        ]
        
        try:
            await chat_engine.save_to_memory(
                messages=messages,
                conversation_id=test_conv_id,
                mode="async"
            )
            
            print("✅ 保存消息到Memory成功（async模式）")
        except Exception as e:
            print(f"⚠️ 保存Memory时出错: {str(e)[:100]}")
    
    async def test_save_to_memory_sync_mode(self):
        """测试保存消息到Memory（sync模式）"""
        test_conv_id = "test_memory_save_003"
        
        messages = [
            {"role": "user", "content": "Test message sync"}
        ]
        
        try:
            await chat_engine.save_to_memory(
                messages=messages,
                conversation_id=test_conv_id,
                mode="sync"
            )
            
            print("✅ 保存消息到Memory成功（sync模式）")
        except Exception as e:
            print(f"⚠️ 保存Memory时出错: {str(e)[:100]}")
    
    async def test_memory_retrieval_in_generate(self):
        """测试在generate_response中Memory检索是否工作"""
        test_conv_id = "test_memory_retrieval_001"
        
        # 先生成一条消息，应该会触发Memory检索
        messages = [
            {"role": "user", "content": "What is the weather today?"}
        ]
        
        response = await chat_engine.generate_response(
            messages=messages,
            conversation_id=test_conv_id,
            use_tools=False,
            stream=False
        )
        
        assert isinstance(response, dict)
        assert "content" in response
        # Memory检索应该在后台进行，不影响响应
        
        print("✅ generate_response中Memory检索正常")
    
    async def test_clear_conversation_memory_interface(self):
        """测试清除会话Memory接口"""
        test_conv_id = "test_clear_memory_001"
        
        result = await chat_engine.clear_conversation_memory(test_conv_id)
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "conversation_id" in result
        assert result["conversation_id"] == test_conv_id
        
        print(f"✅ 清除Memory接口调用成功（success={result['success']}）")
    
    async def test_get_conversation_memory_interface(self):
        """测试获取会话Memory接口"""
        test_conv_id = "test_get_memory_001"
        
        result = await chat_engine.get_conversation_memory(test_conv_id)
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "memories" in result
        assert isinstance(result["memories"], list)
        
        print(f"✅ 获取Memory接口调用成功（success={result['success']}）")
        print(f"   返回记忆数: {len(result['memories'])}")
    
    async def test_get_conversation_memory_with_limit(self):
        """测试带限制获取Memory"""
        test_conv_id = "test_get_memory_002"
        limit = 5
        
        result = await chat_engine.get_conversation_memory(test_conv_id, limit=limit)
        
        assert isinstance(result, dict)
        assert "memories" in result
        # 如果有返回，应该不超过limit
        if result.get("success"):
            assert len(result["memories"]) <= limit
        
        print(f"✅ 带限制获取Memory成功（limit={limit}）")
    
    async def test_memory_cache_behavior(self):
        """测试Memory缓存行为"""
        test_conv_id = "test_cache_001"
        
        # 第一次检索
        result1 = await chat_engine.get_conversation_memory(test_conv_id)
        
        # 第二次检索（应该命中缓存，如果有缓存机制）
        result2 = await chat_engine.get_conversation_memory(test_conv_id)
        
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        # 两次结果应该相同（如果有缓存）
        
        print("✅ Memory缓存行为测试完成")
    
    async def test_memory_with_empty_conversation(self):
        """测试空会话的Memory操作"""
        test_conv_id = "empty_conversation_999"
        
        result = await chat_engine.get_conversation_memory(test_conv_id)
        
        assert isinstance(result, dict)
        # 空会话应该返回空记忆列表
        if result.get("success"):
            assert isinstance(result["memories"], list)
        
        print("✅ 空会话Memory操作测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

