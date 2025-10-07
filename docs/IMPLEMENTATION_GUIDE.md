# YYChat 优化实施指南

本指南提供了分步骤实施优化方案的详细说明。

---

## 📋 准备工作

### 1. 备份当前环境

```bash
# 备份代码
git add .
git commit -m "备份：优化前的状态"
git tag v0.1.0-before-optimization

# 备份数据
cp -r chroma_db chroma_db.backup
cp -r logs logs.backup
```

### 2. 性能基准测试

```bash
# 创建测试脚本
cat > test_performance.sh << 'EOF'
#!/bin/bash
echo "=== 性能基准测试 ==="
echo "测试时间: $(date)"

# 测试10次请求，记录时间
for i in {1..10}; do
  echo -n "Request $i: "
  time curl -s -X POST http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $YYCHAT_API_KEY" \
    -d '{
      "messages": [{"role": "user", "content": "你好"}],
      "stream": false
    }' > /dev/null
done
EOF

chmod +x test_performance.sh

# 运行基准测试
./test_performance.sh > baseline_performance.txt
```

---

## 🚀 阶段1: 快速优化 (1-2小时)

### 步骤1.1: 降低Memory超时 (5分钟)

```bash
# 创建或修改 .env 文件
cat > .env << 'EOF'
# 从示例配置复制基础配置
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# 关键优化配置
MEMORY_RETRIEVAL_TIMEOUT=0.5
MEMORY_ENABLE_CACHE=true
MEMORY_CACHE_TTL=300
MEMORY_CACHE_SIZE=100
ENABLE_MEMORY_RETRIEVAL=true
EOF

# 重启服务
./start_with_venv.sh
```

### 步骤1.2: 安装优化依赖 (2分钟)

```bash
# 添加 cachetools
pip install cachetools>=5.3.1

# 更新 requirements.txt
echo "cachetools>=5.3.1" >> requirements.txt
```

### 步骤1.3: 应用Memory缓存 (20分钟)

#### 方案A: 直接替换文件 (推荐)

```bash
# 备份原文件
cp core/chat_memory.py core/chat_memory.py.backup

# 使用优化版本
cp core/chat_memory_optimized.py core/chat_memory.py
```

#### 方案B: 手动修改 (如果需要保留自定义修改)

在 `core/chat_memory.py` 顶部添加:

```python
from cachetools import TTLCache
import hashlib
```

在 `ChatMemory.__init__` 中添加:

```python
# 添加缓存 (5分钟过期，最多100条)
self._memory_cache = TTLCache(maxsize=100, ttl=300)
```

修改 `get_relevant_memory` 方法，添加缓存逻辑（参考 `chat_memory_optimized.py`）。

### 步骤1.4: 应用Personality缓存 (10分钟)

编辑 `core/personality_manager.py`:

```python
# 在文件顶部添加
from functools import lru_cache

# 修改 get_personality 方法
@lru_cache(maxsize=32)
def get_personality(self, personality_id: str):
    # 保持原有代码不变
    ...
```

### 步骤1.5: 应用Tool Schema缓存 (10分钟)

编辑 `services/tools/registry.py`:

```python
class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self._schema_cache = None  # 新增
        self._schema_dirty = False  # 新增
    
    def register(self, tool_class: Type[Tool]):
        # ... 原有代码 ...
        self._schema_dirty = True  # 新增：标记缓存失效
    
    def get_functions_schema(self) -> List[Dict]:
        # 检查缓存
        if self._schema_cache is not None and not self._schema_dirty:
            return self._schema_cache
        
        # 重建缓存
        self._schema_cache = [
            tool.to_function_call_schema()
            for tool in self._tools.values()
        ]
        self._schema_dirty = False
        return self._schema_cache
```

### 步骤1.6: 添加Memory检索开关 (5分钟)

编辑 `config/config.py`:

```python
class Config:
    # ... 现有配置 ...
    
    # 添加
    ENABLE_MEMORY_RETRIEVAL = os.getenv("ENABLE_MEMORY_RETRIEVAL", "true").lower() == "true"
```

编辑 `core/chat_engine.py`，在Memory检索处添加条件:

```python
# 原代码
memory_section = self.chat_memory.get_relevant_memory(...)

# 修改为
memory_section = ""
if self.config.ENABLE_MEMORY_RETRIEVAL:
    memory_section = self.chat_memory.get_relevant_memory(...)
    log.debug(f"检索到相关记忆 {len(memory_section)} 条")
else:
    log.debug("Memory检索已禁用")
```

### 步骤1.7: 重启并测试 (10分钟)

```bash
# 重启服务
./start_with_venv.sh

# 等待服务启动
sleep 5

# 运行性能测试
./test_performance.sh > optimized_performance.txt

# 对比结果
echo "=== 优化前后对比 ==="
echo "优化前:"
grep "real" baseline_performance.txt | awk '{sum+=$2; count++} END {print "平均:", sum/count "s"}'

echo "优化后:"
grep "real" optimized_performance.txt | awk '{sum+=$2; count++} END {print "平均:", sum/count "s"}'
```

---

## 📊 阶段2: 验证和调优 (1-2小时)

### 步骤2.1: 功能验证

```bash
# 测试基本聊天
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $YYCHAT_API_KEY" \
  -d '{
    "messages": [{"role": "user", "content": "你好，介绍一下自己"}],
    "stream": false
  }'

# 测试流式响应
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $YYCHAT_API_KEY" \
  -d '{
    "messages": [{"role": "user", "content": "1+1等于几？"}],
    "use_tools": true,
    "stream": true
  }'

# 测试Memory
curl -X GET http://localhost:8000/v1/conversations/test_user/memory \
  -H "Authorization: Bearer $YYCHAT_API_KEY"
```

### 步骤2.2: 压力测试

```bash
# 安装 wrk (如果没有)
# macOS: brew install wrk
# Linux: apt-get install wrk

# 创建测试脚本
cat > test_load.lua << 'EOF'
wrk.method = "POST"
wrk.headers["Content-Type"] = "application/json"
wrk.headers["Authorization"] = "Bearer " .. os.getenv("YYCHAT_API_KEY")
wrk.body = '{"messages":[{"role":"user","content":"你好"}],"stream":false}'
EOF

# 运行压力测试
wrk -t4 -c50 -d30s --latency \
  -s test_load.lua \
  http://localhost:8000/v1/chat/completions

# 查看结果，重点关注:
# - Latency (延迟)
# - Requests/sec (吞吐量)
# - 99th percentile (P99延迟)
```

### 步骤2.3: 缓存命中率监控

编辑代码添加监控日志:

```python
# core/chat_memory_optimized.py
def get_relevant_memory(...):
    cache_key = self._get_cache_key(conversation_id, query, limit)
    
    if cache_key in self._memory_cache:
        log.info(f"[CACHE_HIT] Memory缓存命中")  # 添加
        return self._memory_cache[cache_key]
    
    log.info(f"[CACHE_MISS] Memory缓存未命中")  # 添加
    # ... 原有逻辑
```

查看缓存命中率:

```bash
# 运行一段时间后
grep "CACHE_HIT\|CACHE_MISS" logs/app.log | sort | uniq -c

# 计算命中率
# 命中率 = CACHE_HIT / (CACHE_HIT + CACHE_MISS) * 100%
```

---

## 🔧 阶段3: 高级优化 (可选)

### 步骤3.1: 实现性能监控API

创建 `utils/performance.py`:

```python
from dataclasses import dataclass, asdict
from typing import Dict, List
import time
import statistics

@dataclass
class PerformanceMetrics:
    memory_retrieval_time: float = 0.0
    personality_apply_time: float = 0.0
    tool_schema_build_time: float = 0.0
    openai_api_time: float = 0.0
    first_chunk_time: float = 0.0
    total_time: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)

class PerformanceMonitor:
    def __init__(self):
        self._metrics_history: List[PerformanceMetrics] = []
        self._max_history = 1000
    
    def record(self, metrics: PerformanceMetrics):
        self._metrics_history.append(metrics)
        if len(self._metrics_history) > self._max_history:
            self._metrics_history.pop(0)
    
    def get_statistics(self) -> Dict:
        if not self._metrics_history:
            return {"message": "No data"}
        
        total_times = [m.total_time for m in self._metrics_history]
        memory_times = [m.memory_retrieval_time for m in self._metrics_history]
        
        return {
            "total_requests": len(self._metrics_history),
            "avg_total_time": f"{statistics.mean(total_times):.3f}s",
            "avg_memory_time": f"{statistics.mean(memory_times):.3f}s",
            "p50_total_time": f"{statistics.median(total_times):.3f}s",
            "p95_total_time": f"{sorted(total_times)[int(len(total_times)*0.95)]:.3f}s",
            "p99_total_time": f"{sorted(total_times)[int(len(total_times)*0.99)]:.3f}s",
        }

# 全局实例
performance_monitor = PerformanceMonitor()
```

在 `app.py` 添加API:

```python
from utils.performance import performance_monitor

@app.get("/v1/performance/stats", tags=["Monitoring"])
async def get_performance_stats(api_key: str = Depends(verify_api_key)):
    """获取性能统计"""
    return performance_monitor.get_statistics()
```

### 步骤3.2: 在chat_engine中记录性能指标

```python
# core/chat_engine.py
from utils.performance import performance_monitor, PerformanceMetrics

async def generate_response(...):
    metrics = PerformanceMetrics()
    start_time = time.time()
    
    # Memory检索
    mem_start = time.time()
    if self.config.ENABLE_MEMORY_RETRIEVAL:
        memory_section = ...
    metrics.memory_retrieval_time = time.time() - mem_start
    
    # ... 其他处理 ...
    
    metrics.total_time = time.time() - start_time
    performance_monitor.record(metrics)
```

---

## 📈 成功标准

### 性能指标

| 指标 | 目标值 | 验收方法 |
|------|--------|----------|
| 平均响应时间 | < 0.8s | `./test_performance.sh` |
| P95响应时间 | < 1.5s | wrk压力测试 |
| P99响应时间 | < 2.0s | wrk压力测试 |
| 缓存命中率 | > 60% | 日志分析 |
| 吞吐量 | > 50 req/s | wrk压力测试 |

### 功能验证

- [ ] 基本聊天功能正常
- [ ] 流式响应正常
- [ ] 工具调用正常
- [ ] Memory检索正常
- [ ] Personality应用正常
- [ ] 无新增错误或警告

---

## 🔄 回滚方案

如果优化后出现问题:

```bash
# 1. 停止服务
pkill -f "uvicorn app:app"

# 2. 恢复代码
git checkout core/chat_memory.py
git checkout core/personality_manager.py
git checkout services/tools/registry.py
git checkout config/config.py

# 3. 恢复配置
rm .env
# 使用原有的 .env 配置

# 4. 重启服务
./start_with_venv.sh
```

---

## 📝 文档更新

完成优化后，更新以下文档:

1. `README.md` - 添加性能优化说明
2. `CHANGELOG.md` - 记录本次优化
3. `.env.example` - 更新推荐配置

---

## 🎯 下一步

完成快速优化后，可以考虑:

1. **统一双引擎架构** - 合并 `chat_engine.py` 和 `mem0_proxy.py`
2. **添加分布式缓存** - 使用Redis替代本地缓存
3. **实现请求队列** - 使用Celery处理异步任务
4. **增加监控Dashboard** - 使用Grafana可视化性能指标

---

**预计总耗时**: 2-4小时  
**难度等级**: 中等  
**风险等级**: 低 (可随时回滚)

