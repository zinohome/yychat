"""
services/mcp/utils/mcp_client.py basic tests
Focus on core functionality with proper mocking
"""
import pytest
import json
from unittest.mock import MagicMock, patch

from services.mcp.utils.mcp_client import McpClient, McpStreamableHttpClient


class TestMcpClient:
    def test_mcp_client_initialization(self):
        """Test McpClient base class initialization"""
        class ConcreteMcpClient(McpClient):
            def close(self):
                pass
            
            def initialize(self):
                pass
            
            def send_message(self, data: dict) -> dict:
                return {"result": "test"}
        
        client = ConcreteMcpClient("test_client", "http://localhost:8000")
        
        assert client.name == "test_client"
        assert client.url == "http://localhost:8000"
        assert client.headers is None
        assert client.timeout == 50
        assert client.id_counter == 0

    def test_get_next_id(self):
        """Test ID counter functionality"""
        class ConcreteMcpClient(McpClient):
            def close(self):
                pass
            
            def initialize(self):
                pass
            
            def send_message(self, data: dict) -> dict:
                return {"result": "test"}
        
        client = ConcreteMcpClient("test_client", "http://localhost:8000")
        
        # Test ID counter increments
        assert client._get_next_id() == 1
        assert client._get_next_id() == 2
        assert client._get_next_id() == 3
        assert client.id_counter == 3

    def test_list_tools_success(self):
        """Test list_tools method with successful response"""
        class ConcreteMcpClient(McpClient):
            def close(self):
                pass
            
            def initialize(self):
                pass
            
            def send_message(self, data: dict) -> dict:
                return {"result": {"tools": [{"name": "test_tool"}]}}
        
        client = ConcreteMcpClient("test_client", "http://localhost:8000")
        
        tools = client.list_tools()
        
        assert tools == [{"name": "test_tool"}]

    def test_list_tools_unsupported_method(self):
        """Test list_tools method with unsupported method error"""
        class ConcreteMcpClient(McpClient):
            def close(self):
                pass
            
            def initialize(self):
                pass
            
            def send_message(self, data: dict) -> dict:
                return {"error": {"code": -32001, "message": "Unsupported method"}}
        
        client = ConcreteMcpClient("test_client", "http://localhost:8000")
        
        tools = client.list_tools()
        
        assert tools == []

    def test_list_tools_method_not_found(self):
        """Test list_tools method with method not found error"""
        class ConcreteMcpClient(McpClient):
            def close(self):
                pass
            
            def initialize(self):
                pass
            
            def send_message(self, data: dict) -> dict:
                return {"error": {"code": -32601, "message": "Method not found"}}
        
        client = ConcreteMcpClient("test_client", "http://localhost:8000")
        
        tools = client.list_tools()
        
        assert tools == []

    def test_list_tools_other_error(self):
        """Test list_tools method with other error"""
        class ConcreteMcpClient(McpClient):
            def close(self):
                pass
            
            def initialize(self):
                pass
            
            def send_message(self, data: dict) -> dict:
                return {"error": {"code": -1, "message": "Other error"}}
        
        client = ConcreteMcpClient("test_client", "http://localhost:8000")
        
        with pytest.raises(Exception, match="MCP Server tools/list error"):
            client.list_tools()

    def test_call_tool_success(self):
        """Test call_tool method with successful response"""
        class ConcreteMcpClient(McpClient):
            def close(self):
                pass
            
            def initialize(self):
                pass
            
            def send_message(self, data: dict) -> dict:
                return {"result": {"content": [{"text": "test_result"}]}}
        
        client = ConcreteMcpClient("test_client", "http://localhost:8000")
        
        result = client.call_tool("test_tool", {"param": "value"})
        
        assert result == [{"text": "test_result"}]

    def test_call_tool_error(self):
        """Test call_tool method with error response"""
        class ConcreteMcpClient(McpClient):
            def close(self):
                pass
            
            def initialize(self):
                pass
            
            def send_message(self, data: dict) -> dict:
                return {"error": {"code": -1, "message": "Tool error"}}
        
        client = ConcreteMcpClient("test_client", "http://localhost:8000")
        
        with pytest.raises(Exception, match="MCP Server tools/call error"):
            client.call_tool("test_tool", {"param": "value"})


class TestMcpStreamableHttpClient:
    def test_initialization(self):
        """Test McpStreamableHttpClient initialization"""
        client = McpStreamableHttpClient("test_client", "http://localhost:8000")
        
        assert client.name == "test_client"
        assert client.url == "http://localhost:8000"
        assert client.client is not None

    def test_initialize(self):
        """Test initialize method"""
        client = McpStreamableHttpClient("test_client", "http://localhost:8000")
        
        # Mock successful responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.headers = {"content-type": "application/json"}
        
        with patch.object(client.client, 'post') as mock_post:
            mock_post.return_value = mock_response
            
            # Initialize should not raise an exception
            client.initialize()

    def test_send_message_success(self):
        """Test successful message sending"""
        client = McpStreamableHttpClient("test_client", "http://localhost:8000")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.headers = {"content-type": "application/json"}
        
        with patch.object(client.client, 'post') as mock_post:
            mock_post.return_value = mock_response
            
            result = client.send_message({"test": "data"})
            
            assert result == {"result": "success"}
            mock_post.assert_called_once()

    def test_send_message_http_error(self):
        """Test HTTP error handling"""
        client = McpStreamableHttpClient("test_client", "http://localhost:8000")
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.headers = {"content-type": "application/json"}
        mock_response.is_success = False
        mock_response.reason_phrase = "Internal Server Error"
        mock_response.content = b"Internal Server Error"
        
        with patch.object(client.client, 'post') as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(ValueError, match="MCP Server response: 500"):
                client.send_message({"test": "data"})

    def test_send_message_json_error(self):
        """Test JSON parsing error handling"""
        client = McpStreamableHttpClient("test_client", "http://localhost:8000")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.headers = {"content-type": "application/json"}
        
        with patch.object(client.client, 'post') as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(Exception, match="Invalid JSON"):
                client.send_message({"test": "data"})

    def test_close(self):
        """Test client close method"""
        client = McpStreamableHttpClient("test_client", "http://localhost:8000")
        
        with patch.object(client.client, 'close') as mock_close:
            client.close()
            mock_close.assert_called_once()

    def test_initialize_with_error(self):
        """Test initialize method with error response"""
        client = McpStreamableHttpClient("test_client", "http://localhost:8000")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": {"code": -1, "message": "Init error"}}
        mock_response.headers = {"content-type": "application/json"}
        
        with patch.object(client.client, 'post') as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(Exception, match="MCP Server initialize error"):
                client.initialize()

    def test_initialize_with_notifications_error(self):
        """Test initialize method with notifications error"""
        client = McpStreamableHttpClient("test_client", "http://localhost:8000")
        
        # Mock successful initialize response
        init_response = MagicMock()
        init_response.status_code = 200
        init_response.json.return_value = {"result": "success"}
        init_response.headers = {"content-type": "application/json"}
        
        # Mock failed notifications response
        notif_response = MagicMock()
        notif_response.status_code = 200
        notif_response.json.return_value = {"error": {"code": -1, "message": "Notif error"}}
        notif_response.headers = {"content-type": "application/json"}
        
        with patch.object(client.client, 'post') as mock_post:
            mock_post.side_effect = [init_response, notif_response]
            
            with pytest.raises(Exception, match="MCP Server notifications/initialized error"):
                client.initialize()
