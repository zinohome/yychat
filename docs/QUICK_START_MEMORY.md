# Mem0 记忆系统快速开始

## 🚀 快速配置

### 本地模式（推荐开发使用）

```bash
# .env 文件
MEMO_USE_LOCAL=true
```

就这么简单！其他配置都有默认值。

### API 模式（生产环境可选）

```bash
# .env 文件
MEMO_USE_LOCAL=false
MEM0_API_KEY=your_api_key_here
```

## ✅ 验证配置

### 1. 检查配置

```bash
python utils/check_mem0_config.py
```

输出示例：
```
📌 当前模式: 本地模式 (Local)
✅ 配置检查通过！所有配置项都正确。
```

### 2. 运行测试

```bash
python test_memory_mode.py
```

输出示例：
```
=== 测试同步 ChatMemory ===
当前模式: 本地模式
✓ ChatMemory 初始化成功
✓ 添加消息成功
✓ 检索到 1 条相关记忆
✅ 同步 ChatMemory 测试通过
```

## 📖 使用示例

### 在代码中使用（无需修改）

```python
from core.chat_memory import ChatMemory, get_async_chat_memory

# 同步使用
memory = ChatMemory()  # 自动根据配置选择模式
memory.add_message(
    conversation_id="user123",
    message={"role": "user", "content": "你好"}
)

# 异步使用
async_memory = get_async_chat_memory()
await async_memory.add_message(
    conversation_id="user123",
    message={"role": "assistant", "content": "你好！"}
)
```

## 🔄 模式切换

### 从本地切换到 API

1. 修改 `.env`:
   ```bash
   MEMO_USE_LOCAL=false
   MEM0_API_KEY=your_key
   ```

2. 重启应用

### 从 API 切换到本地

1. 修改 `.env`:
   ```bash
   MEMO_USE_LOCAL=true
   ```

2. 重启应用

## 📚 详细文档

- [完整使用指南](./MEMORY_MODE_GUIDE.md) - 详细配置和最佳实践
- [优化总结](./MEMORY_OPTIMIZATION_SUMMARY.md) - 技术实现细节

## 🆘 故障排查

### 问题：配置检查失败

```bash
# 查看详细错误
python utils/check_mem0_config.py

# 查看配置模板
python utils/check_mem0_config.py --template
```

### 问题：测试失败

```bash
# 查看日志
tail -f logs/app.log

# 检查依赖
pip install -r requirements.txt
```

### 问题：本地模式初始化慢

首次初始化 ChromaDB 需要几秒钟，这是正常的。

### 问题：API 模式连接失败

检查网络连接和 API Key 是否正确。

## 💡 小贴士

1. **开发环境**：使用本地模式，快速且免费
2. **生产环境**：根据需求选择，本地模式更私密，API 模式更易扩展
3. **数据迁移**：两种模式数据独立，切换前请注意备份
4. **性能优化**：本地模式无网络延迟，但首次初始化较慢

## 🎯 常见使用场景

### 场景 1：个人开发测试

```bash
# 使用本地模式，无需额外配置
MEMO_USE_LOCAL=true
```

### 场景 2：多人协作（共享记忆）

```bash
# 使用 API 模式，团队共享记忆
MEMO_USE_LOCAL=false
MEM0_API_KEY=team_shared_key
```

### 场景 3：离线部署

```bash
# 使用本地模式，完全离线运行
MEMO_USE_LOCAL=true
CHROMA_PERSIST_DIRECTORY=/data/chroma
```

## 📞 支持

遇到问题？

1. 查看 [详细文档](./MEMORY_MODE_GUIDE.md)
2. 运行 `python utils/check_mem0_config.py` 诊断
3. 检查 `logs/app.log` 日志

