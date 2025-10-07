# Chat Engine 测试检查清单

**版本**: v1.0.0  
**日期**: 2025-10-07

---

## 🧪 手动测试清单

### 1. 基础功能测试

#### ✅ 测试 1.1: 普通对话（非流式）
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
```

**预期结果**: 返回正常的 JSON 响应，包含 `role` 和 `content`

---

#### ✅ 测试 1.2: 流式对话
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "请简单介绍一下人工智能"}],
    "stream": true
  }'
```

**预期结果**: 返回流式响应，逐步输出内容

---

### 2. 工具调用测试

#### ✅ 测试 2.1: 时间工具
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "现在几点钟？"}],
    "personality_id": "health_assistant",
    "use_tools": true,
    "stream": true
  }'
```

**预期结果**: 
1. 调用 `gettime` 工具
2. 返回当前上海时间
3. 内容被保存到记忆

**验证点**:
- ✅ 工具被正确识别
- ✅ 工具参数解析成功（空参数）
- ✅ 返回格式化时间
- ✅ 无 JSON 解析错误

---

#### ✅ 测试 2.2: 计算器工具
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "计算 123 加 456"}],
    "use_tools": true,
    "stream": false
  }'
```

**预期结果**: 返回计算结果 579

---

#### ✅ 测试 2.3: 搜索工具（需要 API Key）
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "搜索一下梅西是谁"}],
    "use_tools": true,
    "stream": true
  }'
```

**预期结果**: 返回梅西的相关信息

---

### 3. 人格系统测试

#### ✅ 测试 3.1: 健康助手人格
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "我最近总是失眠"}],
    "personality_id": "health_assistant",
    "stream": false
  }'
```

**预期结果**: 以健康助手的口吻回复，给出专业建议

---

#### ✅ 测试 3.2: 专业人格
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "如何提高代码质量？"}],
    "personality_id": "professional",
    "stream": false
  }'
```

**预期结果**: 以专业、简洁的方式回复

---

### 4. 记忆系统测试

#### ✅ 测试 4.1: 记忆保存
```bash
# 第一轮对话
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "我叫张三，今年25岁"}],
    "conversation_id": "test_memory_001",
    "stream": false
  }'

# 等待 2 秒让记忆保存

# 第二轮对话
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你还记得我的名字和年龄吗？"}],
    "conversation_id": "test_memory_001",
    "stream": false
  }'
```

**预期结果**: 第二轮对话能正确回忆第一轮的信息

---

#### ✅ 测试 4.2: 获取记忆
```bash
curl -X GET http://localhost:8000/v1/conversations/test_memory_001/memory
```

**预期结果**: 返回该对话的所有记忆

---

#### ✅ 测试 4.3: 清除记忆
```bash
curl -X DELETE http://localhost:8000/v1/conversations/test_memory_001/memory
```

**预期结果**: 记忆被清除，再次查询返回空列表

---

### 5. 边界情况测试

#### ✅ 测试 5.1: 空消息列表
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [],
    "stream": false
  }'
```

**预期结果**: 返回友好的错误提示

---

#### ✅ 测试 5.2: 无效消息格式
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"invalid": "format"}],
    "stream": false
  }'
```

**预期结果**: 返回格式错误提示

---

#### ✅ 测试 5.3: 超长消息
```bash
# 生成一个 10000 字的消息
python -c "
import requests
long_text = '测试' * 5000
response = requests.post('http://localhost:8000/v1/chat/completions', json={
    'messages': [{'role': 'user', 'content': long_text}],
    'stream': False
})
print(response.status_code, len(response.text))
"
```

**预期结果**: 正常处理或返回 token 超限提示

---

### 6. 并发测试

#### ✅ 测试 6.1: 10 个并发请求
```bash
#!/bin/bash
for i in {1..10}; do
  curl -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
      "messages": [{"role": "user", "content": "测试并发请求 '${i}'"}],
      "stream": false
    }' &
done
wait
```

**预期结果**: 所有请求都能正常响应

---

#### ✅ 测试 6.2: 100 个并发请求（压力测试）
```bash
# 使用 Apache Bench
ab -n 100 -c 10 -p request.json -T application/json \
   http://localhost:8000/v1/chat/completions
```

**预期结果**: 
- 响应时间合理（< 2s）
- 无错误或超时
- 无内存泄漏

---

### 7. 错误恢复测试

#### ✅ 测试 7.1: OpenAI API 不可用
```bash
# 临时修改 .env 中的 API Key 为无效值
# 然后发送请求

curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "测试"}],
    "stream": false
  }'
```

**预期结果**: 返回友好的错误提示，不会崩溃

---

#### ✅ 测试 7.2: 工具执行失败
```bash
# 使用一个会失败的参数
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "计算 10 除以 0"}],
    "use_tools": true,
    "stream": false
  }'
```

**预期结果**: 工具返回错误，但系统继续正常运行

---

## 🔍 日志检查要点

在运行上述测试时，检查日志中是否有以下内容：

### ✅ 正常日志
```
INFO | 传入参数 - personality_id: health_assistant, use_tools: True
DEBUG | 最终请求参数: {...}
DEBUG | Tool gettime execution finished. Success: True
DEBUG | 总处理时间: 1.23秒
```

### ❌ 需要关注的日志
```
ERROR | Tool None not found
ERROR | Expecting value: line 1 column 1 (char 0)
WARNING | 避免超出模型token限制
ERROR | 'NoneType' object has no attribute 'get'
```

---

## 📊 性能指标

### 响应时间基准
| 场景 | 目标时间 | 可接受时间 | 超时时间 |
|------|----------|------------|----------|
| 普通对话（非流式） | < 1s | < 2s | > 5s |
| 流式对话（首字节） | < 0.5s | < 1s | > 2s |
| 工具调用 | < 2s | < 3s | > 5s |
| 记忆检索 | < 0.3s | < 0.5s | > 1s |

### 资源使用
- CPU: < 50% (单核)
- 内存: < 500MB
- 连接数: < 100

---

## 🐛 已知问题跟踪

| 问题ID | 描述 | 状态 | 优先级 |
|--------|------|------|--------|
| ~~#001~~ | ~~异步流式迭代器阻塞~~ | ✅ 已修复 | 高 |
| ~~#002~~ | ~~工具调用后内容未保存~~ | ✅ 已修复 | 中 |
| ~~#003~~ | ~~工具可能无限递归~~ | ✅ 已修复 | 高 |
| ~~#004~~ | ~~工具重复注册~~ | ✅ 已修复 | 中 |
| ~~#005~~ | ~~缺少输入验证~~ | ✅ 已修复 | 中 |

---

## 📝 测试记录模板

```
测试日期: ________
测试人员: ________
环境: [ ] 开发 [ ] 测试 [ ] 生产

测试结果:
- 测试 1.1: [ ] 通过 [ ] 失败 - 备注: ____________
- 测试 1.2: [ ] 通过 [ ] 失败 - 备注: ____________
- 测试 2.1: [ ] 通过 [ ] 失败 - 备注: ____________
...

总结:
- 通过率: ____%
- 严重问题: ____个
- 一般问题: ____个
- 建议: ________________
```

---

## 🚀 自动化测试脚本

```python
# test_chat_engine_full.py
import pytest
import asyncio
from core.chat_engine import ChatEngine

class TestChatEngine:
    @pytest.fixture
    def chat_engine(self):
        return ChatEngine()
    
    @pytest.mark.asyncio
    async def test_basic_response(self, chat_engine):
        messages = [{"role": "user", "content": "你好"}]
        response = await chat_engine.generate_response(
            messages=messages,
            conversation_id="test",
            stream=False
        )
        assert response["role"] == "assistant"
        assert len(response["content"]) > 0
    
    @pytest.mark.asyncio
    async def test_tool_call(self, chat_engine):
        messages = [{"role": "user", "content": "现在几点"}]
        response = await chat_engine.generate_response(
            messages=messages,
            conversation_id="test",
            use_tools=True,
            stream=False
        )
        assert response["role"] == "assistant"
        assert "时间" in response["content"] or "点" in response["content"]
    
    @pytest.mark.asyncio
    async def test_empty_messages(self, chat_engine):
        response = await chat_engine.generate_response(
            messages=[],
            conversation_id="test",
            stream=False
        )
        assert "错误" in response["content"] or "不能为空" in response["content"]

# 运行: pytest test_chat_engine_full.py -v
```

---

**文档状态**: ✅ 完成  
**最后更新**: 2025-10-07

