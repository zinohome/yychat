# YYChat API 使用指南

## 一、产品简介

YYChat是一个基于OpenAI API的聊天机器人服务，提供兼容OpenAI接口的聊天完成功能，同时增加了会话记忆管理、人格定制和工具调用等增强特性。本指南详细介绍如何调用YYChat API进行开发。

## 二、认证说明

### 2.1 认证方式

YYChat API采用Bearer令牌认证机制，兼容OpenAI的认证格式。

### 2.2 请求头设置

所有API请求（除根路径外）必须包含以下认证头：

```http
Authorization: Bearer <your_api_key>
```

### 2.3 API密钥获取

API密钥配置在服务器端的环境变量`YYCHAT_API_KEY`中，请联系系统管理员获取。

### 2.4 认证失败响应

认证失败时，API将返回与OpenAI格式一致的错误信息，状态码为401：

```json
{
  "error": {
    "message": "Incorrect API key provided",
    "type": "invalid_request_error",
    "param": null,
    "code": "invalid_api_key"
  }
}
```

## 三、核心API调用

### 3.1 聊天完成API

**端点**: `POST /v1/chat/completions`

**功能**: 生成聊天响应，支持流式输出和上下文管理。

**请求参数**: 

```json
{
  "model": "gpt-3.5-turbo",  // 使用的模型名称
  "messages": [              // 消息历史，必需参数
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  // 可选参数
  "temperature": 0.7,        // 采样温度，默认0.7
  "max_tokens": null,        // 最大生成token数
  "top_p": 1.0,              // 核采样，默认1.0
  "n": 1,                    // 生成的响应数量，默认1
  "stream": false,           // 是否使用流式输出，默认false
  "stop": null,              // 停止词
  "presence_penalty": 0.0,   // 存在惩罚，默认0.0
  "frequency_penalty": 0.0,  // 频率惩罚，默认0.0
  "logit_bias": null,        // logit偏置
  "user": "user_123",       // 用户标识
  
  // YYChat特有参数
  "conversation_id": "conv_123", // 会话ID，用于上下文管理
  "personality_id": "friendly",  // 人格ID
  "use_tools": true               // 是否使用工具，默认true
}
```

**会话管理规则**: 
- `conversation_id`是维护会话上下文的关键标识
- 如果未提供`conversation_id`，系统会尝试使用`user`字段作为会话标识
- 如果两者都未提供，将使用默认值`"default_conversation"`
- 相同`conversation_id`的请求会共享上下文记忆

**响应格式**:

非流式响应（`stream=false`）:
```json
{
  "id": "chatcmpl-conv_123",
  "object": "chat.completion",
  "created": 1677664795,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 15,
    "total_tokens": 35
  }
}
```

流式响应（`stream=true`）:

返回Server-Sent Events (SSE)格式，每行以`data: `开头，包含部分响应内容。当收到`data: [DONE]`时表示响应结束。

### 3.2 流式响应处理示例

以下是处理流式响应的客户端代码示例（Python）：

```python
import requests
import json

url = "http://localhost:8000/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
}

payload = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Write a short story"}],
    "stream": True,
    "conversation_id": "test_conv"
}

response = requests.post(url, headers=headers, json=payload, stream=True)

for chunk in response.iter_lines():
    if chunk:
        # 去除data:前缀
        data = chunk.decode("utf-8").replace("data: ", "")
        if data == "[DONE]":
            break
        try:
            # 解析JSON数据
            json_data = json.loads(data)
            # 提取并打印内容
            if "choices" in json_data:
                delta = json_data["choices"][0].get("delta", {})
                if "content" in delta:
                    print(delta["content"], end="", flush=True)
        except json.JSONDecodeError:
            continue
```

## 四、会话记忆管理

YYChat提供了会话记忆管理API，方便开发者查看和清除会话历史。

### 4.1 清除会话记忆

**端点**: `DELETE /v1/conversations/{conversation_id}/memory`

**功能**: 清除指定会话的所有记忆。

**响应**: 
```json
{
  "success": true,
  "message": "Memory for conversation conv_123 cleared"
}
```

### 4.2 获取会话记忆

**端点**: `GET /v1/conversations/{conversation_id}/memory`

**功能**: 获取指定会话的记忆列表。

**响应**: 
```json
{
  "object": "list",
  "data": [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hello! How can I help you today?"}
  ],
  "total": 2
}
```

### 4.3 验证会话记忆

**端点**: `GET /api/verify-memory/{conversation_id}`

**功能**: 验证指定会话ID的记忆是否存在，并返回部分记忆内容。

**响应**: 
```json
{
  "success": true,
  "conversation_id": "conv_123",
  "memory_count": 2,
  "memories": [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hello! How can I help you today?"}
  ]
}
```

## 五、工具调用

YYChat支持两种类型的工具调用：本地工具和MCP服务工具。

### 5.1 本地工具调用

**端点**: `POST /v1/tools/call`

**功能**: 调用服务器本地注册的工具。

**请求参数**: 
```json
{
  "tool_name": "weather_tool",
  "params": {"location": "Beijing", "date": "2023-01-01"}
}
```

**响应**: 
```json
{
  "success": true,
  "result": {"temperature": "10°C", "condition": "Sunny"}
}
```

### 5.2 MCP服务调用

**端点**: `POST /v1/mcp/call`

**功能**: 调用MCP（微服务编排平台）上的服务。

**请求参数**: 
```json
{
  "tool_name": "weather_service",
  "mcp_server": "mcp.example.com", // 可选，指定MCP服务器
  "params": {"location": "Beijing", "date": "2023-01-01"}
}
```

**替代参数格式**（向后兼容）: 
```json
{
  "service_name": "weather",
  "method_name": "get_weather",
  "params": {"location": "Beijing", "date": "2023-01-01"}
}
```

## 六、工具列表查询

### 6.1 列出本地工具

**端点**: `GET /v1/tools`

**功能**: 列出所有已注册的非MCP工具。

**响应**: 
```json
{
  "tools": [
    {
      "name": "weather_tool",
      "description": "获取指定地点的天气信息"
    },
    {
      "name": "calculator",
      "description": "执行数学计算"
    }
  ]
}
```

### 6.2 列出MCP工具

**端点**: `GET /v1/mcp/tools`

**功能**: 列出所有已注册的MCP工具。

**响应**: 
```json
{
  "tools": [
    {
      "name": "weather_service",
      "description": "MCP天气服务"
    },
    {
      "name": "news_service",
      "description": "MCP新闻服务"
    }
  ]
}
```

## 七、模型和人格管理

### 7.1 模型管理

**列出可用模型**: `GET /v1/models`

**响应**: 
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-3.5-turbo",
      "object": "model",
      "created": 1677610602,
      "owned_by": "openai"
    }
  ]
}
```

**获取模型详情**: `GET /v1/models/{model_id}`

**响应**: 
```json
{
  "id": "gpt-3.5-turbo",
  "object": "model",
  "created": 1677610602,
  "owned_by": "openai"
}
```

### 7.2 人格管理

**列出可用人格**: `GET /v1/personalities`

**响应**: 
```json
{
  "object": "list",
  "data": [
    {"id": "friendly", "name": "友好助手"},
    {"id": "professional", "name": "专业顾问"},
    {"id": "health_assistant", "name": "健康助手"}
  ]
}
```

## 八、API参考信息

**根路径信息**: `GET /`

无需认证，返回API版本和可用端点信息。

**响应**: 
```json
{
  "message": "Welcome to the YYChat OpenAI Compatible API",
  "version": "0.1.1",
  "api_endpoints": ["/v1/chat/completions", "/v1/models", "/v1/personalities"]
}
```

## 九、错误处理

YYChat API的错误响应遵循统一格式，包含以下字段：
- `message`: 错误描述
- `type`: 错误类型
- `param`: 相关参数
- `code`: 错误代码

常见错误类型：
- `invalid_request_error`: 请求参数无效
- `invalid_api_key`: API密钥错误
- `server_error`: 服务器内部错误
- `validation_error`: 请求验证失败
- `mcp_service_error`: MCP服务调用错误

## 十、示例代码

### 10.1 Python调用示例

```python
import requests
import json

# 配置
url = "http://localhost:8000/v1/chat/completions"
api_key = "YOUR_API_KEY"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# 聊天请求
payload = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "user", "content": "解释量子计算的基本原理"}
    ],
    "conversation_id": "test_user_123",
    "personality_id": "professional",
    "use_tools": True
}

# 发送请求
response = requests.post(url, headers=headers, json=payload)

# 处理响应
if response.status_code == 200:
    data = response.json()
    print("响应内容:", data["choices"][0]["message"]["content"])
else:
    print(f"请求失败: {response.status_code}")
    print(response.json())
```

### 10.2 cURL命令示例

```bash
# 基本聊天请求
echo '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"Hello!"}],"conversation_id":"test_conv"}' | \
curl -X POST http://localhost:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-H "Authorization: Bearer YOUR_API_KEY" \
-d @-

# 流式响应请求
echo '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"Hello!"}],"stream":true}' | \
curl -X POST http://localhost:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-H "Authorization: Bearer YOUR_API_KEY" \
-d @- \
-N
```

## 十一、交互式文档

YYChat API提供了基于FastAPI的交互式文档：

1. 访问 `http://服务器地址:端口/docs`
2. 点击右上角"Authorize"按钮
3. 在弹出窗口中输入API密钥（仅需输入密钥值，不需要Bearer前缀）
4. 点击"Authorize"完成认证后即可在文档中直接测试API

## 十二、注意事项

1. **API密钥安全**: 请妥善保管您的API密钥，不要在客户端代码或公开场合暴露
2. **会话管理**: 建议为每个用户会话使用唯一的`conversation_id`
3. **默认参数**: 大多数参数都有合理的默认值，使用时可仅指定必需参数
4. **工具使用**: 默认情况下`use_tools`为`true`，如需禁用工具请明确设置为`false`
5. **响应处理**: 流式响应和非流式响应的处理方式不同，请根据实际需求选择

---

**版本**: 0.1.1
**更新时间**: 2023-10-01
**适用对象**: YYChat API 用户