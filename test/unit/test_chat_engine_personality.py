"""
ChatEngine Personality应用测试
测试人格系统的加载和应用
"""
import pytest
from core.chat_engine import chat_engine

@pytest.mark.asyncio
class TestChatEnginePersonality:
    """Personality应用测试套件"""
    
    def test_personality_manager_exists(self):
        """测试PersonalityManager是否存在"""
        assert chat_engine.personality_manager is not None
        print("✅ PersonalityManager存在")
    
    def test_list_personalities(self):
        """测试列出所有人格"""
        personalities = chat_engine.personality_manager.list_personalities()
        
        assert isinstance(personalities, list)
        assert len(personalities) > 0
        
        print(f"✅ 成功列出人格，共 {len(personalities)} 个")
        for p in personalities:
            print(f"   - {p.get('id', 'unknown')}: {p.get('name', 'unnamed')}")
    
    def test_get_personality_by_id(self):
        """测试根据ID获取人格"""
        # 先获取所有人格
        personalities = chat_engine.personality_manager.list_personalities()
        
        if len(personalities) > 0:
            first_id = personalities[0].get('id')
            
            # 获取人格
            personality = chat_engine.personality_manager.get_personality(first_id)
            
            assert personality is not None
            assert hasattr(personality, 'system_prompt') or isinstance(personality, dict)
            
            print(f"✅ 成功获取人格: {first_id}")
        else:
            print("⚠️ 没有可用的人格进行测试")
    
    def test_get_nonexistent_personality(self):
        """测试获取不存在的人格"""
        personality = chat_engine.personality_manager.get_personality("non_existent_999")
        
        # 应该返回None或使用默认人格
        print(f"✅ 不存在的人格返回: {type(personality).__name__ if personality else 'None'}")
    
    async def test_apply_personality_in_generation(self):
        """测试在消息生成中应用人格"""
        # 获取可用人格
        personalities = chat_engine.personality_manager.list_personalities()
        
        if len(personalities) > 0:
            personality_id = personalities[0].get('id')
            
            messages = [{"role": "user", "content": "Hello"}]
            
            response = await chat_engine.generate_response(
                messages=messages,
                conversation_id="test_personality_apply",
                personality_id=personality_id,
                stream=False
            )
            
            assert isinstance(response, dict)
            assert "content" in response
            
            print(f"✅ 成功应用人格 {personality_id} 进行生成")
        else:
            print("⚠️ 没有可用的人格进行测试")
    
    async def test_personality_with_tools(self):
        """测试人格的工具限制"""
        # 测试获取人格允许的工具
        personalities = chat_engine.personality_manager.list_personalities()
        
        if len(personalities) > 0:
            personality_id = personalities[0].get('id')
            
            # 获取该人格的工具schema
            schema = await chat_engine.get_allowed_tools_schema(personality_id=personality_id)
            
            assert isinstance(schema, list)
            
            print(f"✅ 人格 {personality_id} 的工具数: {len(schema)}")
        else:
            print("⚠️ 没有可用的人格进行测试")
    
    async def test_default_personality_behavior(self):
        """测试默认人格行为"""
        messages = [{"role": "user", "content": "Test default"}]
        
        # 不指定personality_id
        response = await chat_engine.generate_response(
            messages=messages,
            conversation_id="test_default_personality",
            stream=False
        )
        
        assert isinstance(response, dict)
        assert "content" in response
        
        print("✅ 默认人格应用正常")
    
    async def test_personality_switching(self):
        """测试在不同请求中切换人格"""
        personalities = chat_engine.personality_manager.list_personalities()
        
        if len(personalities) >= 2:
            messages = [{"role": "user", "content": "Test"}]
            
            # 使用第一个人格
            response1 = await chat_engine.generate_response(
                messages=messages,
                conversation_id="test_switch_1",
                personality_id=personalities[0].get('id'),
                stream=False
            )
            
            # 使用第二个人格
            response2 = await chat_engine.generate_response(
                messages=messages,
                conversation_id="test_switch_2",
                personality_id=personalities[1].get('id'),
                stream=False
            )
            
            assert isinstance(response1, dict)
            assert isinstance(response2, dict)
            
            print("✅ 人格切换测试通过")
        else:
            print("⚠️ 人格数量不足，无法测试切换")
    
    async def test_personality_in_get_supported_personalities(self):
        """测试get_supported_personalities接口"""
        personalities = await chat_engine.get_supported_personalities()
        
        assert isinstance(personalities, list)
        
        if len(personalities) > 0:
            p = personalities[0]
            assert "id" in p
            assert "name" in p
            
            print(f"✅ get_supported_personalities返回 {len(personalities)} 个人格")
        else:
            print("⚠️ get_supported_personalities返回空列表")
    
    def test_personality_data_structure(self):
        """测试人格数据结构"""
        personalities = chat_engine.personality_manager.list_personalities()
        
        if len(personalities) > 0:
            first_id = personalities[0].get('id')
            personality = chat_engine.personality_manager.get_personality(first_id)
            
            if personality:
                # 检查是否有system_prompt
                if hasattr(personality, 'system_prompt'):
                    assert isinstance(personality.system_prompt, str)
                    print(f"✅ 人格包含system_prompt (长度: {len(personality.system_prompt)})")
                elif isinstance(personality, dict) and 'system_prompt' in personality:
                    assert isinstance(personality['system_prompt'], str)
                    print(f"✅ 人格包含system_prompt (长度: {len(personality['system_prompt'])})")
                
                # 检查是否有allowed_tools
                if hasattr(personality, 'allowed_tools'):
                    assert isinstance(personality.allowed_tools, (list, type(None)))
                    print(f"✅ 人格包含allowed_tools配置")
                elif isinstance(personality, dict) and 'allowed_tools' in personality:
                    assert isinstance(personality['allowed_tools'], (list, type(None)))
                    print(f"✅ 人格包含allowed_tools配置")
        else:
            print("⚠️ 没有可用的人格进行数据结构测试")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

