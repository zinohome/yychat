"""
MCP Manager tests
Covers initialization, list_tools, call_tool routing and error handling
"""
import pytest
from unittest.mock import patch, Mock

from services.mcp.manager import MCPManager
from services.mcp.exceptions import MCPServiceError, MCPServerNotFoundError, MCPToolNotFoundError


@pytest.fixture(autouse=True)
def reset_singleton():
    # Reset singleton before each test to avoid module-level initialization contamination
    MCPManager._instance = None
    yield
    MCPManager._instance = None


class TestMCPManager:
    def test_singleton_and_initialize_without_config(self):
        with patch("os.path.exists", return_value=False), \
             patch("services.mcp.manager.get_config") as mock_get_cfg:
            # no env config
            cfg = Mock()
            cfg.MCP_SERVERS_CONFIG = None
            mock_get_cfg.return_value = cfg

            manager = MCPManager()
            # Should not raise; _clients allowed to be None
            assert manager is not None
            # list_tools returns empty when no clients
            assert manager.list_tools() == []

    def test_initialize_with_file_config_success(self):
        # When config file exists and loads fine, clients should be initialized
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", create=True) as mock_open, \
             patch("json.load", return_value={"mcpServers": {}}):
            mock_open.return_value.__enter__.return_value.read.return_value = "{}"
            manager = MCPManager()
            assert manager is not None
            # Clients attribute should exist (may be None or empty dict depending on config)
            assert hasattr(manager, "_clients")

    def test_list_tools_happy_path(self):
        fake_clients = Mock()
        fake_clients.fetch_tools.return_value = [{"name": "t1"}]
        manager = MCPManager()
        manager._clients = fake_clients

        tools = manager.list_tools()
        assert tools == [{"name": "t1"}]
        fake_clients.fetch_tools.assert_called_once()

    def test_list_tools_raises_service_error(self):
        fake_clients = Mock()
        fake_clients.fetch_tools.side_effect = Exception("boom")
        manager = MCPManager()
        manager._clients = fake_clients

        with pytest.raises(MCPServiceError):
            manager.list_tools()

    def test_call_tool_auto_route_success(self):
        fake_clients = Mock()
        fake_clients._clients = {"s1": object()}
        fake_clients._tool_actions = {"toolA": object()}
        fake_clients.execute_tool.return_value = [{"text": "ok"}]

        manager = MCPManager()
        manager._clients = fake_clients

        out = manager.call_tool("toolA", {"q": 1})
        assert out == [{"text": "ok"}]
        fake_clients.execute_tool.assert_called_once_with("toolA", {"q": 1})

    def test_call_tool_with_server_success_and_prefixed(self):
        fake_clients = Mock()
        fake_clients._clients = {"srv": object()}
        # present only prefixed tool
        fake_clients._tool_actions = {"srv__toolB": object()}
        fake_clients.execute_tool.return_value = [{"text": "ok"}]

        manager = MCPManager()
        manager._clients = fake_clients

        out = manager.call_tool("toolB", {"x": 2}, mcp_server="srv")
        assert out == [{"text": "ok"}]
        fake_clients.execute_tool.assert_called_once_with("srv__toolB", {"x": 2})

    def test_call_tool_with_server_falls_back_to_raw_name(self):
        fake_clients = Mock()
        fake_clients._clients = {"srv": object()}
        fake_clients._tool_actions = {"toolC": object()}
        fake_clients.execute_tool.return_value = [{"text": "ok"}]

        manager = MCPManager()
        manager._clients = fake_clients

        out = manager.call_tool("toolC", {}, mcp_server="srv")
        assert out == [{"text": "ok"}]
        fake_clients.execute_tool.assert_called_once_with("toolC", {})

    def test_call_tool_missing_server(self):
        fake_clients = Mock()
        fake_clients._clients = {"srv": object()}
        manager = MCPManager()
        manager._clients = fake_clients

        # Implementation wraps errors in MCPServiceError
        with pytest.raises(MCPServiceError):
            manager.call_tool("toolX", {}, mcp_server="nosuch")

    def test_call_tool_missing_tool_on_server(self):
        fake_clients = Mock()
        fake_clients._clients = {"srv": object()}
        fake_clients._tool_actions = {}
        manager = MCPManager()
        manager._clients = fake_clients

        with pytest.raises(MCPToolNotFoundError):
            manager.call_tool("toolX", {}, mcp_server="srv")

    def test_call_tool_wraps_unknown_error(self):
        fake_clients = Mock()
        fake_clients.execute_tool.side_effect = Exception("unexpected")
        manager = MCPManager()
        manager._clients = fake_clients

        with pytest.raises(MCPServiceError):
            manager.call_tool("any", {})

    def test_close_swallow_errors(self):
        fake_clients = Mock()
        fake_clients.close.side_effect = Exception("fail close")
        manager = MCPManager()
        manager._clients = fake_clients
        # should not raise
        manager.close()
