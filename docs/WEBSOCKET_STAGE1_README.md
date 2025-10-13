# WebSocket 阶段1 功能说明

## 🎯 概述

本文档描述了YYChat后端WebSocket功能阶段1的实现，包括基础WebSocket通信层、消息路由系统和文本消息处理。

## 🚀 新增功能

### 1. WebSocket通信层
- **连接管理**: 支持多客户端连接，最大连接数100
- **心跳机制**: 30秒心跳间隔，300秒连接超时
- **消息大小限制**: 1MB消息大小限制
- **自动清理**: 自动清理过期连接

### 2. 消息路由系统
- **消息类型注册**: 支持注册不同类型的消息处理器
- **中间件支持**: 支持消息处理中间件
- **错误处理**: 统一的错误处理和响应机制

### 3. 文本消息处理
- **流式响应**: 支持流式和非流式文本响应
- **现有功能集成**: 完全集成现有的chat_engine、记忆、人格化、工具调用等功能
- **错误恢复**: 完善的错误处理和恢复机制

## 📡 API端点

### WebSocket端点
- `ws://localhost:9800/ws/chat` - 实时聊天WebSocket连接

### REST端点
- `GET /ws/status` - 获取WebSocket连接状态
- `GET /ws/handlers` - 获取已注册的消息处理器

## 💬 消息格式

### 基础消息格式
```json
{
  "type": "message_type",
  "timestamp": 1234567890.123,
  "client_id": "optional_client_id"
}
```

### 支持的消息类型

#### 1. 心跳消息
```json
{
  "type": "heartbeat",
  "timestamp": 1234567890.123
}
```

**响应:**
```json
{
  "type": "heartbeat_response",
  "timestamp": 1234567890.123,
  "client_id": "client_id"
}
```

#### 2. Ping消息
```json
{
  "type": "ping",
  "timestamp": 1234567890.123
}
```

**响应:**
```json
{
  "type": "pong",
  "timestamp": 1234567890.123,
  "client_id": "client_id"
}
```

#### 3. 状态查询
```json
{
  "type": "get_status",
  "timestamp": 1234567890.123
}
```

**响应:**
```json
{
  "type": "status_response",
  "data": {
    "total_connections": 5,
    "active_connections": 5,
    "total_messages": 100,
    "max_connections": 100,
    "uptime": 3600.0
  },
  "timestamp": 1234567890.123,
  "client_id": "client_id"
}
```

#### 4. 文本消息
```json
{
  "type": "text_message",
  "content": "Hello, how are you?",
  "conversation_id": "optional_conversation_id",
  "personality_id": "optional_personality_id",
  "use_tools": true,
  "stream": true,
  "timestamp": 1234567890.123
}
```

**流式响应:**
```json
// 处理开始
{
  "type": "processing_start",
  "timestamp": 1234567890.123,
  "client_id": "client_id"
}

// 流式响应开始
{
  "type": "stream_start",
  "timestamp": 1234567890.123,
  "client_id": "client_id"
}

// 内容块
{
  "type": "stream_chunk",
  "content": "Hello! I'm doing well, thank you for asking.",
  "timestamp": 1234567890.123,
  "client_id": "client_id"
}

// 流式响应结束
{
  "type": "stream_end",
  "full_content": "Hello! I'm doing well, thank you for asking. How can I help you today?",
  "timestamp": 1234567890.123,
  "client_id": "client_id"
}
```

## 🔧 配置

### WebSocket配置
配置文件: `config/websocket_config.py`

```python
class WebSocketConfig:
    MAX_CONNECTIONS = 100
    HEARTBEAT_INTERVAL = 30
    CONNECTION_TIMEOUT = 300
    MESSAGE_SIZE_LIMIT = 1024 * 1024  # 1MB
```

## 🧪 测试

### 运行测试脚本
```bash
# 确保服务器正在运行
python app.py

# 在另一个终端运行测试
python test_websocket.py
```

### 测试内容
1. **连接测试**: 验证WebSocket连接建立
2. **心跳测试**: 验证心跳机制
3. **Ping测试**: 验证ping/pong机制
4. **状态查询测试**: 验证状态查询功能
5. **文本消息测试**: 验证文本消息处理和流式响应

## 📁 新增文件

```
yychat/
├── config/
│   └── websocket_config.py          # WebSocket配置
├── core/
│   ├── websocket_manager.py         # WebSocket管理器
│   └── message_router.py            # 消息路由器
├── handlers/
│   ├── __init__.py                  # 处理器模块初始化
│   └── text_message_handler.py      # 文本消息处理器
├── test_websocket.py                # WebSocket测试脚本
└── docs/
    └── WEBSOCKET_STAGE1_README.md   # 本文档
```

## 🔄 与现有功能的集成

### 完全兼容现有功能
- ✅ **ChatEngine**: 完全集成现有的聊天引擎
- ✅ **记忆管理**: 支持conversation_id，自动使用记忆功能
- ✅ **人格化**: 支持personality_id，自动应用人格设置
- ✅ **工具调用**: 支持use_tools参数，自动调用工具
- ✅ **MCP调用**: 通过工具调用自动支持MCP服务
- ✅ **流式响应**: 支持流式和非流式响应

### 不破坏现有功能
- ✅ **REST API**: 所有现有REST API保持不变
- ✅ **认证机制**: 保持现有的Bearer Token认证
- ✅ **配置系统**: 使用现有的配置系统
- ✅ **日志系统**: 使用现有的日志系统

## 🚀 下一步

阶段1已完成，接下来将进入阶段2：音频处理服务
- 语音转文本 (STT)
- 文本转语音 (TTS)
- 音频API端点

## 📞 支持

如有问题，请查看日志文件或联系开发团队。
