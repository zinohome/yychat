"""
core/tools.py tests
Tests get_available_tools function
"""
import pytest
from unittest.mock import patch, MagicMock

from core.tools import get_available_tools


class TestGetAvailableTools:
    def test_get_available_tools_success(self):
        """Test successful tool retrieval"""
        mock_tools = [
            {"name": "calculator", "description": "Perform calculations"},
            {"name": "search", "description": "Search information"}
        ]
        
        with patch('core.tools.tool_registry') as mock_registry:
            mock_registry.get_functions_schema.return_value = mock_tools
            
            result = get_available_tools()
            
            assert result == mock_tools
            mock_registry.get_functions_schema.assert_called_once()

    def test_get_available_tools_empty_result(self):
        """Test tool retrieval with empty result"""
        with patch('core.tools.tool_registry') as mock_registry:
            mock_registry.get_functions_schema.return_value = []
            
            result = get_available_tools()
            
            assert result == []
            mock_registry.get_functions_schema.assert_called_once()

    def test_get_available_tools_error(self):
        """Test tool retrieval with error"""
        with patch('core.tools.tool_registry') as mock_registry:
            mock_registry.get_functions_schema.side_effect = Exception("Registry error")
            
            result = get_available_tools()
            
            assert result == []
            mock_registry.get_functions_schema.assert_called_once()

    def test_get_available_tools_import_error(self):
        """Test tool retrieval with import error"""
        with patch('core.tools.tool_registry') as mock_registry:
            mock_registry.get_functions_schema.side_effect = ImportError("Import error")
            result = get_available_tools()
            assert result == []

    def test_get_available_tools_none_result(self):
        """Test tool retrieval with None result"""
        with patch('core.tools.tool_registry') as mock_registry:
            mock_registry.get_functions_schema.return_value = None
            
            result = get_available_tools()
            
            assert result is None

    def test_get_available_tools_complex_tools(self):
        """Test tool retrieval with complex tool definitions"""
        complex_tools = [
            {
                "name": "advanced_calculator",
                "description": "Advanced mathematical operations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
        
        with patch('core.tools.tool_registry') as mock_registry:
            mock_registry.get_functions_schema.return_value = complex_tools
            
            result = get_available_tools()
            
            assert result == complex_tools
            assert len(result) == 2
            assert result[0]["name"] == "advanced_calculator"
            assert result[1]["name"] == "web_search"

    def test_get_available_tools_multiple_calls(self):
        """Test multiple calls to get_available_tools"""
        mock_tools = [{"name": "test_tool", "description": "Test tool"}]
        
        with patch('core.tools.tool_registry') as mock_registry:
            mock_registry.get_functions_schema.return_value = mock_tools
            
            # Call multiple times
            result1 = get_available_tools()
            result2 = get_available_tools()
            result3 = get_available_tools()
            
            assert result1 == mock_tools
            assert result2 == mock_tools
            assert result3 == mock_tools
            assert mock_registry.get_functions_schema.call_count == 3

    def test_get_available_tools_different_errors(self):
        """Test tool retrieval with different types of errors"""
        error_types = [
            ValueError("Value error"),
            RuntimeError("Runtime error"),
            AttributeError("Attribute error"),
            KeyError("Key error")
        ]
        
        for error in error_types:
            with patch('core.tools.tool_registry') as mock_registry:
                mock_registry.get_functions_schema.side_effect = error
                
                result = get_available_tools()
                
                assert result == []
                mock_registry.get_functions_schema.assert_called_once()

    def test_get_available_tools_logging(self):
        """Test that errors are properly logged"""
        with patch('core.tools.tool_registry') as mock_registry, \
             patch('core.tools.log') as mock_log:
            
            mock_registry.get_functions_schema.side_effect = Exception("Test error")
            
            result = get_available_tools()
            
            assert result == []
            mock_log.error.assert_called_once_with("获取可用工具失败: Test error")

    def test_get_available_tools_return_type(self):
        """Test that return type is correct"""
        mock_tools = [{"name": "test_tool"}]
        
        with patch('core.tools.tool_registry') as mock_registry:
            mock_registry.get_functions_schema.return_value = mock_tools
            
            result = get_available_tools()
            
            assert isinstance(result, list)
            assert all(isinstance(tool, dict) for tool in result)

    def test_get_available_tools_with_mixed_data(self):
        """Test tool retrieval with mixed data types"""
        mixed_tools = [
            {"name": "string_tool", "type": "string"},
            {"name": "number_tool", "type": 42},
            {"name": "bool_tool", "type": True},
            {"name": "list_tool", "type": [1, 2, 3]},
            {"name": "dict_tool", "type": {"nested": "value"}}
        ]
        
        with patch('core.tools.tool_registry') as mock_registry:
            mock_registry.get_functions_schema.return_value = mixed_tools
            
            result = get_available_tools()
            
            assert result == mixed_tools
            assert len(result) == 5

    def test_get_available_tools_performance(self):
        """Test performance of get_available_tools"""
        import time
        
        mock_tools = [{"name": f"tool_{i}"} for i in range(100)]
        
        with patch('core.tools.tool_registry') as mock_registry:
            mock_registry.get_functions_schema.return_value = mock_tools
            
            start_time = time.time()
            result = get_available_tools()
            end_time = time.time()
            
            assert result == mock_tools
            # Should complete quickly (less than 0.1 seconds)
            assert end_time - start_time < 0.1

    def test_get_available_tools_concurrent_access(self):
        """Test concurrent access to get_available_tools"""
        import threading
        import time
        
        mock_tools = [{"name": "concurrent_tool"}]
        results = []
        
        with patch('core.tools.tool_registry') as mock_registry:
            mock_registry.get_functions_schema.return_value = mock_tools
            
            def get_tools():
                result = get_available_tools()
                results.append(result)
                time.sleep(0.001)  # Small delay
            
            # Create multiple threads
            threads = []
            for _ in range(10):
                thread = threading.Thread(target=get_tools)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # All threads should have completed successfully
            assert len(results) == 10
            assert all(result == mock_tools for result in results)
