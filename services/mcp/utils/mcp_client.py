import json
from utils.log import log
import re
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from threading import Event, Thread
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from httpx_sse import connect_sse, EventSource
from pydantic import BaseModel

class McpClient(ABC):
    """Interface for MCP client."""

    def __init__(self, name: str, url: str,
                 headers: dict[str, Any] | None = None,
                 timeout: float = 50,
                 ):
        self.name = name
        self.url = url
        self.headers = headers
        self.timeout = timeout
        self.id_counter = 0

    def _get_next_id(self):
        self.id_counter += 1
        return self.id_counter

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def initialize(self):
        raise NotImplementedError

    @abstractmethod
    def send_message(self, data: dict) -> dict:
        raise NotImplementedError

    def list_tools(self) -> list[dict]:
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/list",
            "params": {}
        }
        response = self.send_message(request)
        if "error" in response:
            error = response["error"]
            # -32001: Unsupported method
            # -32601: Method not found
            if error["code"] in {-32001, -32601}:
                return []
            raise Exception(f"{self.name} - MCP Server tools/list error: {error}")
        tools = response.get("result", {}).get("tools", [])
        #log.debug(f"{self.name} - MCP Server tools/list: {tools}")
        return tools

    def call_tool(self, name: str, arguments: dict) -> list[dict]:
        data = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        response = self.send_message(data)
        if "error" in response:
            error = response["error"]
            raise Exception(f"{self.name} - MCP Server tools/call error: {error}")
        content = response.get("result", {}).get("content", [])
        log.debug(f"{self.name} - MCP Server tools/call: {content}")
        return content

    def list_resources(self) -> list[dict]:
        data = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "resources/list",
            "params": {}
        }
        response = self.send_message(data)
        if "error" in response:
            error = response["error"]
            # -32001: Unsupported method
            # -32601: Method not found
            if error["code"] in {-32001, -32601}:
                return []
            raise Exception(f"{self.name} - MCP Server resources/list error: {error}")
        resources = response.get("result", {}).get("resources", [])
        log.debug(f"{self.name} - MCP Server resources/list: {resources}")
        return resources

    def read_resource(self, uri: str) -> list[dict]:
        data = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "resources/read",
            "params": {
                "uri": uri
            }
        }
        response = self.send_message(data)
        if "error" in response:
            error = response["error"]
            raise Exception(f"{self.name} - MCP Server resources/read error: {error}")
        contents = response.get("result", {}).get("contents", [])
        log.debug(f"{self.name} - MCP Server resources/read: {contents}")
        return contents

    def list_resources_templates(self) -> list[dict]:
        data = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "resources/templates/list"
        }
        response = self.send_message(data)
        if "error" in response:
            error = response["error"]
            # -32001: Unsupported method
            # -32601: Method not found
            if error["code"] in {-32001, -32601}:
                return []
            raise Exception(f"{self.name} - MCP Server resources/templates/list error: {error}")
        resources = response.get("result", {}).get("resourceTemplates", [])
        log.debug(f"{self.name} - MCP Server resources/templates/list: {resources}")
        return resources

    def list_prompts(self) -> list[dict]:
        data = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "prompts/list",
            "params": {}
        }
        response = self.send_message(data)
        if "error" in response:
            error = response["error"]
            # -32001: Unsupported method
            # -32601: Method not found
            if error["code"] in {-32001, -32601}:
                return []
            raise Exception(f"{self.name} - MCP Server prompts/list error: {error}")
        prompts = response.get("result", {}).get("prompts", [])
        log.debug(f"{self.name} - MCP Server prompts/list: {prompts}")
        return prompts

    def get_prompt(self, name: str, arguments: dict) -> list[dict]:
        data = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "prompts/get",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        response = self.send_message(data)
        if "error" in response:
            error = response["error"]
            raise Exception(f"{self.name} - MCP Server prompts/get error: {error}")
        messages = response.get("result", {}).get("messages", [])
        log.debug(f"{self.name} - MCP Server prompts/get: {messages}")
        return messages


class McpSseClient(McpClient):
    """
    HTTP with SSE transport MCP client.
    """

    def __init__(self, name: str, url: str,
                 headers: dict[str, Any] | None = None,
                 timeout: float = 50,
                 sse_read_timeout: float = 50,
                 ):
        super().__init__(name, url, headers, timeout)
        self.sse_read_timeout = sse_read_timeout
        self.endpoint_url = None
        self.message_url = None
        self.client = httpx.Client(headers=headers, timeout=httpx.Timeout(timeout, read=sse_read_timeout))
        self.message_dict = {}
        self.response_ready = Event()
        self.should_stop = Event()
        self._listen_thread = None
        self._connected = Event()
        self._error_event = Event()
        self._thread_exception = None
        self.connect()

    @staticmethod
    def remove_request_params(url: str) -> str:
        return urljoin(url, urlparse(url).path)

    def _listen_messages(self) -> None:
        try:
            log.debug(f"{self.name} - Connecting to SSE endpoint: {self.remove_request_params(self.url)}")
            with connect_sse(
                    client=self.client,
                    method="GET",
                    url=self.url,
                    timeout=httpx.Timeout(self.timeout, read=self.sse_read_timeout),
                    follow_redirects=True,
            ) as event_source:
                event_source.response.raise_for_status()
                log.debug(f"{self.name} - SSE connection established")
                for sse in event_source.iter_sse():
                    log.debug(f"{self.name} - Received SSE event: {sse.event}")
                    if self.should_stop.is_set():
                        break
                    match sse.event:
                        case "endpoint":
                            # 固定为使用 mcp.json 的主机名 + /mcp/message，不接受带 sessionId 的端点
                            base = f"{urlparse(self.url).scheme}://{urlparse(self.url).netloc}"
                            self.message_url = urljoin(base + '/', 'mcp/message')
                            log.debug(f"{self.name} - Using fixed message URL: {self.message_url}")
                            self._connected.set()
                        case "message":
                            message = json.loads(sse.data)
                            #log.debug(f"{self.name} - Received server message: {message}")
                            self.message_dict[message["id"]] = message
                            self.response_ready.set()
                        case _:
                            log.warning(f"{self.name} - Unknown SSE event: {sse.event}")
        except Exception as e:
            self._thread_exception = e
            self._error_event.set()
            self._connected.set()

    def send_message(self, data: dict) -> dict:
        if not (self.message_url or self.endpoint_url):
            if self._thread_exception:
                raise ConnectionError(f"{self.name} - MCP Server connection failed: {self._thread_exception}")
            else:
                raise RuntimeError(f"{self.name} - Please call connect() first")
        log.debug(f"{self.name} - Sending client message: {data}")
        response = self.client.post(
            url=(self.message_url or self.endpoint_url),
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
        )
        response.raise_for_status()
        log.debug(f"response status: {response.status_code} {response.reason_phrase}")
        if not response.is_success:
            raise ValueError(
                f"{self.name} - MCP Server response: {response.status_code} {response.reason_phrase} ({response.content})")
        if "id" in data:
            message_id = data["id"]
            while True:
                self.response_ready.wait()
                self.response_ready.clear()
                if message_id in self.message_dict:
                    #log.debug(f"message_id: {message_id}")
                    message = self.message_dict.pop(message_id, None)
                    #log.debug(f"message: {message}")
                    if message and message.get("method") == "ping":
                        continue
                    return message
        return {}

    def connect(self) -> None:
        self._listen_thread = Thread(target=self._listen_messages, daemon=True)
        self._listen_thread.start()
        while True:
            if self._error_event.is_set():
                if isinstance(self._thread_exception, httpx.HTTPStatusError):
                    raise ConnectionError(f"{self.name} - MCP Server connection failed: {self._thread_exception}") \
                        from self._thread_exception
                else:
                    raise self._thread_exception
            if self._connected.wait(timeout=0.1):
                break
            if not self._listen_thread.is_alive():
                raise ConnectionError(f"{self.name} - MCP Server SSE listener thread died unexpectedly!")

    def close(self) -> None:
        try:
            self.should_stop.set()
            self.client.close()
            if self._listen_thread and self._listen_thread.is_alive():
                self._listen_thread.join(timeout=10)
        except Exception as e:
            raise Exception(f"{self.name} - MCP Server connection close failed: {str(e)}")

    def initialize(self):
        init_data = {
            "jsonrpc": "2.0",
            "id": uuid.uuid4().hex,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "MCP HTTP with SSE Client",
                    "version": "1.0.0"
                }
            }
        }
        response = self.send_message(init_data)
        if "error" in response:
            raise Exception(f"MCP Server initialize error: {response['error']}")
        notify_data = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        notify_response = self.send_message(notify_data)
        if "error" in notify_response:
            raise Exception(f"MCP Server notifications/initialized error: {notify_response['error']}")


class McpStreamableHttpClient(McpClient):
    """
    Streamable HTTP transport MCP client.
    """

    def __init__(self, name: str, url: str,
                 headers: dict[str, Any] | None = None,
                 timeout: float = 50,
                 ):
        super().__init__(name, url, headers, timeout)
        self.client = httpx.Client(headers=headers, timeout=httpx.Timeout(timeout))
        self.session_id = None

    def close(self) -> None:
        try:
            self.client.close()
        except Exception as e:
            raise Exception(f"{self.name} - MCP Server connection close failed: {str(e)}")

    def send_message(self, data: dict) -> dict:
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        log.debug(f"{self.name} - Sending client message: {data}")
        response = self.client.post(
            url=self.url,
            json=data,
            headers=headers,
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
        )
        log.debug(f"response status: {response.status_code} {response.reason_phrase}")
        if not response.is_success:
            raise ValueError(
                f"{self.name} - MCP Server response: {response.status_code} {response.reason_phrase} ({response.content})")
        log.debug(f"response headers: {response.headers}")
        if "mcp-session-id" in response.headers:
            self.session_id = response.headers.get("mcp-session-id")
        log.debug(f"response content: {response.content}")
        if not response.content:
            return {}
        message = {}
        content_type = response.headers.get("content-type", "None")
        if "text/event-stream" in content_type:
            for sse in EventSource(response).iter_sse():
                if sse.event != "message":
                    raise Exception(f"{self.name} - Unknown Server-Sent Event: {sse.event}")
                message = json.loads(sse.data)
        elif "application/json" in content_type:
            message = (response.json() if response.content else None) or {}
        else:
            raise Exception(f"{self.name} - Unsupported Content-Type: {content_type}")
        log.debug(f"message: {message}")
        return message

    def initialize(self):
        init_data = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "MCP Streamable HTTP Client",
                    "version": "1.0.0"
                }
            }
        }
        response = self.send_message(init_data)
        if "error" in response:
            raise Exception(f"MCP Server initialize error: {response['error']}")
        notify_data = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        notify_response = self.send_message(notify_data)
        if "error" in notify_response:
            raise Exception(f"MCP Server notifications/initialized error: {notify_response['error']}")


class ActionType(Enum):
    TOOL = "tool"
    RESOURCE = "resource"
    RESOURCE_TEMPLATE = "resource_template"
    PROMPT = "prompt"


class ToolAction(BaseModel):
    tool_name: str
    server_name: str
    action_type: ActionType
    action_feature: dict


class McpClients:
    def __init__(self, servers_config: dict[str, Any],
                 resources_as_tools: bool = False,
                 prompts_as_tools: bool = False):
        if "mcpServers" in servers_config:
            servers_config = servers_config["mcpServers"]
        self._clients = {
            name: self.init_client(name, config)
            for name, config in servers_config.items()
        }
        for client in self._clients.values():
            client.initialize()
        self._resources_as_tools = resources_as_tools
        self._prompts_as_tools = prompts_as_tools
        self._tool_actions: dict[str, ToolAction] = {}

    @staticmethod
    def init_client(name: str, config: dict[str, Any]) -> McpClient:
        if not re.fullmatch(r'^[a-zA-Z0-9_-]+$', name):
            raise Exception(f"Invalid server name '{name}': string does not match pattern. "
                            f"Expected a string that matches the pattern '^[a-zA-Z0-9_-]+$'.")
        transport = "sse"
        if "transport" in config:
            transport = config["transport"]
        if transport == "streamable_http":
            return McpStreamableHttpClient(
                name=name,
                url=config.get("url"),
                headers=config.get("headers", None),
                timeout=config.get("timeout", 50),
            )
        return McpSseClient(
            name=name,
            url=config.get("url"),
            headers=config.get("headers", None),
            timeout=config.get("timeout", 50),
            sse_read_timeout=config.get("sse_read_timeout", 50),
        )

    def fetch_tools(self) -> list[dict]:
        try:
            all_tools = []
            for server_name, client in self._clients.items():
                # tools list
                tools = client.list_tools()
                for tool in tools:
                    name = tool["name"]
                    # 存储工具操作时仍然需要处理重复名称，但不修改工具本身的名称
                    registered_name = name
                    if name in self._tool_actions:
                        registered_name = f"{server_name}__{name}"
                    
                    self._tool_actions[registered_name] = ToolAction(
                        tool_name=name,  # 保存原始工具名
                        server_name=server_name,
                        action_type=ActionType.TOOL,
                        action_feature=tool,
                    )
                    # 不修改原始工具名，直接添加到all_tools
                    all_tools.append(tool)
                
                # 其余代码保持不变...
            
            #log.debug(f"Fetching tools: {all_tools}")
            return all_tools
        except Exception as e:
            raise Exception(f"Error fetching tools: {str(e)}")

    def execute_tool(self, tool_name: str, tool_args: dict[str, Any]) -> list[dict]:
        if not self._tool_actions:
            self.fetch_tools()
        if tool_name not in self._tool_actions:
            raise Exception(f"There is not a tool named {tool_name!r}")
        tool_action = self._tool_actions[tool_name]
        server_name = tool_action.server_name
        log.debug(f"Executing tool! server name: {server_name}, tool name: {tool_name}, tool arguments: {tool_args}")
        if server_name not in self._clients:
            raise Exception(f"There is not a MCP Server named {server_name!r}")
        client = self._clients[server_name]
        action_type = tool_action.action_type
        try:
            tool_contents = []
            if action_type == ActionType.TOOL:
                tool_contents = client.call_tool(tool_name, tool_args)
            elif action_type in [ActionType.RESOURCE, ActionType.RESOURCE_TEMPLATE]:
                if action_type == ActionType.RESOURCE:
                    resource = tool_action.action_feature
                    uri = resource["uri"]
                else:
                    uri = tool_args["uri"]
                contents = client.read_resource(uri)
                for content in contents:
                    if "text" in content:
                        tool_contents.append({
                            "type": "resource",
                            "resource": {
                                "uri": content["uri"],
                                "mimeType": content.get("mimeType", "text/plain"),
                                "text": content["text"]
                            }
                        })
                    elif "blob" in content:
                        tool_contents.append({
                            "type": "resource",
                            "resource": {
                                "uri": content["uri"],
                                "mimeType": content.get("mimeType", None),
                                "blob": content["blob"]
                            }
                        })
                    else:
                        raise Exception(f"Unsupported resource: {content}")
            elif action_type == ActionType.PROMPT:
                prompt = tool_action.action_feature
                messages = client.get_prompt(prompt["name"], tool_args)
                text = ""
                for message in messages:
                    role = message["role"]
                    content = message["content"]
                    content_text = content.get("text", str(content))
                    text += f"{role}: {content_text}\n"
                tool_contents.append({
                    "type": "text",
                    "text": text.strip()
                })
            else:
                raise Exception(f"Unsupported Action type: {action_type}")
            log.debug(f"Executing tool: {tool_contents}")
            return tool_contents
        except Exception as e:
            raise Exception(f"Error executing tool: {str(e)}")

    def close(self) -> None:
        for client in self._clients.values():
            try:
                client.close()
            except Exception as e:
                log.error(e)
