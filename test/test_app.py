import json
import pytest  # 添加这行
from unittest.mock import patch, MagicMock

# 测试聊天完成API
def test_chat_completions(test_client, mock_openai_client):
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

# 测试流式响应
@pytest.mark.asyncio
async def test_chat_completions_stream(test_client, mock_openai_client):
    # 模拟流式响应
    async def mock_stream():
        for i in range(3):
            # 将JSON对象先创建为变量，避免复杂的嵌套f-string
            response_data = {
                "id": "test-id",
                "object": "chat.completion.chunk",
                "created": 123456789,
                "model": "gpt-4.1-turbo-2024-04-09",
                "choices": [{"delta": {"content": f"响应部分 {i}"}, "index": 0}]
            }
            # 正确格式：在同一行内完成字符串定义
            yield 'data: ' + json.dumps(response_data) + '\n\n'
        # 正确格式：在同一行内完成字符串定义
        yield 'data: [DONE]\n\n'
    
    # 补丁流式响应方法
    mock_openai_client.chat.completions.create.return_value = MagicMock()
    mock_openai_client.chat.completions.create.return_value.__aiter__.return_value = mock_stream()
    
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
    # 修改断言，使用startswith来匹配Content-Type
    assert response.headers["Content-Type"].startswith("text/event-stream")
    
    # 验证响应内容包含数据块
    content = response.text
    assert "data: " in content
    assert "[DONE]" in content

# 测试人格列表API
def test_list_personalities(test_client):
    response = test_client.get("/v1/personalities")
    
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert isinstance(data["data"], list)

# 测试清除会话记忆API
def test_clear_conversation_memory(test_client):
    with patch('core.chat_engine.chat_engine.clear_conversation_memory') as mock_clear:
        conversation_id = "test-conversation-123"
        response = test_client.delete(f"/v1/conversations/{conversation_id}/memory")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert conversation_id in data["message"]
        mock_clear.assert_called_once_with(conversation_id)

# 测试MCP服务调用API
def test_call_mcp_service(test_client):
    with patch('core.chat_engine.chat_engine.call_mcp_service') as mock_call:
        # 设置模拟返回值
        mock_call.return_value = {"success": True, "result": {"message": "测试成功"}}
        
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
        mock_call.assert_called_once_with("test_service", "test_method", {"key": "value"})

# 测试无效请求
def test_invalid_request(test_client):
    # 缺少必填字段
    test_data = {
        "messages": [{"role": "user", "content": "你好"}]
        # 缺少model字段
    }
    
    response = test_client.post("/v1/chat/completions", json=test_data)
    
    assert response.status_code == 422  # 验证错误状态码