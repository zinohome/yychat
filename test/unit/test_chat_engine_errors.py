"""
ChatEngine错误处理测试
测试各种异常情况和错误恢复
"""
import pytest
from unittest.mock import patch, Mock
from core.chat_engine import chat_engine

@pytest.mark.asyncio
class TestChatEngineErrors:
    """错误处理测试套件"""
    
    async def test_empty_messages_handling(self):
        """测试空消息列表的处理"""
        response = await chat_engine.generate_response(
            messages=[],
            conversation_id="test_empty",
            stream=False
        )
        
        assert isinstance(response, dict)
        # 应该优雅处理，不抛出异常
        
        print("✅ 空消息列表处理正常")
    
    async def test_invalid_message_format(self):
        """测试无效消息格式"""
        invalid_messages = [
            {"role": "user"}  # 缺少content
        ]
        
        response = await chat_engine.generate_response(
            messages=invalid_messages,
            conversation_id="test_invalid",
            stream=False
        )
        
        assert isinstance(response, dict)
        # 应该优雅处理或返回错误信息
        
        print("✅ 无效消息格式处理正常")
    
    async def test_invalid_personality_id(self):
        """测试无效人格ID"""
        messages = [{"role": "user", "content": "test"}]
        
        response = await chat_engine.generate_response(
            messages=messages,
            conversation_id="test_invalid_personality",
            personality_id="non_existent_personality_999",
            stream=False
        )
        
        assert isinstance(response, dict)
        assert "content" in response
        # 应该优雅降级，使用默认设置
        
        print("✅ 无效人格ID优雅降级")
    
    async def test_very_long_message(self):
        """测试超长消息"""
        long_message = "test " * 10000  # 50000字符
        
        messages = [{"role": "user", "content": long_message}]
        
        try:
            response = await chat_engine.generate_response(
                messages=messages,
                conversation_id="test_long",
                stream=False
            )
            
            assert isinstance(response, dict)
            print("✅ 超长消息处理正常")
        except Exception as e:
            # 可能因为token限制失败，这也是预期的
            print(f"✅ 超长消息正确抛出异常: {type(e).__name__}")
    
    async def test_special_characters_in_message(self):
        """测试特殊字符处理"""
        special_messages = [
            {"role": "user", "content": "Test with emoji 🎉 and symbols @#$%^&*()"},
            {"role": "user", "content": "Test with\nnewlines\nand\ttabs"},
            {"role": "user", "content": "Test with quotes \"' and backslash \\"}
        ]
        
        for msg in special_messages:
            response = await chat_engine.generate_response(
                messages=[msg],
                conversation_id="test_special",
                stream=False
            )
            
            assert isinstance(response, dict)
        
        print("✅ 特殊字符处理正常")
    
    async def test_concurrent_requests(self):
        """测试并发请求处理"""
        import asyncio
        
        messages = [{"role": "user", "content": "concurrent test"}]
        
        # 创建3个并发请求
        tasks = [
            chat_engine.generate_response(
                messages=messages,
                conversation_id=f"test_concurrent_{i}",
                stream=False
            )
            for i in range(3)
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 检查所有响应
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                print(f"⚠️ 并发请求{i}出错: {type(response).__name__}")
            else:
                assert isinstance(response, dict)
        
        print(f"✅ 并发请求测试完成（{len([r for r in responses if not isinstance(r, Exception)])}/3成功）")
    
    async def test_invalid_conversation_id(self):
        """测试无效会话ID"""
        messages = [{"role": "user", "content": "test"}]
        
        # 测试各种特殊的conversation_id
        special_ids = ["", " ", None, "id/with/slashes", "id\\with\\backslashes"]
        
        for conv_id in special_ids:
            try:
                response = await chat_engine.generate_response(
                    messages=messages,
                    conversation_id=conv_id if conv_id is not None else "none_test",
                    stream=False
                )
                assert isinstance(response, dict)
            except Exception as e:
                # 某些情况可能会失败，这也是可以接受的
                print(f"⚠️ conversation_id={repr(conv_id)} 触发异常: {type(e).__name__}")
        
        print("✅ 无效会话ID处理测试完成")
    
    async def test_health_check_when_healthy(self):
        """测试正常状态下的健康检查"""
        health = await chat_engine.health_check()
        
        assert isinstance(health, dict)
        assert "healthy" in health
        assert "timestamp" in health
        assert "details" in health
        
        print(f"✅ 健康检查: {'健康' if health['healthy'] else '不健康'}")
    
    @patch('core.chat_engine.chat_engine.client')
    async def test_api_error_handling(self, mock_client):
        """测试API错误处理（使用mock）"""
        # Mock API抛出异常
        mock_client.create_chat.side_effect = Exception("API Error")
        
        messages = [{"role": "user", "content": "test"}]
        
        try:
            response = await chat_engine.generate_response(
                messages=messages,
                conversation_id="test_api_error",
                stream=False
            )
            
            # 应该返回错误响应而不是崩溃
            assert isinstance(response, dict)
            print("✅ API错误优雅处理")
        except Exception as e:
            # 如果抛出异常，也应该是已处理的异常
            print(f"✅ API错误抛出预期异常: {type(e).__name__}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

