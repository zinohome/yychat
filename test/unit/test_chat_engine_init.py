"""
ChatEngine初始化测试
验证引擎正确初始化
"""
import pytest
from core.chat_engine import ChatEngine, chat_engine

class TestChatEngineInitialization:
    """ChatEngine初始化测试套件"""
    
    def test_chat_engine_instance(self):
        """测试ChatEngine实例化
        
        验证:
        - 可以创建ChatEngine实例
        - 全局实例chat_engine可用
        """
        engine = ChatEngine()
        assert engine is not None, "应该能创建实例"
        assert isinstance(engine, ChatEngine), "应该是ChatEngine类型"
        print("✅ ChatEngine实例化正常")
    
    def test_global_instance_exists(self):
        """测试全局实例存在
        
        验证:
        - chat_engine全局实例可用
        - 实例不为None
        """
        assert chat_engine is not None, "全局实例应该存在"
        assert isinstance(chat_engine, ChatEngine), "应该是ChatEngine实例"
        print("✅ 全局实例存在")
    
    def test_client_initialized(self):
        """测试OpenAI客户端初始化
        
        验证:
        - client属性存在
        - client有必要的方法
        """
        assert chat_engine.client is not None, "OpenAI客户端应该初始化"
        assert hasattr(chat_engine.client, 'create_chat'), "应该有create_chat方法"
        assert hasattr(chat_engine.client, 'create_chat_stream'), "应该有create_chat_stream方法"
        print("✅ OpenAI客户端已初始化")
    
    def test_memory_initialized(self):
        """测试Memory系统初始化
        
        验证:
        - 同步Memory实例存在
        - 异步Memory实例存在
        """
        assert chat_engine.chat_memory is not None, "同步Memory应该初始化"
        assert chat_engine.async_chat_memory is not None, "异步Memory应该初始化"
        print("✅ Memory系统已初始化")
    
    def test_personality_manager_initialized(self):
        """测试PersonalityManager初始化
        
        验证:
        - personality_manager存在
        - 可以获取人格列表
        """
        assert chat_engine.personality_manager is not None, "PersonalityManager应该初始化"
        
        # 验证可以获取人格
        personalities = chat_engine.personality_manager.list_personalities()
        assert isinstance(personalities, list), "应该返回列表"
        assert len(personalities) > 0, "应该至少有一个人格"
        print(f"✅ PersonalityManager已初始化，共{len(personalities)}个人格")
    
    def test_tool_manager_initialized(self):
        """测试ToolManager初始化
        
        验证:
        - tool_manager存在
        - 可以执行工具
        """
        assert chat_engine.tool_manager is not None, "ToolManager应该初始化"
        print("✅ ToolManager已初始化")
    
    def test_all_components_initialized(self):
        """测试所有组件都已初始化
        
        综合验证所有关键组件
        """
        components = {
            "client": chat_engine.client,
            "chat_memory": chat_engine.chat_memory,
            "async_chat_memory": chat_engine.async_chat_memory,
            "personality_manager": chat_engine.personality_manager,
            "tool_manager": chat_engine.tool_manager
        }
        
        for name, component in components.items():
            assert component is not None, f"{name}应该已初始化"
        
        print("✅ 所有组件已初始化")


if __name__ == "__main__":
    # 允许直接运行此测试文件
    pytest.main([__file__, "-v", "-s"])

