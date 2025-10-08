# 🚀 快速开始测试 - 5分钟上手

**更新时间**: 2025年10月8日  
**适用对象**: 立即开始测试的开发者

---

## ⚡ 3步开始

### 1️⃣ 安装依赖（1分钟）

```bash
cd /Users/zhangjun/PycharmProjects/yychat
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### 2️⃣ 创建测试结构（1分钟）

```bash
chmod +x scripts/create_test_files.sh
./scripts/create_test_files.sh
```

### 3️⃣ 运行第一个测试（1分钟）

```bash
pytest test/test_environment.py -v
```

✅ **如果看到2个测试通过，说明环境OK！**

---

## 📅 立即开始Day 1

### 完整指南

阅读详细的Day 1指南：
```bash
cat docs/DAY1_EXECUTION_GUIDE.md
```

### 快速版本

**今天目标**: 完成ChatEngine基础测试

**时间**: 6小时

**步骤**:

1. **完成环境准备**（已完成✅）

2. **复制测试模板**:
```bash
# 从DAY1_EXECUTION_GUIDE.md复制测试代码
# 创建3个测试文件:
# - test/unit/test_chat_engine_init.py
# - test/unit/test_chat_engine_generate.py  
# - test/unit/test_chat_engine_base_interface.py
```

3. **运行测试**:
```bash
pytest test/unit/test_chat_engine_*.py -v
```

4. **查看覆盖率**:
```bash
chmod +x scripts/check_coverage.sh
./scripts/check_coverage.sh
```

---

## 📊 进度追踪

### 使用覆盖率脚本

```bash
# 每天运行一次
./scripts/check_coverage.sh

# 查看HTML报告
open htmlcov/index.html
```

### 手动检查

```bash
# 查看当前覆盖率
pytest --cov=core --cov=services --cov-report=term

# 只看核心模块
pytest --cov=core.chat_engine --cov-report=term
```

---

## 📝 测试编写模板

### 基础测试

```python
import pytest

def test_something():
    """测试某功能"""
    result = some_function()
    assert result is not None
```

### 异步测试

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """测试异步功能"""
    result = await async_function()
    assert result is not None
```

### 使用fixture

```python
import pytest

def test_with_fixture(test_conversation_id, test_messages):
    """使用fixture的测试"""
    assert test_conversation_id is not None
    assert len(test_messages) > 0
```

---

## 🎯 3周路线图

### Week 1: 核心引擎（目标40%）
- Day 1: ChatEngine基础 ✅ **← 今天从这里开始**
- Day 2: ChatEngine扩展
- Day 3: Mem0Proxy
- Day 4: ChatMemory
- Day 5: 总结

### Week 2: 关键模块（目标60%）
- Day 6-7: 工具系统
- Day 8: PersonalityManager
- Day 9: EngineManager
- Day 10: 总结

### Week 3: 辅助和集成（目标80%）
- Day 11-12: API测试
- Day 13: 辅助模块
- Day 14: 集成测试
- Day 15: 最终冲刺

---

## 🆘 常见问题

### Q: pytest找不到模块？
```bash
# 确保pytest.ini正确配置
cat pytest.ini

# 或设置PYTHONPATH
export PYTHONPATH=$PYTHONPATH:.
```

### Q: 测试失败怎么办？
```bash
# 查看详细错误
pytest test/xxx.py -v -s

# 只运行失败的测试
pytest --lf
```

### Q: 如何跳过某些测试？
```python
@pytest.mark.skip(reason="暂时跳过")
def test_something():
    pass
```

### Q: 覆盖率不准确？
```bash
# 清除缓存重新运行
rm -rf .pytest_cache __pycache__
pytest --cov=core --cov-report=html
```

---

## 📚 参考文档

### 详细指南
- `docs/TESTING_FOCUSED_PLAN.md` - 完整3周计划
- `docs/DAY1_EXECUTION_GUIDE.md` - Day 1详细指南
- `docs/PROJECT_COMPREHENSIVE_ANALYSIS.md` - 项目分析

### 快速命令

```bash
# 运行所有测试
pytest

# 只运行unit测试
pytest test/unit/ -v

# 查看覆盖率
pytest --cov

# 生成HTML报告
pytest --cov --cov-report=html

# 只测试某个模块
pytest test/unit/test_chat_engine.py

# 只测试某个函数
pytest test/unit/test_chat_engine.py::test_singleton_pattern
```

---

## ✅ Day 1 检查清单

开始前：
- [ ] 安装pytest和依赖
- [ ] 创建测试目录结构
- [ ] 运行环境验证测试

编写测试：
- [ ] test_chat_engine_init.py (7个测试)
- [ ] test_chat_engine_generate.py (9个测试)
- [ ] test_chat_engine_base_interface.py (9个测试)

完成后：
- [ ] 所有测试通过
- [ ] 覆盖率≥15%
- [ ] 提交代码

---

## 🎉 开始你的测试之旅！

**现在就开始**:

```bash
# 1. 确认环境
pytest --version

# 2. 创建结构
./scripts/create_test_files.sh

# 3. 开始编写
# 打开 docs/DAY1_EXECUTION_GUIDE.md
# 复制测试代码到相应文件

# 4. 运行测试
pytest -v

# 5. 查看进度
./scripts/check_coverage.sh
```

**记住**: 每天进步一点，坚持3周，80%覆盖率手到擒来！💪

---

**有问题？** 查看详细文档或调整计划！

**准备好了？** 打开 `docs/DAY1_EXECUTION_GUIDE.md` 开始Day 1！🚀

