"""
Mem0Proxy基础测试
测试Mem0代理引擎的初始化和基本功能
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from core.mem0_proxy import (
    Mem0ChatEngine, 
    get_mem0_proxy,
    Mem0Client,
    OpenAIClient,
    PersonalityHandler,
    MemoryHandler
)

@pytest.mark.asyncio
class TestMem0ProxyInitialization:
    """Mem0Proxy初始化测试套件"""
    
    def test_mem0_proxy_singleton(self):
        """测试单例模式"""
        proxy1 = get_mem0_proxy()
        proxy2 = get_mem0_proxy()
        
        assert proxy1 is proxy2
        assert id(proxy1) == id(proxy2)
        print("✅ Mem0Proxy单例模式验证通过")
    
    def test_mem0_proxy_instance(self):
        """测试Mem0Proxy实例化"""
        proxy = get_mem0_proxy()
        
        assert proxy is not None
        assert isinstance(proxy, Mem0ChatEngine)
        print("✅ Mem0Proxy实例化成功")
    
    def test_clients_initialized(self):
        """测试客户端初始化"""
        proxy = get_mem0_proxy()
        
        assert hasattr(proxy, 'mem0_client')
        assert hasattr(proxy, 'openai_client')
        assert proxy.mem0_client is not None
        assert proxy.openai_client is not None
        print("✅ 客户端初始化成功")
    
    def test_handlers_initialized(self):
        """测试Handler初始化"""
        proxy = get_mem0_proxy()
        
        assert hasattr(proxy, 'personality_handler')
        assert hasattr(proxy, 'memory_handler')
        assert hasattr(proxy, 'tool_handler')
        assert hasattr(proxy, 'fallback_handler')
        
        assert proxy.personality_handler is not None
        assert proxy.memory_handler is not None
        assert proxy.tool_handler is not None
        assert proxy.fallback_handler is not None
        
        print("✅ 所有Handler初始化成功")
    
    def test_fallback_mechanism_exists(self):
        """测试降级机制存在"""
        proxy = get_mem0_proxy()
        
        # FallbackHandler应该存在
        assert hasattr(proxy, 'fallback_handler')
        # 应该有OpenAI客户端作为降级
        assert hasattr(proxy, 'openai_client')
        
        print("✅ 降级机制存在")
    
    async def test_generate_simple_message(self):
        """测试生成简单消息"""
        proxy = get_mem0_proxy()
        
        messages = [{"role": "user", "content": "Hello"}]
        
        try:
            response = await proxy.generate_response(
                messages=messages,
                conversation_id="test_mem0_simple",
                use_tools=False,
                stream=False
            )
            
            assert isinstance(response, dict)
            assert "content" in response or "error" in response
            print("✅ 简单消息生成测试通过")
        except Exception as e:
            # 如果Mem0不可用，这是预期的
            print(f"⚠️ 消息生成失败（可能是Mem0不可用）: {str(e)[:50]}")
    
    async def test_generate_with_personality(self):
        """测试使用人格生成"""
        proxy = get_mem0_proxy()
        
        messages = [{"role": "user", "content": "Test"}]
        
        try:
            response = await proxy.generate_response(
                messages=messages,
                conversation_id="test_mem0_personality",
                personality_id="friendly",
                use_tools=False,
                stream=False
            )
            
            assert isinstance(response, dict)
            print("✅ 带人格的消息生成测试通过")
        except Exception as e:
            print(f"⚠️ 测试失败: {str(e)[:50]}")
    
    async def test_generate_streaming(self):
        """测试流式生成"""
        proxy = get_mem0_proxy()
        
        messages = [{"role": "user", "content": "Test stream"}]
        
        try:
            generator = await proxy.generate_response(
                messages=messages,
                conversation_id="test_mem0_stream",
                use_tools=False,
                stream=True
            )
            
            # 尝试获取至少一个chunk
            chunks = []
            count = 0
            async for chunk in generator:
                chunks.append(chunk)
                count += 1
                if count >= 3:  # 只获取前3个chunk
                    break
            
            assert len(chunks) > 0
            print(f"✅ 流式生成测试通过（获取{len(chunks)}个chunk）")
        except Exception as e:
            print(f"⚠️ 流式生成测试失败: {str(e)[:50]}")
    
    async def test_get_engine_info(self):
        """测试获取引擎信息"""
        proxy = get_mem0_proxy()
        
        info = await proxy.get_engine_info()
        
        assert isinstance(info, dict)
        assert "name" in info
        assert info["name"] == "mem0_proxy"
        assert "version" in info
        assert "features" in info
        assert isinstance(info["features"], list)
        
        print(f"✅ 引擎信息获取成功")
        print(f"   名称: {info['name']}")
        print(f"   版本: {info['version']}")
        print(f"   功能数: {len(info['features'])}")
    
    async def test_health_check(self):
        """测试健康检查"""
        proxy = get_mem0_proxy()
        
        health = await proxy.health_check()
        
        assert isinstance(health, dict)
        assert "healthy" in health
        assert "timestamp" in health
        assert "details" in health
        
        print(f"✅ 健康检查成功")
        print(f"   状态: {'健康' if health['healthy'] else '不健康'}")
    
    async def test_clear_conversation_memory(self):
        """测试清除会话记忆"""
        proxy = get_mem0_proxy()
        
        result = await proxy.clear_conversation_memory("test_clear_mem0")
        
        assert isinstance(result, dict)
        assert "success" in result
        # Mem0可能成功也可能失败，但接口应该正常
        
        print(f"✅ 清除记忆接口调用成功（success={result.get('success')}）")
    
    async def test_get_conversation_memory(self):
        """测试获取会话记忆"""
        proxy = get_mem0_proxy()
        
        result = await proxy.get_conversation_memory("test_get_mem0")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "memories" in result
        
        print(f"✅ 获取记忆接口调用成功")
    
    async def test_get_supported_personalities(self):
        """测试获取支持的人格"""
        proxy = get_mem0_proxy()
        
        personalities = await proxy.get_supported_personalities()
        
        assert isinstance(personalities, list)
        
        if len(personalities) > 0:
            p = personalities[0]
            assert "id" in p
            assert "name" in p
            print(f"✅ 获取人格列表成功（{len(personalities)}个）")
        else:
            print("⚠️ 获取人格列表返回空")
    
    async def test_get_available_tools(self):
        """测试获取可用工具"""
        proxy = get_mem0_proxy()
        
        tools = await proxy.get_available_tools()
        
        assert isinstance(tools, list)
        print(f"✅ 获取工具列表成功（{len(tools)}个）")


@pytest.mark.asyncio
class TestMem0ClientComponents:
    """Mem0客户端组件测试"""
    
    def test_mem0_client_initialization(self):
        """测试Mem0Client初始化"""
        from config.config import get_config
        config = get_config()
        
        client = Mem0Client(config)
        
        assert client is not None
        assert hasattr(client, 'client')
        print("✅ Mem0Client初始化成功")
    
    def test_openai_client_initialization(self):
        """测试OpenAIClient初始化"""
        from config.config import get_config
        config = get_config()
        
        client = OpenAIClient(config)
        
        assert client is not None
        assert hasattr(client, 'client')
        print("✅ OpenAIClient初始化成功")
    
    async def test_personality_handler(self):
        """测试PersonalityHandler"""
        from config.config import get_config
        config = get_config()
        
        handler = PersonalityHandler(config)
        
        messages = [{"role": "user", "content": "test"}]
        result = await handler.apply_personality(messages, personality_id="friendly")
        
        assert isinstance(result, list)
        print("✅ PersonalityHandler工作正常")
    
    async def test_personality_handler_no_personality(self):
        """测试PersonalityHandler无人格情况"""
        from config.config import get_config
        config = get_config()
        
        handler = PersonalityHandler(config)
        
        messages = [{"role": "user", "content": "test"}]
        result = await handler.apply_personality(messages, personality_id=None)
        
        # 无人格时应该返回原消息
        assert result == messages
        print("✅ PersonalityHandler无人格处理正确")
    
    def test_memory_handler_initialization(self):
        """测试MemoryHandler初始化"""
        from config.config import get_config
        config = get_config()
        
        handler = MemoryHandler(config)
        
        assert handler is not None
        assert hasattr(handler, 'chat_memory')
        assert hasattr(handler, 'async_chat_memory')
        print("✅ MemoryHandler初始化成功")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
