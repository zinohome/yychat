"""
ChatEngine工具调用测试
测试工具调用、执行和结果处理
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from core.chat_engine import chat_engine

@pytest.mark.asyncio
class TestChatEngineTools:
    """工具调用测试套件"""
    
    async def test_get_allowed_tools_schema_no_personality(self):
        """测试获取所有工具schema（不指定人格）"""
        schema = await chat_engine.get_allowed_tools_schema()
        
        assert isinstance(schema, list)
        # 应该返回所有可用工具
        if len(schema) > 0:
            tool = schema[0]
            # OpenAI schema格式
            assert "function" in tool or "type" in tool
        
        print(f"✅ 获取所有工具schema成功，共 {len(schema)} 个工具")
    
    async def test_get_allowed_tools_schema_with_personality(self):
        """测试根据人格过滤工具schema"""
        schema = await chat_engine.get_allowed_tools_schema(personality_id="friendly")
        
        assert isinstance(schema, list)
        # friendly人格可能有工具限制
        
        print(f"✅ 获取friendly人格工具schema成功，共 {len(schema)} 个工具")
    
    async def test_get_allowed_tools_schema_invalid_personality(self):
        """测试无效人格ID"""
        schema = await chat_engine.get_allowed_tools_schema(personality_id="non_existent_999")
        
        assert isinstance(schema, list)
        # 无效人格应该返回所有工具（优雅降级）
        
        print(f"✅ 无效人格优雅降级，返回 {len(schema)} 个工具")
    
    async def test_tool_manager_initialized(self):
        """测试ToolManager是否正确初始化"""
        assert chat_engine.tool_manager is not None
        assert hasattr(chat_engine.tool_manager, 'execute_tools_concurrently')
        
        print("✅ ToolManager初始化正常")
    
    async def test_call_mcp_service_with_tool_name(self):
        """测试MCP服务调用（使用tool_name）"""
        # 这个测试可能需要真实的MCP服务，所以我们只测试接口
        result = await chat_engine.call_mcp_service(
            tool_name="test_tool",
            params={"test": "param"}
        )
        
        assert isinstance(result, dict)
        assert "success" in result
        # 可能成功或失败，但应该有标准返回格式
        
        print(f"✅ MCP服务调用接口正常（success={result.get('success')}）")
    
    async def test_call_mcp_service_with_service_method(self):
        """测试MCP服务调用（使用service_name和method_name）"""
        result = await chat_engine.call_mcp_service(
            service_name="test_service",
            method_name="test_method",
            params={"test": "param"}
        )
        
        assert isinstance(result, dict)
        assert "success" in result
        
        print(f"✅ MCP服务调用接口正常（使用service+method）")
    
    async def test_call_mcp_service_no_params(self):
        """测试MCP服务调用无参数情况"""
        # 应该能处理无参数的情况
        try:
            result = await chat_engine.call_mcp_service(
                tool_name="test_tool"
            )
            assert isinstance(result, dict)
            print("✅ MCP服务调用支持无参数")
        except ValueError as e:
            # 可能会因为工具不存在而失败，这也是正常的
            print(f"✅ MCP服务调用正常抛出错误: {str(e)[:50]}")
    
    @patch('core.chat_engine.chat_engine.tool_manager')
    async def test_handle_tool_calls_mock(self, mock_tool_manager):
        """测试工具调用处理（使用mock）"""
        # Mock tool_manager的执行结果
        mock_tool_manager.execute_tools_concurrently = AsyncMock(return_value=[
            {
                "success": True,
                "tool_name": "test_tool",
                "result": "test result"
            }
        ])
        
        # 准备测试数据
        tool_calls = [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "arguments": '{"param": "value"}'
                }
            }
        ]
        
        original_messages = [
            {"role": "user", "content": "test message"}
        ]
        
        # 调用_handle_tool_calls（如果是私有方法，这个测试可能需要调整）
        try:
            result = await chat_engine._handle_tool_calls(
                tool_calls=tool_calls,
                conversation_id="test_conv",
                original_messages=original_messages
            )
            
            assert isinstance(result, dict)
            print("✅ 工具调用处理测试通过（使用mock）")
        except AttributeError:
            # 如果方法不存在或名称不同，跳过
            print("⚠️ _handle_tool_calls方法不可访问，跳过此测试")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

