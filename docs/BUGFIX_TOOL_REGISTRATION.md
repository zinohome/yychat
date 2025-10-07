# Bug 修复：工具未注册导致调用失败

## 🐛 问题描述

用户提问"现在几点钟"时，系统应该调用 `gettime` 工具，但出现以下错误：

```
WARNING | manager.py:12 | Tool None not found
ERROR | chat_engine.py:387 | Error generating streaming response: 'NoneType' object has no attribute 'get'
```

## 🔍 根本原因

发现了**两个关键问题**：

### 1. 工具未注册

在 `services/tools/implementations/` 目录下的所有工具实现文件中，工具注册代码被注释掉了：

```python
# time_tool.py
#tool_registry.register(TimeTool)  ❌ 被注释

# calculator.py
#tool_registry.register(CalculatorTool)  ❌ 被注释

# tavily_search.py
# tool_registry.register(TavilySearchTool)  ❌ 被注释或有空格
```

**影响**：所有工具都无法被找到和调用。

### 2. ToolManager 返回 None

在 `services/tools/manager.py` 中，当工具未找到时返回 `None`：

```python
# 问题代码
async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    tool = tool_registry.get_tool(tool_name)
    if not tool:
        log.warning(f"Tool {tool_name} not found")
        return None  ❌ 返回 None 导致后续代码崩溃
```

**影响**：返回的 `None` 在 `build_tool_response_messages()` 中被当作字典访问，导致 `'NoneType' object has no attribute 'get'` 错误。

## ✅ 解决方案

### 1. 启用所有工具注册

**time_tool.py**（第36行）
```python
# 修复前
#tool_registry.register(TimeTool)

# 修复后
tool_registry.register(TimeTool())
```

**calculator.py**（第64行）
```python
# 修复前
#tool_registry.register(CalculatorTool)

# 修复后
tool_registry.register(CalculatorTool())
```

**tavily_search.py**（第89行）
```python
# 修复前
# tool_registry.register(TavilySearchTool)

# 修复后
tool_registry.register(TavilySearchTool())
```

**注意**：需要实例化工具类（添加 `()`）才能正确注册。

### 2. 修复 ToolManager 的返回值

**manager.py**（第9-27行）
```python
# 修复前
async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    tool = tool_registry.get_tool(tool_name)
    if not tool:
        log.warning(f"Tool {tool_name} not found")
        return None  ❌
    
    try:
        result = await tool.execute(params)
        return {"success": True, "result": result}  ❌ 缺少 tool_name
    except Exception as e:
        return {"success": False, "error": str(e)}  ❌ 缺少 tool_name

# 修复后
async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    tool = tool_registry.get_tool(tool_name)
    if not tool:
        log.warning(f"Tool {tool_name} not found")
        return {
            "success": False, 
            "error": f"工具 '{tool_name}' 未找到",
            "tool_name": tool_name  ✅ 返回完整字典
        }
    
    try:
        result = await tool.execute(params)
        return {"success": True, "result": result, "tool_name": tool_name}  ✅
    except Exception as e:
        return {"success": False, "error": str(e), "tool_name": tool_name}  ✅
```

### 3. 简化 execute_tools_concurrently

由于 `execute_tool` 现在保证返回完整字典，简化了批量执行逻辑：

```python
# 修复后
async def execute_tools_concurrently(self, tool_calls: list) -> list:
    tasks = []
    for call in tool_calls:
        task = self.execute_tool(call["name"], call["parameters"])
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # 异常情况：返回错误信息
            processed_results.append({
                "success": False,
                "error": str(result),
                "tool_name": tool_calls[i]["name"]
            })
        else:
            # 正常情况：execute_tool 已经返回完整的字典
            processed_results.append(result)
    
    return processed_results
```

## 📊 修复效果

### 修复前

1. **工具调用失败**：
   ```
   Tool None not found
   'NoneType' object has no attribute 'get'
   ```

2. **用户体验**：
   - 问"现在几点"无响应
   - 计算器和搜索功能不可用
   - 看到错误信息

### 修复后

1. **工具正常调用**：
   ```
   Executing tool: gettime with params: {}
   Tool gettime execution finished. Success: True
   ```

2. **用户体验**：
   - ✅ 时间查询正常工作
   - ✅ 计算器可用
   - ✅ 搜索功能可用
   - ✅ 即使工具未找到，也能得到友好的错误提示

## 🧪 验证方法

### 1. 检查工具是否注册

```python
# 在 Python 交互环境中
from services.tools.registry import tool_registry

# 查看所有已注册的工具
print(tool_registry.list_tools())

# 应该看到：
# ['gettime', 'calculator', 'tavily_search']
```

### 2. 测试时间查询

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "现在几点？"}],
    "use_tools": true,
    "stream": true
  }'
```

**预期响应**：
```
现在是 2025-10-07 14:30:00（上海时间，UTC+8）
```

### 3. 测试工具未找到的情况

如果工具确实不存在，现在会得到友好的错误提示：

```
工具 'unknown_tool' 未找到
```

而不是系统崩溃。

## 📚 相关文件

### 修改的文件

1. **services/tools/manager.py** - 修复返回值问题
2. **services/tools/implementations/time_tool.py** - 启用工具注册
3. **services/tools/implementations/calculator.py** - 启用工具注册
4. **services/tools/implementations/tavily_search.py** - 启用工具注册

### 受影响的功能

- ✅ 时间查询（`gettime`）
- ✅ 计算器（`calculator`）
- ✅ 网络搜索（`tavily_search`）
- ✅ 流式响应中的工具调用
- ✅ 非流式响应中的工具调用

## 💡 最佳实践

### 1. 工具注册模式

```python
# ✅ 正确：实例化后注册
tool_registry.register(MyTool())

# ❌ 错误：注册类而不是实例
tool_registry.register(MyTool)

# ❌ 错误：注释掉注册
#tool_registry.register(MyTool())
```

### 2. 工具执行返回值

```python
# ✅ 正确：始终返回完整字典
return {
    "success": True/False,
    "result": result,  # 或 "error": error_msg
    "tool_name": tool_name  # 必须包含
}

# ❌ 错误：返回 None
return None
```

### 3. 错误处理

```python
# ✅ 正确：提供有意义的错误信息
return {
    "success": False,
    "error": f"工具 '{tool_name}' 未找到",
    "tool_name": tool_name
}

# ❌ 错误：抛出异常或返回 None
raise Exception("Tool not found")
return None
```

## 🔄 后续建议

1. **自动化测试**：添加工具注册检查
2. **启动验证**：应用启动时验证所有工具是否正确注册
3. **文档更新**：在工具开发指南中说明注册要求
4. **CI 检查**：在 CI 中检查工具注册代码是否被注释

## 📝 总结

这次修复解决了两个关键问题：

1. ✅ **工具注册**：所有工具现在都正确注册并可用
2. ✅ **错误处理**：工具未找到时返回友好错误而不是崩溃

修复后，所有工具调用功能恢复正常，用户可以正常使用时间查询、计算器和搜索功能。

