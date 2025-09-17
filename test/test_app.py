import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

# 模拟模型定义
class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="使用的模型名称")
    messages: list = Field(..., description="消息历史")
    temperature: float = Field(default=0.7, description="采样温度")
    max_tokens: int = Field(default=None, description="最大生成token数")
    stream: bool = Field(default=False, description="是否使用流式输出")
    user: str = Field(default=None, description="用户标识")
    conversation_id: str = Field(default=None, description="会话ID")
    personality_id: str = Field(default="professional", description="人格ID")
    use_tools: bool = Field(default=True, description="是否使用工具")

class ToolCallRequest(BaseModel):
    tool_name: str = Field(..., description="要调用的工具名称")
    params: dict = Field(default_factory=dict, description="工具参数")

class MCPServiceCallRequest(BaseModel):
    tool_name: str = Field(default=None, description="要调用的工具名称")
    mcp_server: str = Field(default=None, description="指定的MCP服务器")
    params: dict = Field(default_factory=dict, description="工具参数")
    service_name: str = Field(default=None, description="MCP服务名称")
    method_name: str = Field(default=None, description="MCP服务方法名称")

@pytest.fixture
def test_client():
    # 导入应用并创建测试客户端
    from app import app
    with TestClient(app) as client:
        yield client

@pytest.fixture
def mock_openai_client():
    with patch('openai.AsyncOpenAI') as mock_async_client:
        mock_client_instance = MagicMock()
        mock_async_client.return_value = mock_client_instance
        
        # 模拟聊天完成方法
        mock_chat = MagicMock()
        mock_client_instance.chat = mock_chat
        mock_completions = MagicMock()
        mock_chat.completions = mock_completions
        
        # 模拟create方法返回一个对象，该对象有choices属性
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "这是一个测试响应"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        # 添加usage信息
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30
        mock_response.usage = mock_usage
        
        mock_completions.create.return_value = mock_response
        
        yield mock_client_instance

@pytest.fixture
def mock_chat_engine():
    with patch('core.chat_engine.chat_engine') as mock_engine:
        # 模拟generate_response方法
        mock_generate = AsyncMock()
        mock_generate.return_value = {
            "role": "assistant",
            "content": "这是一个测试响应",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
        mock_engine.generate_response = mock_generate
        
        # 模拟call_mcp_service方法
        mock_mcp = AsyncMock()
        mock_mcp.return_value = {"success": True, "result": {"message": "测试成功"}}
        mock_engine.call_mcp_service = mock_mcp
        
        # 模拟clear_conversation_memory方法
        mock_clear = MagicMock()
        mock_engine.clear_conversation_memory = mock_clear
        
        # 模拟get_conversation_memory方法
        mock_get = MagicMock()
        mock_get.return_value = [{"role": "user", "content": "你好"}]
        mock_engine.get_conversation_memory = mock_get
        
        yield mock_engine

@pytest.fixture
def mock_personality_manager():
    with patch('core.personality_manager.PersonalityManager') as mock_manager:
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        
        # 模拟list_personalities方法
        mock_instance.list_personalities.return_value = [
            {"id": "professional", "name": "专业助手"},
            {"id": "friendly", "name": "友好伙伴"}
        ]
        
        yield mock_instance

@pytest.fixture
def mock_tool_registry():
    with patch('services.tools.registry.tool_registry') as mock_registry:
        mock_registry.list_tools.return_value = {
            "gettime": MagicMock(name="gettime", description="获取当前时间"),
            "calculator": MagicMock(name="calculator", description="计算器工具")
        }
        yield mock_registry

@pytest.fixture
def mock_mcp_manager():
    with patch('services.mcp.manager.mcp_manager') as mock_manager:
        mock_manager.list_tools.return_value = [
            {"name": "weather", "description": "天气服务"},
            {"name": "news", "description": "新闻服务"}
        ]
        yield mock_manager

@pytest.fixture
def mock_tool_manager():
    with patch('services.tools.manager.ToolManager') as mock_manager:
        mock_instance = AsyncMock()
        mock_manager.return_value = mock_instance
        mock_instance.execute_tool.return_value = {"result": "工具执行成功"}
        yield mock_instance

# 测试聊天完成API
def test_chat_completions(test_client, mock_chat_engine):
    # 准备测试数据
    test_data = {
        "model": "gpt-4.1-turbo-2024-04-09",
        "messages": [
            {"role": "system", "content": "你是一个助手"},
            {"role": "user", "content": "你好，世界！"}
        ],
        "temperature": 0.7,
        "personality_id": "professional",
        "use_tools": False
    }
    
    # 发送请求
    response = test_client.post("/v1/chat/completions", json=test_data)
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"
    assert len(data["choices"]) == 1
    assert "message" in data["choices"][0]
    assert "content" in data["choices"][0]["message"]
    assert "usage" in data
    
    # 验证调用参数
    conversation_id = test_data.get("conversation_id") or test_data.get("user")
    mock_chat_engine.generate_response.assert_called_once_with(
        test_data["messages"],
        conversation_id,
        test_data["personality_id"],
        test_data["use_tools"],
        stream=False
    )

# 测试流式响应
@pytest.mark.asyncio
async def test_chat_completions_stream(test_client, mock_chat_engine):
    # 模拟流式响应生成器
    async def mock_stream_generator():
        for i in range(3):
            yield {
                "content": f"响应部分 {i}",
                "finish_reason": None,
                "stream": True
            }
        # 发送结束标志
        yield {
            "content": "",
            "finish_reason": "stop",
            "stream": True
        }
    
    # 设置模拟返回值
    mock_chat_engine.generate_response.return_value = mock_stream_generator()
    
    # 准备测试数据
    test_data = {
        "model": "gpt-4.1-turbo-2024-04-09",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": True,
        "use_tools": False
    }
    
    # 发送请求
    response = test_client.post("/v1/chat/completions", json=test_data)
    
    # 验证响应
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/event-stream")
    
    # 验证响应内容包含数据块
    content = response.text
    assert "data: " in content
    assert "响应部分" in content
    assert "[DONE]" in content
    
    # 验证调用参数
    conversation_id = test_data.get("conversation_id") or test_data.get("user")
    mock_chat_engine.generate_response.assert_called_once_with(
        test_data["messages"],
        conversation_id,
        test_data["personality_id"],  # 这里会使用默认值
        test_data["use_tools"],
        stream=True
    )

# 测试人格列表API
def test_list_personalities(test_client, mock_personality_manager):
    response = test_client.get("/v1/personalities")
    
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 2
    assert {"id": "professional", "name": "专业助手"} in data["data"]
    assert {"id": "friendly", "name": "友好伙伴"} in data["data"]

# 测试清除会话记忆API
def test_clear_conversation_memory(test_client, mock_chat_engine):
    conversation_id = "test-conversation-123"
    response = test_client.delete(f"/v1/conversations/{conversation_id}/memory")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert conversation_id in data["message"]
    mock_chat_engine.clear_conversation_memory.assert_called_once_with(conversation_id)

# 测试获取会话记忆API
def test_get_conversation_memory(test_client, mock_chat_engine):
    conversation_id = "test-conversation-123"
    response = test_client.get(f"/v1/conversations/{conversation_id}/memory")
    
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 1
    assert data["total"] == 1
    mock_chat_engine.get_conversation_memory.assert_called_once_with(conversation_id)

# 测试MCP服务调用API
def test_call_mcp_service(test_client, mock_chat_engine):
    # 准备测试数据
    test_data = {
        "service_name": "test_service",
        "method_name": "test_method",
        "params": {"key": "value"}
    }
    
    # 发送请求
    response = test_client.post("/v1/mcp/call", json=test_data)
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["result"]["message"] == "测试成功"
    
    # 验证调用参数
    mock_chat_engine.call_mcp_service.assert_called_once_with(
        tool_name=None,
        params=test_data["params"],
        service_name=test_data["service_name"],
        method_name=test_data["method_name"],
        mcp_server=None
    )

# 测试直接使用tool_name调用MCP服务
def test_call_mcp_service_with_tool_name(test_client, mock_chat_engine):
    # 准备测试数据
    test_data = {
        "tool_name": "test_service__test_method",
        "params": {"key": "value"},
        "mcp_server": "test_server"
    }
    
    # 发送请求
    response = test_client.post("/v1/mcp/call", json=test_data)
    
    # 验证响应
    assert response.status_code == 200
    
    # 验证调用参数
    mock_chat_engine.call_mcp_service.assert_called_once_with(
        tool_name=test_data["tool_name"],
        params=test_data["params"],
        service_name=None,
        method_name=None,
        mcp_server=test_data["mcp_server"]
    )

# 测试MCP服务调用错误处理
def test_call_mcp_service_error(test_client, mock_chat_engine):
    # 设置模拟返回错误
    mock_chat_engine.call_mcp_service.return_value = {"success": False, "error": "测试错误"}
    
    # 准备测试数据
    test_data = {
        "service_name": "test_service",
        "method_name": "test_method",
        "params": {"key": "value"}
    }
    
    # 发送请求
    response = test_client.post("/v1/mcp/call", json=test_data)
    
    # 验证响应
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["message"] == "测试错误"

# 测试列出非MCP工具
def test_list_tools(test_client, mock_tool_registry, mock_mcp_manager):
    response = test_client.get("/v1/tools")
    
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert isinstance(data["tools"], list)
    assert len(data["tools"]) == 2
    assert {"name": "gettime", "description": "获取当前时间"} in data["tools"]
    assert {"name": "calculator", "description": "计算器工具"} in data["tools"]

# 测试列出MCP工具
def test_list_mcp_tools(test_client, mock_mcp_manager):
    response = test_client.get("/v1/mcp/tools")
    
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert isinstance(data["tools"], list)
    assert len(data["tools"]) == 2
    assert {"name": "weather", "description": "天气服务"} in data["tools"]
    assert {"name": "news", "description": "新闻服务"} in data["tools"]

# 测试调用非MCP工具
def test_call_tool(test_client, mock_tool_manager):
    # 准备测试数据
    test_data = {
        "tool_name": "gettime",
        "params": {"format": "%Y-%m-%d"}
    }
    
    # 发送请求
    response = test_client.post("/v1/tools/call", json=test_data)
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["result"] == {"result": "工具执行成功"}
    
    # 验证调用参数
    mock_tool_manager.execute_tool.assert_called_once_with(
        test_data["tool_name"],
        test_data["params"]
    )

# 测试无效请求
def test_invalid_request(test_client):
    # 缺少必填字段
    test_data = {
        "messages": [{"role": "user", "content": "你好"}]
        # 缺少model字段
    }
    
    response = test_client.post("/v1/chat/completions", json=test_data)
    
    assert response.status_code == 422  # 验证错误状态码

# 测试根路径API
def test_root_path(test_client):
    response = test_client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to the OpenAI compatible Chat API"
    assert data["version"] == "1.0.0"
    assert "/v1/chat/completions" in data["api_endpoints"]

# 测试模型列表API
def test_list_models(test_client):
    response = test_client.get("/v1/models")
    
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1
    assert "id" in data["data"][0]

# 测试获取模型详情API
def test_get_model(test_client):
    # 先获取模型列表中的第一个模型ID
    list_response = test_client.get("/v1/models")
    model_id = list_response.json()["data"][0]["id"]
    
    # 获取该模型的详情
    response = test_client.get(f"/v1/models/{model_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == model_id
    
    # 测试获取不存在的模型
    response = test_client.get("/v1/models/non-existent-model")
    assert response.status_code == 404