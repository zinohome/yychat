# Bug 修复：工具调用 JSON 解析错误

## 🐛 问题描述

在流式响应处理中发现 JSON 解析错误：

```
ERROR | chat_engine.py:379 | Error generating streaming response: Expecting value: line 1 column 1 (char 0)
```

## 🔍 根本原因

在 `_handle_tool_calls` 和流式工具处理中，代码直接使用 `json.loads()` 解析工具参数：

```python
# 问题代码
parameters = json.loads(call["function"]["arguments"])
```

**问题场景**：
1. 工具参数字符串为空（`""`）
2. 工具参数格式不正确
3. 工具参数在流式传输中未完整接收

这些情况下 `json.loads()` 会抛出 `JSONDecodeError`，导致整个响应失败。

## ✅ 解决方案

添加安全的 JSON 解析逻辑：

```python
# 修复后的代码
args_str = call["function"]["arguments"]
try:
    parameters = json.loads(args_str) if args_str else {}
except json.JSONDecodeError as e:
    log.error(f"工具参数 JSON 解析失败: {args_str}, 错误: {e}")
    parameters = {}
```

### 修复内容

1. **检查空字符串**：`if args_str else {}`
2. **异常捕获**：`try-except` 包裹 `json.loads()`
3. **降级处理**：解析失败时使用空参数 `{}`
4. **日志记录**：记录详细的错误信息便于调试

### 修复位置

**文件**：`core/chat_engine.py`

**位置 1**：`_handle_tool_calls()` 方法（第 397-410 行）
```python
# 准备工具调用列表
calls_to_execute = []
for call in normalized_calls:
    # 安全地解析 JSON 参数
    args_str = call["function"]["arguments"]
    try:
        parameters = json.loads(args_str) if args_str else {}
    except json.JSONDecodeError as e:
        log.error(f"工具参数 JSON 解析失败: {args_str}, 错误: {e}")
        parameters = {}
    
    calls_to_execute.append({
        "name": call["function"]["name"],
        "parameters": parameters
    })
```

**位置 2**：`_generate_streaming_response()` 方法（第 313-327 行）
```python
# 准备工具调用列表（流式响应中）
calls_to_execute = []
for call in normalized_calls:
    # 安全地解析 JSON 参数
    args_str = call["function"]["arguments"]
    try:
        parameters = json.loads(args_str) if args_str else {}
    except json.JSONDecodeError as e:
        log.error(f"工具参数 JSON 解析失败: {args_str}, 错误: {e}")
        parameters = {}
    
    calls_to_execute.append({
        "name": call["function"]["name"],
        "parameters": parameters
    })
```

## 📊 影响范围

### 受影响的场景

- ✅ 流式响应中的工具调用
- ✅ 非流式响应中的工具调用
- ✅ 工具参数为空的情况
- ✅ 工具参数格式错误的情况

### 修复效果

**修复前**：
```
ERROR | Error generating streaming response: Expecting value: line 1 column 1 (char 0)
→ 整个响应失败，用户看到错误信息
```

**修复后**：
```
ERROR | 工具参数 JSON 解析失败: "", 错误: ...
→ 使用空参数继续执行，工具可能返回默认结果
→ 用户仍能得到响应（可能是提示需要提供参数）
```

## 🔄 相关问题

### 为什么会出现空参数？

1. **流式传输延迟**：arguments 在多个 chunk 中累积
2. **工具不需要参数**：某些工具本身不需要参数（如 `gettime`）
3. **模型错误**：模型可能生成不完整的工具调用

### 最佳实践

1. **工具定义时明确参数**：
   ```json
   {
     "name": "gettime",
     "parameters": {
       "type": "object",
       "properties": {},
       "required": []
     }
   }
   ```

2. **工具实现中处理空参数**：
   ```python
   def execute(self, params=None):
       if not params:
           params = {}
       # 处理逻辑...
   ```

3. **日志监控**：关注 "工具参数 JSON 解析失败" 日志

## 🧪 测试验证

### 测试场景

1. **正常工具调用**（有参数）
   ```python
   # 应该正常工作
   {"name": "weather", "arguments": '{"city": "北京"}'}
   ```

2. **无参数工具调用**
   ```python
   # 修复前：抛出异常
   # 修复后：使用空参数 {}
   {"name": "gettime", "arguments": ""}
   ```

3. **错误格式参数**
   ```python
   # 修复前：抛出异常
   # 修复后：记录错误，使用空参数
   {"name": "tool", "arguments": "invalid json"}
   ```

### 验证方法

```bash
# 1. 启动服务
python app.py

# 2. 测试时间查询（无参数工具）
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "现在几点？"}],
    "stream": true
  }'

# 3. 查看日志
tail -f logs/app.log
```

## 📝 总结

### ✅ 已修复

- 工具调用 JSON 解析异常处理
- 空参数和错误格式的容错
- 详细的错误日志记录

### 🎯 改进效果

- 更稳定：不会因为参数问题导致整个响应失败
- 更友好：用户仍能得到有意义的响应
- 更易调试：清晰的错误日志

### 💡 后续建议

1. **监控**：关注 "工具参数 JSON 解析失败" 频率
2. **优化**：对频繁出错的工具进行参数验证改进
3. **文档**：明确工具的参数要求和默认行为

