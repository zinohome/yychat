import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from services.tools.manager import ToolManager
from services.tools.registry import tool_registry

# 测试ToolManager的execute_tool方法
@pytest.mark.asyncio
async def test_tool_manager_execute_tool():
    # 创建模拟工具
    mock_tool = AsyncMock()
    mock_tool.execute.return_value = "Tool execution result"
    
    # 使用patch替换get_tool方法
    with patch('services.tools.registry.ToolRegistry.get_tool', return_value=mock_tool):
        manager = ToolManager()
        result = await manager.execute_tool("test_tool", {"param1": "value1"})
        
        # 验证结果
        assert result["success"] is True
        assert result["result"] == "Tool execution result"
        mock_tool.execute.assert_called_once_with({"param1": "value1"})

# 测试执行不存在的工具
@pytest.mark.asyncio
async def test_tool_manager_execute_non_existent_tool():
    # 使用patch让get_tool返回None
    with patch('services.tools.registry.ToolRegistry.get_tool', return_value=None):
        manager = ToolManager()
        result = await manager.execute_tool("non_existent_tool", {"param1": "value1"})
        
        # 验证结果
        assert result is None

# 测试工具执行异常
@pytest.mark.asyncio
async def test_tool_manager_execute_tool_exception():
    # 创建抛出异常的模拟工具
    mock_tool = AsyncMock()
    mock_tool.execute.side_effect = Exception("Tool execution error")
    
    # 使用patch替换get_tool方法
    with patch('services.tools.registry.ToolRegistry.get_tool', return_value=mock_tool):
        manager = ToolManager()
        result = await manager.execute_tool("test_tool", {"param1": "value1"})
        
        # 验证结果
        assert result["success"] is False
        assert "error" in result
        assert "Tool execution error" in result["error"]

# 测试execute_tools_concurrently方法 - 全部成功
@pytest.mark.asyncio
async def test_tool_manager_execute_tools_concurrently_success():
    # 创建模拟工具
    mock_tool1 = AsyncMock()
    mock_tool1.execute.return_value = "Result 1"
    
    mock_tool2 = AsyncMock()
    mock_tool2.execute.return_value = "Result 2"
    
    # 使用side_effect让get_tool根据工具名返回不同的模拟工具
    def get_tool_mock(tool_name):
        if tool_name == "tool1":
            return mock_tool1
        elif tool_name == "tool2":
            return mock_tool2
        return None
    
    # 使用patch替换get_tool方法
    with patch('services.tools.registry.ToolRegistry.get_tool', side_effect=get_tool_mock):
        manager = ToolManager()
        tool_calls = [
            {"name": "tool1", "parameters": {"param1": "value1"}},
            {"name": "tool2", "parameters": {"param2": "value2"}}
        ]
        results = await manager.execute_tools_concurrently(tool_calls)
        
        # 验证结果
        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[0]["result"] == "Result 1"
        assert results[0]["tool_name"] == "tool1"
        assert results[1]["success"] is True
        assert results[1]["result"] == "Result 2"
        assert results[1]["tool_name"] == "tool2"

# 测试execute_tools_concurrently方法 - 部分成功
@pytest.mark.asyncio
async def test_tool_manager_execute_tools_concurrently_partial_failure():
    # 创建模拟工具，一个成功，一个抛出异常
    mock_tool1 = AsyncMock()
    mock_tool1.execute.return_value = "Result 1"
    
    mock_tool2 = AsyncMock()
    mock_tool2.execute.side_effect = Exception("Tool 2 error")
    
    # 使用side_effect让get_tool根据工具名返回不同的模拟工具
    def get_tool_mock(tool_name):
        if tool_name == "tool1":
            return mock_tool1
        elif tool_name == "tool2":
            return mock_tool2
        return None
    
    # 使用patch替换get_tool方法
    with patch('services.tools.registry.ToolRegistry.get_tool', side_effect=get_tool_mock):
        manager = ToolManager()
        tool_calls = [
            {"name": "tool1", "parameters": {"param1": "value1"}},
            {"name": "tool2", "parameters": {"param2": "value2"}}
        ]
        results = await manager.execute_tools_concurrently(tool_calls)
        
        # 验证结果
        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[0]["result"] == "Result 1"
        assert results[1]["success"] is False
        assert "error" in results[1]
        assert "Tool 2 error" in results[1]["error"]

# 测试execute_tools_concurrently方法 - 空列表
@pytest.mark.asyncio
async def test_tool_manager_execute_tools_concurrently_empty_list():
    manager = ToolManager()
    results = await manager.execute_tools_concurrently([])
    
    # 验证结果是空列表
    assert len(results) == 0

# 测试execute_tools_concurrently方法 - 包含不存在的工具
@pytest.mark.asyncio
async def test_tool_manager_execute_tools_concurrently_with_non_existent():
    # 使用patch让get_tool返回None
    with patch('services.tools.registry.ToolRegistry.get_tool', return_value=None):
        manager = ToolManager()
        tool_calls = [
            {"name": "non_existent_tool", "parameters": {"param1": "value1"}}
        ]
        results = await manager.execute_tools_concurrently(tool_calls)
        
        # 验证结果
        assert len(results) == 1
        assert results[0] is None