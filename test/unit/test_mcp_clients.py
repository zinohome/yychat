"""
McpClients tests
Covers fetch_tools aggregation with duplicate names and execute_tool routing
"""
import pytest
from unittest.mock import patch

from services.mcp.utils.mcp_client import McpClients, ToolAction, ActionType, McpSseClient


class FakeClient:
    def __init__(self, name, tools):
        self.name = name
        self._tools = tools
        self.called = []

    def initialize(self):
        return None

    def list_tools(self):
        return self._tools

    def call_tool(self, name, arguments):
        self.called.append((name, arguments))
        return [{"text": f"{self.name}:{name}:{arguments}"}]

    def read_resource(self, uri: str):
        return [{"uri": uri, "text": "content"}]

    def get_prompt(self, name: str, arguments: dict):
        return [{"role": "system", "content": {"text": f"{name}:{arguments}"}}]


class TestMcpClients:
    def test_fetch_tools_aggregate_and_prefix(self):
        servers_config = {"s1": {"url": "http://s1"}, "s2": {"url": "http://s2"}}
        tools_s1 = [{"name": "echo"}]
        tools_s2 = [{"name": "echo"}]  # duplicate name on different server

        def fake_init(name, config):
            return FakeClient(name, tools_s1 if name == "s1" else tools_s2)

        with patch.object(McpClients, "init_client", side_effect=fake_init):
            clients = McpClients(servers_config)
            all_tools = clients.fetch_tools()
            # all_tools should contain both tool dicts without renaming
            assert all_tools == tools_s1 + tools_s2
            # internal tool actions should contain prefix for second duplicate
            # either 'echo' and 's2__echo' or 's1__echo' based on insertion order
            action_keys = set(clients._tool_actions.keys())
            assert "echo" in action_keys
            assert any(k.endswith("__echo") for k in action_keys)

    def test_execute_tool_routes_to_correct_server(self):
        servers_config = {"alpha": {"url": "http://a"}, "beta": {"url": "http://b"}}
        tools_alpha = [{"name": "do"}]
        tools_beta = [{"name": "do"}]

        def fake_init(name, config):
            return FakeClient(name, tools_alpha if name == "alpha" else tools_beta)

        with patch.object(McpClients, "init_client", side_effect=fake_init):
            clients = McpClients(servers_config)
            # Prepare tool actions via fetch
            clients.fetch_tools()
            # Prefer unprefixed first then prefixed for duplicate
            out1 = clients.execute_tool("do", {"x": 1})
            assert out1 and out1[0]["text"].startswith("alpha:")
            # Execute via prefixed name
            prefixed = [k for k in clients._tool_actions.keys() if k.endswith("__do")][0]
            out2 = clients.execute_tool(prefixed, {"y": 2})
            assert out2 and out2[0]["text"].startswith("beta:")

    def test_remove_request_params_utility(self):
        url = "http://example.com/path?x=1#frag"
        assert McpSseClient.remove_request_params(url) == "http://example.com/path"
