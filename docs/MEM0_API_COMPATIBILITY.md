# Mem0 API 兼容性说明

## 问题描述

Mem0 的**本地模式**和 **API 模式**在 `add()` 方法的参数格式上有差异：

### 本地模式（Memory/AsyncMemory）

```python
from mem0 import Memory

memory = Memory(config=memory_config)
memory.add(
    "这是消息内容",           # 直接传入字符串
    user_id="user123",
    metadata={"role": "user"}
)
```

### API 模式（MemoryClient/AsyncMemoryClient）

```python
from mem0 import MemoryClient

client = MemoryClient(api_key="your_key")
client.add(
    messages=[{                # 需要 messages 列表
        "role": "user",
        "content": "这是消息内容"
    }],
    user_id="user123",
    metadata={"role": "user"}
)
```

## 错误示例

如果在 API 模式下使用本地模式的参数格式：

```python
# ❌ 错误用法（会导致 400 Bad Request）
client.add(
    "这是消息内容",  # API 模式不接受直接的字符串
    user_id="user123"
)
```

**错误信息**：
```
HTTP error occurred: Client error '400 Bad Request' for url 'https://api.mem0.ai/v1/memories/'
ERROR: '"messages"'
```

## 解决方案

我们在 `core/chat_memory.py` 中通过检测模式自动适配参数格式：

### ChatMemory.add_message()

```python
def add_message(self, conversation_id: str, message: dict):
    if self.is_local:
        # 本地模式：直接传字符串
        self.memory.add(
            message["content"],
            user_id=conversation_id,
            metadata=metadata
        )
    else:
        # API 模式：使用 messages 列表
        self.memory.add(
            messages=[{
                "role": message["role"],
                "content": message["content"]
            }],
            user_id=conversation_id,
            metadata=metadata
        )
```

### AsyncChatMemory.add_message()

```python
async def add_message(self, conversation_id: str, message: dict):
    if self.is_local:
        # 本地模式
        await self.async_memory.add(
            message["content"],
            user_id=conversation_id,
            metadata=metadata
        )
    else:
        # API 模式
        await self.async_memory.add(
            messages=[{
                "role": message["role"],
                "content": message["content"]
            }],
            user_id=conversation_id,
            metadata=metadata
        )
```

### AsyncChatMemory.add_messages_batch()

批量添加方法也做了相同的适配：

```python
if self.is_local:
    result = await self.async_memory.add(
        formatted_content,
        user_id=conversation_id,
        metadata=metadata
    )
else:
    result = await self.async_memory.add(
        messages=[{
            "role": message["role"],
            "content": formatted_content
        }],
        user_id=conversation_id,
        metadata=metadata
    )
```

## 其他 API 差异

### 1. 检索方法

**本地模式**：
```python
# 可能有多个方法名
memory.get_relevant(query, user_id=user_id, limit=5)
# 或
memory.search(query, user_id=user_id, limit=5)
```

**API 模式**：
```python
# 统一使用 search
client.search(query, user_id=user_id, limit=5)
```

### 2. 返回格式

**本地模式**：
- 返回列表或字典
- 结构可能因版本而异

**API 模式**：
- 通常返回标准的 JSON 响应
- 包含 `results` 字段

我们的代码已经处理了这些差异。

## 使用建议

### 开发阶段

- ✅ 使用本地模式（`MEMO_USE_LOCAL=true`）
- 优点：快速、免费、无网络依赖
- 注意：首次初始化较慢

### 生产环境

**本地模式适用于**：
- 对数据隐私要求高
- 单机部署
- 不需要跨实例共享记忆

**API 模式适用于**：
- 多实例部署
- 需要跨服务器共享记忆
- 希望 Mem0 托管存储

## 测试验证

### 测试 API 模式

```bash
# 1. 设置环境变量
export MEMO_USE_LOCAL=false
export MEM0_API_KEY=your_api_key

# 2. 运行测试
python check_mem0_config.py
```

如果配置正确，应该看到：
```
✓ API Key 已配置
✓ mem0ai 已安装
✓ MemoryClient 可用
```

### 运行完整测试

```bash
python test_memory_mode.py
```

应该能成功添加和检索记忆。

## 故障排查

### 问题 1：API 400 错误

**症状**：
```
HTTP error '400 Bad Request'
ERROR: '"messages"'
```

**原因**：使用了本地模式的参数格式

**解决**：确保使用最新的 `chat_memory.py`（已包含自动适配）

### 问题 2：API Key 无效

**症状**：
```
HTTP error '401 Unauthorized'
```

**解决**：检查 `MEM0_API_KEY` 是否正确

### 问题 3：网络超时

**症状**：
```
TimeoutError
```

**解决**：
1. 检查网络连接
2. 增加超时时间：`MEMORY_RETRIEVAL_TIMEOUT=30`

## 版本兼容性

| Mem0 版本 | 本地模式 | API 模式 | 兼容性 |
|----------|---------|---------|--------|
| < 0.1.0  | Memory | N/A | ⚠️ 旧版本 |
| 0.1.x    | Memory | MemoryClient | ✅ 支持 |
| 0.2.x+   | Memory | MemoryClient | ✅ 推荐 |

建议使用最新版本：
```bash
pip install --upgrade mem0ai
```

## 总结

✅ **已修复**
- 自动检测模式并适配参数格式
- 本地和 API 模式无缝切换
- 统一的调用接口

✅ **无需担心**
- 直接使用 `ChatMemory` 和 `AsyncChatMemory`
- 框架自动处理 API 差异
- 切换模式无需修改代码

🎯 **最佳实践**
- 开发用本地模式
- 生产根据需求选择
- 定期测试两种模式

