# YYChat API 规范文档

## 概述

YYChat 是一个基于 OpenAI API 的聊天机器人服务，提供与 OpenAI Chat Completions API 兼容的接口，并集成了记忆管理、工具调用、性能监控等功能。

### 基本信息

- **API 版本**: v1
- **基础 URL**: `http://localhost:8000` (默认)
- **认证方式**: Bearer Token (API Key)
- **内容类型**: `application/json`
- **字符编码**: UTF-8

## 认证

所有 API 请求都需要在请求头中包含有效的 API Key：

```http
Authorization: Bearer YOUR_API_KEY
```

默认 API Key 可通过环境变量 `YYCHAT_API_KEY` 配置。

## 核心 API 端点

### 1. 聊天完成 (Chat Completions)

#### POST `/v1/chat/completions`

创建聊天完成请求，支持流式和非流式响应。

**请求参数**:

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `model` | string | 否 | 配置值 | 使用的模型名称 |
| `messages` | array | 是 | - | 消息历史数组 |
| `temperature` | float | 否 | 0.7 | 采样温度 (0-2) |
| `max_tokens` | integer | 否 | null | 最大生成 token 数 |
| `top_p` | float | 否 | 1.0 | 核采样 (0-1) |
| `n` | integer | 否 | 1 | 生成的响应数量 |
| `stream` | boolean | 否 | false | 是否使用流式输出 |
| `stop` | string/array | 否 | null | 停止词 |
| `presence_penalty` | float | 否 | 0.0 | 存在惩罚 (-2-2) |
| `frequency_penalty` | float | 否 | 0.0 | 频率惩罚 (-2-2) |
| `logit_bias` | object | 否 | null | logit 偏置 |
| `user` | string | 否 | null | 用户标识 |
| `conversation_id` | string | 否 | null | 会话 ID |
| `personality_id` | string | 否 | null | 人格 ID |
| `use_tools` | boolean | 否 | true | 是否使用工具 |

**消息格式**:
```json
{
  "role": "user|assistant|system",
  "content": "消息内容"
}
```

**请求示例**:
```json
{
  "model": "gpt-4.1",
  "messages": [
    {
      "role": "system",
      "content": "你是一个有用的助手。"
    },
    {
      "role": "user",
      "content": "你好，请介绍一下自己。"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false,
  "conversation_id": "user_123",
  "personality_id": "health_assistant",
  "use_tools": true
}
```

**响应格式**:

**非流式响应**:
```json
{
  "id": "chatcmpl-user_123",
  "object": "chat.completion",
  "created": 1699123456,
  "model": "gpt-4.1",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！我是一个AI助手..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 50,
    "total_tokens": 70
  }
}
```

**流式响应**:
```
data: {"id": "chatcmpl-user_123", "object": "chat.completion.chunk", "created": 1699123456, "model": "gpt-4.1", "choices": [{"index": 0, "delta": {"content": "你好"}, "finish_reason": null}]}

data: {"id": "chatcmpl-user_123", "object": "chat.completion.chunk", "created": 1699123456, "model": "gpt-4.1", "choices": [{"index": 0, "delta": {"content": "！"}, "finish_reason": null}]}

data: [DONE]
```

### 2. 模型管理

#### GET `/v1/models`

获取可用模型列表。

**响应示例**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4.1",
      "object": "model",
      "created": 1699123456,
      "owned_by": "openai"
    }
  ]
}
```

#### GET `/v1/models/{model_id}`

获取指定模型的详细信息。

**路径参数**:
- `model_id`: 模型 ID

**响应示例**:
```json
{
  "id": "gpt-4.1",
  "object": "model",
  "created": 1699123456,
  "owned_by": "openai"
}
```

### 3. 人格管理

#### GET `/v1/personalities`

获取可用的人格列表。

**响应示例**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "health_assistant",
      "name": "健康助手",
      "description": "专业的健康咨询助手"
    }
  ]
}
```

## 服务管理 API

### 4. 会话记忆管理

#### GET `/v1/conversations/{conversation_id}/memory`

获取指定会话的记忆。

**路径参数**:
- `conversation_id`: 会话 ID

**响应示例**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "mem_123",
      "content": "用户喜欢喝咖啡",
      "created_at": "2023-11-05T10:00:00Z"
    }
  ],
  "total": 1
}
```

#### DELETE `/v1/conversations/{conversation_id}/memory`

清除指定会话的记忆。

**响应示例**:
```json
{
  "success": true,
  "message": "Memory for conversation user_123 cleared"
}
```

#### GET `/api/verify-memory/{conversation_id}`

验证指定会话的记忆是否存在。

**响应示例**:
```json
{
  "success": true,
  "conversation_id": "user_123",
  "memory_count": 5,
  "memories": [
    {
      "id": "mem_123",
      "content": "用户喜欢喝咖啡"
    }
  ]
}
```

### 5. 工具管理

#### GET `/v1/tools`

列出所有可用的非 MCP 工具。

**响应示例**:
```json
{
  "tools": [
    {
      "name": "search_web",
      "description": "搜索网络信息"
    },
    {
      "name": "calculate",
      "description": "执行数学计算"
    }
  ]
}
```

#### POST `/v1/tools/call`

调用指定的非 MCP 工具。

**请求参数**:
```json
{
  "tool_name": "search_web",
  "params": {
    "query": "Python 编程教程",
    "max_results": 5
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "result": {
    "results": [
      {
        "title": "Python 编程教程",
        "url": "https://example.com/python-tutorial",
        "snippet": "这是一个Python编程教程..."
      }
    ]
  }
}
```

### 6. MCP 服务管理

#### GET `/v1/mcp/tools`

列出所有可用的 MCP 工具。

**响应示例**:
```json
{
  "tools": [
    {
      "name": "mcp_file_read",
      "description": "读取文件内容"
    },
    {
      "name": "mcp_database_query",
      "description": "执行数据库查询"
    }
  ]
}
```

#### POST `/v1/mcp/call`

调用 MCP 服务。

**请求参数**:
```json
{
  "tool_name": "mcp_file_read",
  "mcp_server": "filesystem",
  "params": {
    "file_path": "/path/to/file.txt"
  },
  "service_name": "filesystem",
  "method_name": "read_file"
}
```

**响应示例**:
```json
{
  "success": true,
  "result": {
    "content": "文件内容...",
    "size": 1024
  }
}
```

## 引擎管理 API

### 7. 引擎管理

#### GET `/v1/engines/list`

列出所有已注册的引擎。

**响应示例**:
```json
{
  "success": true,
  "current_engine": "chat_engine",
  "engines": [
    {
      "name": "chat_engine",
      "type": "ChatEngine",
      "status": "active"
    },
    {
      "name": "mem0_proxy",
      "type": "Mem0Proxy",
      "status": "inactive"
    }
  ],
  "count": 2
}
```

#### GET `/v1/engines/current`

获取当前引擎信息。

**响应示例**:
```json
{
  "success": true,
  "engine": {
    "name": "chat_engine",
    "type": "ChatEngine",
    "status": "active",
    "capabilities": ["chat", "memory", "tools"]
  }
}
```

#### POST `/v1/engines/switch`

切换引擎。

**请求参数**:
```json
{
  "engine_name": "mem0_proxy"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "Engine switched to mem0_proxy",
  "current_engine": "mem0_proxy"
}
```

#### GET `/v1/engines/health`

检查所有引擎的健康状态。

**响应示例**:
```json
{
  "success": true,
  "engines": {
    "chat_engine": {
      "status": "healthy",
      "response_time": 0.1
    },
    "mem0_proxy": {
      "status": "healthy",
      "response_time": 0.2
    }
  }
}
```

## 性能监控 API

### 8. 性能监控

#### GET `/v1/performance/stats`

获取性能统计信息。

**响应示例**:
```json
{
  "total_requests": 1000,
  "average_response_time": 0.5,
  "success_rate": 0.98,
  "error_rate": 0.02,
  "memory_usage": {
    "current": "50MB",
    "peak": "100MB"
  }
}
```

#### GET `/v1/performance/recent`

获取最近的性能指标。

**查询参数**:
- `count`: 返回的记录数量 (默认: 10)

**响应示例**:
```json
{
  "count": 10,
  "metrics": [
    {
      "timestamp": "2023-11-05T10:00:00Z",
      "response_time": 0.3,
      "status": "success"
    }
  ]
}
```

#### DELETE `/v1/performance/clear`

清除性能监控数据。

**响应示例**:
```json
{
  "success": true,
  "message": "性能监控数据已清除"
}
```

## Dashboard API

### 9. Dashboard

#### GET `/dashboard`

访问性能监控 Dashboard (无需认证)。

返回 HTML 页面用于可视化性能监控数据。

#### GET `/api/dashboard/stats`

获取 Dashboard 性能统计信息 (无需认证)。

**响应示例**:
```json
{
  "total_requests": 1000,
  "average_response_time": 0.5,
  "success_rate": 0.98
}
```

## 根路径

### GET `/`

获取 API 基本信息 (无需认证)。

**响应示例**:
```json
{
  "message": "Welcome to the YYChat OpenAI Compatible API",
  "version": "0.1.1",
  "api_endpoints": [
    "/v1/chat/completions",
    "/v1/models",
    "/v1/personalities"
  ]
}
```

## 错误处理

### 错误响应格式

所有错误响应都遵循以下格式：

```json
{
  "error": {
    "message": "错误描述",
    "type": "错误类型",
    "param": "参数名",
    "code": "错误代码"
  }
}
```

### 常见错误代码

| HTTP 状态码 | 错误类型 | 错误代码 | 描述 |
|-------------|----------|----------|------|
| 400 | `validation_error` | `invalid_request` | 请求参数无效 |
| 401 | `invalid_request_error` | `invalid_api_key` | API Key 无效 |
| 404 | `invalid_request_error` | `model_not_found` | 模型不存在 |
| 500 | `server_error` | `internal_error` | 服务器内部错误 |
| 500 | `mcp_service_error` | `mcp_error` | MCP 服务错误 |

### 错误示例

**API Key 无效**:
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

**模型不存在**:
```json
{
  "error": {
    "message": "Model not found",
    "type": "invalid_request_error",
    "param": "model",
    "code": "model_not_found"
  }
}
```

## 配置说明

### 环境变量配置

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `YYCHAT_API_KEY` | `yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4` | API 密钥 |
| `OPENAI_API_KEY` | - | OpenAI API 密钥 |
| `OPENAI_MODEL` | `gpt-4.1` | 默认模型 |
| `SERVER_HOST` | `0.0.0.0` | 服务器主机 |
| `SERVER_PORT` | `8000` | 服务器端口 |
| `CHAT_ENGINE` | `chat_engine` | 聊天引擎类型 |
| `DEFAULT_PERSONALITY` | `health_assistant` | 默认人格 |
| `ENABLE_PERFORMANCE_MONITOR` | `true` | 启用性能监控 |

### 支持的聊天引擎

1. **chat_engine**: 标准聊天引擎
2. **mem0_proxy**: Mem0 代理引擎

## 使用示例

### Python 客户端示例

```python
import requests
import json

# 配置
API_BASE = "http://localhost:8000"
API_KEY = "your-api-key"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 发送聊天请求
def chat_completion(messages, stream=False):
    url = f"{API_BASE}/v1/chat/completions"
    data = {
        "model": "gpt-4.1",
        "messages": messages,
        "stream": stream,
        "conversation_id": "user_123"
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# 使用示例
messages = [
    {"role": "user", "content": "你好，请介绍一下自己。"}
]

result = chat_completion(messages)
print(result["choices"][0]["message"]["content"])
```

### JavaScript 客户端示例

```javascript
const API_BASE = 'http://localhost:8000';
const API_KEY = 'your-api-key';

async function chatCompletion(messages, stream = false) {
    const response = await fetch(`${API_BASE}/v1/chat/completions`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${API_KEY}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            model: 'gpt-4.1',
            messages: messages,
            stream: stream,
            conversation_id: 'user_123'
        })
    });
    
    return await response.json();
}

// 使用示例
const messages = [
    { role: 'user', content: '你好，请介绍一下自己。' }
];

chatCompletion(messages).then(result => {
    console.log(result.choices[0].message.content);
});
```

## 注意事项

1. **API Key 安全**: 请妥善保管您的 API Key，不要在客户端代码中硬编码。

2. **请求频率**: 建议控制请求频率，避免对服务器造成过大压力。

3. **会话管理**: 使用 `conversation_id` 来管理会话状态和记忆。

4. **流式响应**: 流式响应适用于需要实时显示生成内容的场景。

5. **工具调用**: 工具调用功能需要正确配置相应的工具和服务。

6. **性能监控**: 生产环境建议启用性能监控以跟踪服务状态。

## 更新日志

- **v0.1.1**: 初始版本，支持基本的聊天完成功能
- 支持记忆管理、工具调用、性能监控等功能
- 兼容 OpenAI Chat Completions API 格式
