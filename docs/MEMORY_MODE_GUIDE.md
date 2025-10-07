# Mem0 使用模式配置指南

## 概述

`yychat` 现在支持两种 Mem0 记忆存储模式：
1. **本地模式**（默认）：使用本地 ChromaDB 存储
2. **API模式**：使用 Mem0 云服务

## 配置方式

### 环境变量配置

在 `.env` 文件或环境变量中设置：

```bash
# 使用本地模式（默认）
MEMO_USE_LOCAL=true

# 或使用 API 模式
MEMO_USE_LOCAL=false
MEM0_API_KEY=your_mem0_api_key_here
```

## 两种模式对比

| 特性 | 本地模式 | API 模式 |
|------|---------|---------|
| **数据存储** | 本地 ChromaDB (`./chroma_db/`) | Mem0 云端 |
| **API Key** | 不需要 | 必需 `MEM0_API_KEY` |
| **网络依赖** | 无（完全离线） | 需要网络连接 |
| **性能** | 低延迟（本地访问） | 受网络影响 |
| **成本** | 免费（使用自己的资源） | 按 Mem0 定价收费 |
| **扩展性** | 受限于本地资源 | 云端自动扩展 |
| **数据隐私** | 完全私密（本地） | 存储在 Mem0 服务器 |
| **多实例共享** | 不支持 | 支持（多实例共享记忆） |

## 本地模式配置详情

### 1. 环境变量

```bash
# 启用本地模式
MEMO_USE_LOCAL=true

# LLM 配置（用于记忆摘要和总结）
MEM0_LLM_PROVIDER=openai
MEM0_LLM_CONFIG_MODEL=gpt-4o-mini
MEM0_LLM_CONFIG_MAX_TOKENS=32768

# ChromaDB 配置
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=chat_history
```

### 2. 依赖安装

```bash
pip install mem0ai chromadb
```

### 3. 数据位置

记忆数据存储在：
- 默认路径：`./chroma_db/`
- 可通过 `CHROMA_PERSIST_DIRECTORY` 自定义

## API 模式配置详情

### 1. 环境变量

```bash
# 启用 API 模式
MEMO_USE_LOCAL=false

# Mem0 API 配置
MEM0_API_KEY=your_mem0_api_key_here
```

### 2. 获取 API Key

1. 访问 [Mem0 官网](https://mem0.ai)
2. 注册账号
3. 在控制台获取 API Key

### 3. 依赖安装

```bash
pip install mem0ai
```

## 代码实现说明

### ChatMemory 类

```python
from core.chat_memory import ChatMemory

# 自动根据配置选择模式
memory = ChatMemory()

# 添加消息
memory.add_message(
    conversation_id="user123",
    message={"role": "user", "content": "你好"}
)

# 检索相关记忆
relevant = memory.get_relevant_memory(
    conversation_id="user123",
    query="你好"
)
```

### AsyncChatMemory 类

```python
from core.chat_memory import get_async_chat_memory

# 获取异步实例
async_memory = get_async_chat_memory()

# 异步添加消息
await async_memory.add_message(
    conversation_id="user123",
    message={"role": "assistant", "content": "你好！"}
)

# 异步检索记忆
relevant = await async_memory.get_relevant_memory(
    conversation_id="user123",
    query="问候"
)
```

## 模式切换

### 从本地切换到 API

1. 修改环境变量：
   ```bash
   MEMO_USE_LOCAL=false
   MEM0_API_KEY=your_api_key
   ```

2. 重启应用

3. **注意**：本地存储的记忆不会自动迁移到云端

### 从 API 切换到本地

1. 修改环境变量：
   ```bash
   MEMO_USE_LOCAL=true
   ```

2. 重启应用

3. **注意**：云端记忆不会自动同步到本地

## 数据迁移

### 本地 → API

如需将本地记忆迁移到 Mem0 API：

```python
from core.chat_memory import ChatMemory
from mem0 import MemoryClient

# 读取本地记忆
local_memory = ChatMemory()  # MEMO_USE_LOCAL=true
local_memories = local_memory.get_all_memory("user123")

# 写入到 API
api_client = MemoryClient(api_key="your_api_key")
for mem in local_memories:
    api_client.add(mem, user_id="user123")
```

### API → 本地

类似的逆向操作。

## 最佳实践

### 本地模式

- ✅ 适合个人使用或小型部署
- ✅ 对数据隐私要求高的场景
- ✅ 网络不稳定或离线环境
- ✅ 开发和测试环境

### API 模式

- ✅ 适合多用户/大规模部署
- ✅ 需要跨实例共享记忆
- ✅ 不想管理本地存储
- ✅ 生产环境（高可用）

## 故障排查

### 本地模式问题

**问题：ChromaDB 初始化失败**
```
解决：检查 CHROMA_PERSIST_DIRECTORY 路径是否有写权限
```

**问题：记忆检索慢**
```
解决：增加 MEMORY_RETRIEVAL_TIMEOUT 或优化查询长度
```

### API 模式问题

**问题：API Key 无效**
```
解决：检查 MEM0_API_KEY 是否正确配置
```

**问题：网络超时**
```
解决：检查网络连接或增加超时时间
```

## 监控与日志

应用启动时会输出当前使用的模式：

```
# 本地模式
INFO: 使用本地模式初始化Memory，配置: ...

# API 模式
INFO: 使用API模式初始化MemoryClient
```

查看日志文件：`./logs/app.log`

## 相关配置

完整配置项参见 `config/config.py`:

- `MEMO_USE_LOCAL`: 模式开关
- `MEM0_API_KEY`: API 密钥
- `MEM0_LLM_PROVIDER`: LLM 提供商
- `MEM0_LLM_CONFIG_MODEL`: LLM 模型
- `CHROMA_PERSIST_DIRECTORY`: 本地存储路径
- `MEMORY_RETRIEVAL_LIMIT`: 检索数量限制
- `MEMORY_RETRIEVAL_TIMEOUT`: 检索超时时间

## 总结

通过 `MEMO_USE_LOCAL` 配置，你可以灵活选择适合你场景的记忆存储方式，两种模式可以随时切换，无需修改代码。

