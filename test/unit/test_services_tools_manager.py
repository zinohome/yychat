"""
services/tools/manager.py tests
Tests the ToolManager class functionality
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from services.tools.manager import ToolManager


class TestToolManager:
    def test_tool_manager_initialization(self):
        """Test ToolManager initialization"""
        manager = ToolManager()
        assert manager is not None

    @pytest.mark.asyncio
    async def test_execute_tool_success(self):
        """Test successful tool execution"""
        manager = ToolManager()
        
        # Mock tool
        mock_tool = AsyncMock()
        mock_tool.execute.return_value = {"result": "success"}
        
        with patch('services.tools.manager.tool_registry.get_tool', return_value=mock_tool):
            result = await manager.execute_tool("test_tool", {"param": "value"})
            
            assert result["success"] is True
            assert result["result"] == {"result": "success"}
            assert result["tool_name"] == "test_tool"
            mock_tool.execute.assert_called_once_with({"param": "value"})

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self):
        """Test tool execution when tool is not found"""
        manager = ToolManager()
        
        with patch('services.tools.manager.tool_registry.get_tool', return_value=None):
            result = await manager.execute_tool("nonexistent_tool", {"param": "value"})
            
            assert result["success"] is False
            assert "未找到" in result["error"]
            assert result["tool_name"] == "nonexistent_tool"

    @pytest.mark.asyncio
    async def test_execute_tool_exception(self):
        """Test tool execution when tool raises exception"""
        manager = ToolManager()
        
        # Mock tool that raises exception
        mock_tool = AsyncMock()
        mock_tool.execute.side_effect = Exception("Tool execution failed")
        
        with patch('services.tools.manager.tool_registry.get_tool', return_value=mock_tool):
            result = await manager.execute_tool("failing_tool", {"param": "value"})
            
            assert result["success"] is False
            assert result["error"] == "Tool execution failed"
            assert result["tool_name"] == "failing_tool"

    @pytest.mark.asyncio
    async def test_execute_tools_concurrently_success(self):
        """Test concurrent tool execution with all tools succeeding"""
        manager = ToolManager()
        
        # Mock tools
        mock_tool1 = AsyncMock()
        mock_tool1.execute.return_value = {"result1": "success"}
        mock_tool2 = AsyncMock()
        mock_tool2.execute.return_value = {"result2": "success"}
        
        with patch('services.tools.manager.tool_registry.get_tool') as mock_get_tool:
            mock_get_tool.side_effect = [mock_tool1, mock_tool2]
            
            tool_calls = [
                {"name": "tool1", "parameters": {"param1": "value1"}},
                {"name": "tool2", "parameters": {"param2": "value2"}}
            ]
            
            results = await manager.execute_tools_concurrently(tool_calls)
            
            assert len(results) == 2
            assert results[0]["success"] is True
            assert results[0]["result"] == {"result1": "success"}
            assert results[0]["tool_name"] == "tool1"
            assert results[1]["success"] is True
            assert results[1]["result"] == {"result2": "success"}
            assert results[1]["tool_name"] == "tool2"

    @pytest.mark.asyncio
    async def test_execute_tools_concurrently_mixed_results(self):
        """Test concurrent tool execution with mixed success/failure"""
        manager = ToolManager()
        
        # Mock tools - one succeeds, one fails
        mock_tool1 = AsyncMock()
        mock_tool1.execute.return_value = {"result1": "success"}
        mock_tool2 = AsyncMock()
        mock_tool2.execute.side_effect = Exception("Tool2 failed")
        
        with patch('services.tools.manager.tool_registry.get_tool') as mock_get_tool:
            mock_get_tool.side_effect = [mock_tool1, mock_tool2]
            
            tool_calls = [
                {"name": "tool1", "parameters": {"param1": "value1"}},
                {"name": "tool2", "parameters": {"param2": "value2"}}
            ]
            
            results = await manager.execute_tools_concurrently(tool_calls)
            
            assert len(results) == 2
            assert results[0]["success"] is True
            assert results[0]["result"] == {"result1": "success"}
            assert results[0]["tool_name"] == "tool1"
            assert results[1]["success"] is False
            assert results[1]["error"] == "Tool2 failed"
            assert results[1]["tool_name"] == "tool2"

    @pytest.mark.asyncio
    async def test_execute_tools_concurrently_tool_not_found(self):
        """Test concurrent tool execution with tool not found"""
        manager = ToolManager()
        
        # Mock tools - one found, one not found
        mock_tool1 = AsyncMock()
        mock_tool1.execute.return_value = {"result1": "success"}
        
        with patch('services.tools.manager.tool_registry.get_tool') as mock_get_tool:
            mock_get_tool.side_effect = [mock_tool1, None]
            
            tool_calls = [
                {"name": "tool1", "parameters": {"param1": "value1"}},
                {"name": "nonexistent_tool", "parameters": {"param2": "value2"}}
            ]
            
            results = await manager.execute_tools_concurrently(tool_calls)
            
            assert len(results) == 2
            assert results[0]["success"] is True
            assert results[0]["result"] == {"result1": "success"}
            assert results[0]["tool_name"] == "tool1"
            assert results[1]["success"] is False
            assert "未找到" in results[1]["error"]
            assert results[1]["tool_name"] == "nonexistent_tool"

    @pytest.mark.asyncio
    async def test_execute_tools_concurrently_empty_list(self):
        """Test concurrent tool execution with empty list"""
        manager = ToolManager()
        
        results = await manager.execute_tools_concurrently([])
        
        assert results == []

    @pytest.mark.asyncio
    async def test_execute_tools_concurrently_single_tool(self):
        """Test concurrent tool execution with single tool"""
        manager = ToolManager()
        
        # Mock tool
        mock_tool = AsyncMock()
        mock_tool.execute.return_value = {"result": "success"}
        
        with patch('services.tools.manager.tool_registry.get_tool', return_value=mock_tool):
            tool_calls = [
                {"name": "single_tool", "parameters": {"param": "value"}}
            ]
            
            results = await manager.execute_tools_concurrently(tool_calls)
            
            assert len(results) == 1
            assert results[0]["success"] is True
            assert results[0]["result"] == {"result": "success"}
            assert results[0]["tool_name"] == "single_tool"

    @pytest.mark.asyncio
    async def test_execute_tools_concurrently_asyncio_gather_exception(self):
        """Test concurrent tool execution when asyncio.gather returns exception"""
        manager = ToolManager()
        
        # Mock tool that raises exception
        mock_tool = AsyncMock()
        mock_tool.execute.side_effect = Exception("Async exception")
        
        with patch('services.tools.manager.tool_registry.get_tool', return_value=mock_tool):
            tool_calls = [
                {"name": "failing_tool", "parameters": {"param": "value"}}
            ]
            
            results = await manager.execute_tools_concurrently(tool_calls)
            
            assert len(results) == 1
            assert results[0]["success"] is False
            assert results[0]["error"] == "Async exception"
            assert results[0]["tool_name"] == "failing_tool"

    @pytest.mark.asyncio
    async def test_execute_tool_with_complex_parameters(self):
        """Test tool execution with complex parameters"""
        manager = ToolManager()
        
        # Mock tool
        mock_tool = AsyncMock()
        mock_tool.execute.return_value = {"complex_result": "success"}
        
        complex_params = {
            "string_param": "test",
            "number_param": 42,
            "list_param": [1, 2, 3],
            "dict_param": {"nested": "value"},
            "bool_param": True,
            "none_param": None
        }
        
        with patch('services.tools.manager.tool_registry.get_tool', return_value=mock_tool):
            result = await manager.execute_tool("complex_tool", complex_params)
            
            assert result["success"] is True
            assert result["result"] == {"complex_result": "success"}
            assert result["tool_name"] == "complex_tool"
            mock_tool.execute.assert_called_once_with(complex_params)

    @pytest.mark.asyncio
    async def test_execute_tool_with_empty_parameters(self):
        """Test tool execution with empty parameters"""
        manager = ToolManager()
        
        # Mock tool
        mock_tool = AsyncMock()
        mock_tool.execute.return_value = {"result": "success"}
        
        with patch('services.tools.manager.tool_registry.get_tool', return_value=mock_tool):
            result = await manager.execute_tool("empty_params_tool", {})
            
            assert result["success"] is True
            assert result["result"] == {"result": "success"}
            assert result["tool_name"] == "empty_params_tool"
            mock_tool.execute.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_execute_tools_concurrently_large_number(self):
        """Test concurrent tool execution with large number of tools"""
        manager = ToolManager()
        
        # Mock tools
        mock_tools = []
        for i in range(10):
            mock_tool = AsyncMock()
            mock_tool.execute.return_value = {"result": f"success_{i}"}
            mock_tools.append(mock_tool)
        
        with patch('services.tools.manager.tool_registry.get_tool') as mock_get_tool:
            mock_get_tool.side_effect = mock_tools
            
            tool_calls = [
                {"name": f"tool_{i}", "parameters": {"param": f"value_{i}"}}
                for i in range(10)
            ]
            
            results = await manager.execute_tools_concurrently(tool_calls)
            
            assert len(results) == 10
            for i, result in enumerate(results):
                assert result["success"] is True
                assert result["result"] == {"result": f"success_{i}"}
                assert result["tool_name"] == f"tool_{i}"
