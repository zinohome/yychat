# ❓ 性能监控常见问题

**日期**: 2025年10月7日

---

## Q1: 为什么性能API返回空数据？

### 问题描述
在Swagger Docs中执行：
```bash
GET /v1/performance/recent?count=2
```

返回：
```json
{
  "count": 0,
  "metrics": []
}
```

### 原因分析

**主要原因**：服务重启后，性能数据被清空

性能监控数据存储在**内存中**（使用`deque`），有以下特点：
1. ✅ **优点**: 访问速度快，无需数据库
2. ❌ **缺点**: 服务重启后数据丢失
3. ⚠️ **现象**: 重启后需要有新请求才会有数据

### 解决方案

#### 方案1: 发送测试请求（立即生效）
```bash
# 发送几个测试请求生成数据
curl -X POST http://192.168.66.209:9800/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4" \
  -d '{"messages": [{"role": "user", "content": "测试"}], "stream": false}'

# 再查询
curl http://192.168.66.209:9800/v1/performance/stats \
  -H "Authorization: Bearer yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4"
```

#### 方案2: 持久化存储（需要开发）
```python
# utils/performance.py
import json
import os

class PerformanceMonitor:
    def __init__(self):
        # ...
        self._load_from_file()  # 启动时加载历史数据
    
    def record(self, metrics: PerformanceMetrics):
        # ...
        self._save_to_file()  # 定期保存到文件
    
    def _save_to_file(self):
        """保存到文件"""
        with open('logs/performance_metrics.json', 'w') as f:
            json.dump([m.to_dict() for m in self._metrics_history], f)
    
    def _load_from_file(self):
        """从文件加载"""
        if os.path.exists('logs/performance_metrics.json'):
            with open('logs/performance_metrics.json', 'r') as f:
                # 加载历史数据
                pass
```

---

## Q2: 为什么响应时间这么慢（4秒）？

### 实际数据
```json
{
  "total_time": {
    "avg": "4.082s",
    "min": "3.164s",
    "max": "4.669s"
  },
  "memory_retrieval": {
    "avg": "0.501s",
    "min": "0.500s",
    "max": "0.502s"
  }
}
```

### 问题分析

1. **Memory检索达到超时上限** ⚠️
   - 设置: 0.3s (优化后)
   - 实际: 0.5s (仍然超时)
   - **可能原因**: 配置未生效或Memory本身很慢

2. **总响应时间很长** ⚠️
   - 4秒响应时间明显超过预期
   - Memory只占0.5s，其他3.5s在哪？
   - **需要查看**: OpenAI API时间

### 解决方案

#### 立即检查
```bash
# 1. 验证配置是否生效
grep MEMORY_RETRIEVAL_TIMEOUT .env

# 2. 查看详细日志
tail -f logs/app.log | grep -E "PERF|Memory|OpenAI"

# 3. 查看最近请求详情
curl http://192.168.66.209:9800/v1/performance/recent?count=3 \
  -H "Authorization: Bearer yk-xxx"
```

#### 可能的问题

**问题1: Memory超时配置未生效**
```bash
# 检查
grep MEMORY_RETRIEVAL_TIMEOUT .env
# 应该显示: MEMORY_RETRIEVAL_TIMEOUT="0.3"

# 如果不是0.3，说明配置未生效
# 解决: 重启服务
./start_with_venv.sh
```

**问题2: OpenAI API很慢**
```bash
# 查看OpenAI时间占比
# 在性能数据中查看 openai_api_time
# 如果很大，说明OpenAI慢，不是Memory的问题
```

---

## Q3: 性能日志为什么看不到？

### 问题描述
查看日志没有 `[PERF]` 输出：
```bash
tail -f logs/app.log | grep PERF
# 没有输出
```

### 原因分析

**可能原因1**: `PERFORMANCE_LOG_ENABLED` 被禁用

检查配置：
```bash
grep PERFORMANCE_LOG_ENABLED .env
```

如果没有这个配置或值为`false`，日志不会输出。

**可能原因2**: 使用了流式响应

流式响应的性能指标记录方式不同，可能不会立即输出日志。

### 解决方案

#### 启用性能日志
```bash
# 添加到 .env
echo "PERFORMANCE_LOG_ENABLED=true" >> .env

# 重启服务
./start_with_venv.sh
```

#### 验证
```bash
# 发送请求
curl -X POST http://192.168.66.209:9800/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer yk-xxx" \
  -d '{"messages": [{"role": "user", "content": "测试"}], "stream": false}'

# 查看日志（应该有 [PERF] 输出）
tail -5 logs/app.log | grep PERF
```

---

## Q4: 缓存命中率为什么是0%？

### 实际数据
```json
{
  "cache": {
    "hit_count": 0,
    "miss_count": 4,
    "hit_rate": "0.0%"
  }
}
```

### 原因分析

**原因**: 每次请求的内容都不同

缓存基于查询内容的hash：
- `"测试1"` → cache_key_1
- `"测试2"` → cache_key_2
- `"测试3"` → cache_key_3

都不同，所以都是miss。

### 验证缓存

**发送相同内容3次**：
```bash
for i in {1..3}; do
  curl -X POST http://192.168.66.209:9800/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer yk-xxx" \
    -d '{"messages": [{"role": "user", "content": "今天天气怎么样？"}], "stream": false}'
  sleep 1
done

# 查看缓存命中率（应该 > 60%）
curl http://192.168.66.209:9800/v1/performance/stats \
  -H "Authorization: Bearer yk-xxx" | grep hit_rate
```

**预期结果**：
- 第1次: miss
- 第2次: **hit** ✅
- 第3次: **hit** ✅
- 命中率: 66.7%

---

## Q5: 如何清除性能数据？

### API方式
```bash
curl -X DELETE http://192.168.66.209:9800/v1/performance/clear \
  -H "Authorization: Bearer yk-xxx"
```

### 重启服务方式
```bash
# 重启服务会自动清空（内存数据）
./start_with_venv.sh
```

---

## Q6: 性能监控对系统有影响吗？

### 影响分析

**CPU开销**: < 0.001%  
**内存占用**: ~200KB (1000条记录)  
**延迟增加**: ~0.4ms (0.06%)

**结论**: 影响可忽略不计 ✅

详见: `docs/PERFORMANCE_MONITOR_IMPACT_ANALYSIS.md`

---

## Q7: 怎么看某个特定时间段的性能？

### 当前限制
性能监控目前只保留最近的数据（默认1000条），不支持时间范围查询。

### 解决方案

#### 方案1: 使用统计API
```bash
# 查看所有数据的统计（包含时间范围）
curl http://192.168.66.209:9800/v1/performance/stats \
  -H "Authorization: Bearer yk-xxx"

# 返回包含 time_range:
{
  "summary": {
    "time_range": {
      "from": "2025-10-07 21:03:41",
      "to": "2025-10-07 21:05:21"
    }
  }
}
```

#### 方案2: 导出数据分析
```bash
# 获取最近所有数据
curl http://192.168.66.209:9800/v1/performance/recent?count=1000 \
  -H "Authorization: Bearer yk-xxx" > performance_data.json

# 用Python分析
python3 << EOF
import json
with open('performance_data.json') as f:
    data = json.load(f)
    # 按时间过滤、分析...
EOF
```

---

## 📋 快速诊断清单

遇到问题时，按顺序检查：

1. ✅ **服务是否重启过？**
   - 是 → 发送测试请求生成数据

2. ✅ **配置是否正确？**
   ```bash
   grep ENABLE_PERFORMANCE_MONITOR .env
   grep PERFORMANCE_LOG_ENABLED .env
   ```

3. ✅ **是否有请求流量？**
   - 无 → 发送测试请求

4. ✅ **日志是否正常？**
   ```bash
   tail -f logs/app.log | grep PERF
   ```

5. ✅ **API是否可访问？**
   ```bash
   curl http://192.168.66.209:9800/v1/performance/stats \
     -H "Authorization: Bearer yk-xxx"
   ```

---

## 🎯 最佳实践

### 日常监控
```bash
# 每天查看一次统计
curl http://192.168.66.209:9800/v1/performance/stats \
  -H "Authorization: Bearer $YYCHAT_API_KEY"
```

### 问题诊断
```bash
# 查看最近的详细数据
curl http://192.168.66.209:9800/v1/performance/recent?count=10 \
  -H "Authorization: Bearer $YYCHAT_API_KEY"
```

### 测试缓存
```bash
# 发送相同请求验证缓存
for i in {1..3}; do
  curl -X POST http://192.168.66.209:9800/v1/chat/completions \
    -H "Authorization: Bearer $YYCHAT_API_KEY" \
    -d '{"messages": [{"role": "user", "content": "测试缓存"}]}'
  sleep 1
done
```

---

**相关文档**:
- `docs/PERFORMANCE_MONITOR_IMPACT_ANALYSIS.md`
- `docs/PERFORMANCE_MONITORING_SUCCESS.md`
- `docs/PERFORMANCE_CONFIG_COMPLETE.md`

