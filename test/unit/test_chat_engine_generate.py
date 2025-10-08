"""
ChatEngine消息生成测试
测试核心的消息生成功能
"""
import pytest
from core.chat_engine import chat_engine

@pytest.mark.asyncio
class TestChatEngineGenerate:
    """消息生成测试套件"""
    
    async def test_generate_simple_message(self, test_messages, test_conversation_id):
        """测试生成简单消息
        
        最基本的测试：发送一条消息，获取响应
        """
        response = await chat_engine.generate_response(
            messages=test_messages,
            conversation_id=test_conversation_id,
            use_tools=False,
            stream=False
        )
        
        # 验证响应格式
        assert isinstance(response, dict), "应该返回字典"
        assert "content" in response, "应该有content字段"
        assert "role" in response, "应该有role字段"
        assert response["role"] == "assistant", "角色应该是assistant"
        assert len(response["content"]) > 0, "内容不应为空"
        
        print(f"✅ 简单消息生成成功")
        print(f"   响应长度: {len(response['content'])} 字符")
    
    async def test_generate_with_system_message(self, test_conversation_id):
        """测试带系统消息的生成"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hi"}
        ]
        
        response = await chat_engine.generate_response(
            messages=messages,
            conversation_id=test_conversation_id,
            use_tools=False,
            stream=False
        )
        
        assert "content" in response
        print("✅ 带系统消息生成成功")
    
    async def test_generate_multi_turn(self, test_multi_turn_messages, test_conversation_id):
        """测试多轮对话"""
        response = await chat_engine.generate_response(
            messages=test_multi_turn_messages,
            conversation_id=test_conversation_id,
            use_tools=False,
            stream=False
        )
        
        assert "content" in response
        print("✅ 多轮对话生成成功")
    
    async def test_generate_with_personality(self, test_messages):
        """测试使用人格生成"""
        response = await chat_engine.generate_response(
            messages=test_messages,
            conversation_id="test_personality",
            personality_id="friendly",
            use_tools=False,
            stream=False
        )
        
        assert "content" in response
        assert len(response["content"]) > 0
        print("✅ 使用friendly人格生成成功")
    
    async def test_generate_streaming(self, test_messages, test_conversation_id):
        """测试流式生成
        
        验证:
        - 返回异步生成器
        - 可以迭代获取块
        - 最后一个块有finish_reason
        """
        generator = await chat_engine.generate_response(
            messages=test_messages,
            conversation_id=test_conversation_id,
            use_tools=False,
            stream=True
        )
        
        chunks = []
        async for chunk in generator:
            chunks.append(chunk)
            assert isinstance(chunk, dict), "每个块应该是字典"
            assert "role" in chunk, "应该有role字段"
        
        assert len(chunks) > 0, "应该至少有一个块"
        assert chunks[-1]["finish_reason"] == "stop", "最后一个块应该标记结束"
        
        # 重建完整内容
        full_content = "".join(
            chunk.get("content", "") for chunk in chunks 
            if chunk.get("content")
        )
        assert len(full_content) > 0, "完整内容不应为空"
        
        print(f"✅ 流式生成成功")
        print(f"   块数: {len(chunks)}")
        print(f"   总长度: {len(full_content)} 字符")
    
    async def test_generate_empty_messages(self):
        """测试空消息列表
        
        验证错误处理：应该优雅地处理空消息
        """
        response = await chat_engine.generate_response(
            messages=[],
            conversation_id="test_empty",
            stream=False
        )
        
        # 应该返回错误消息而不是崩溃
        assert isinstance(response, dict)
        print("✅ 空消息列表处理正确")
    
    async def test_generate_with_invalid_personality(self, test_messages):
        """测试无效人格ID
        
        验证:
        - 不应该崩溃
        - 应该优雅降级
        - 仍能生成响应
        """
        response = await chat_engine.generate_response(
            messages=test_messages,
            conversation_id="test_invalid_personality",
            personality_id="non_existent_personality_12345",
            stream=False
        )
        
        # 应该仍能生成响应（使用默认设置）
        assert "content" in response
        print("✅ 无效人格ID处理正确（优雅降级）")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

