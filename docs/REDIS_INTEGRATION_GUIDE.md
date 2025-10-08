# 📦 Redis集成指南

**日期**: 2025年10月8日  
**阶段**: 中期优化 - Phase 2  
**状态**: ✅ 已完成

---

## 📋 概述

本指南介绍如何在YYChat项目中使用Redis作为分布式缓存系统，替代内存缓存。

---

## 🎯 为什么需要Redis？

### 当前问题（内存缓存）
- ❌ **服务重启丢失**: 缓存数据在内存中，重启服务后全部丢失
- ❌ **单实例限制**: 多个服务实例无法共享缓存
- ❌ **不支持分布式**: 无法横向扩展
- ❌ **数据不持久**: 无法查看历史缓存数据

### Redis优势
- ✅ **持久化存储**: 数据不会因重启丢失
- ✅ **分布式共享**: 多实例共享同一Redis
- ✅ **高性能**: Redis本身就是为缓存设计
- ✅ **可扩展**: 支持集群部署

---

## 🔧 安装Redis

### macOS
```bash
# 使用Homebrew安装
brew install redis

# 启动Redis服务
brew services start redis

# 验证安装
redis-cli ping
# 应该返回: PONG
```

### Linux (Ubuntu/Debian)
```bash
# 安装Redis
sudo apt-get update
sudo apt-get install redis-server

# 启动Redis
sudo systemctl start redis
sudo systemctl enable redis

# 验证
redis-cli ping
```

### Docker
```bash
# 运行Redis容器
docker run -d \
  --name yychat-redis \
  -p 6379:6379 \
  redis:latest

# 验证
docker exec -it yychat-redis redis-cli ping
```

---

## 📦 安装Python依赖

```bash
cd /Users/zhangjun/PycharmProjects/yychat

# 安装Redis客户端
pip install redis>=5.0.0 hiredis>=2.2.3

# 或者使用requirements.txt
pip install -r requirements.txt
```

---

## ⚙️ 配置

### 1. 环境变量 (.env)

```bash
# ===== Redis缓存配置 =====
# 是否使用Redis缓存（false=使用内存缓存）
USE_REDIS_CACHE=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_TTL=1800

# 内存缓存配置（Redis降级方案）
MEMORY_CACHE_MAXSIZE=1000
MEMORY_CACHE_TTL=1800
```

### 2. 配置说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `USE_REDIS_CACHE` | 是否使用Redis缓存 | `false` |
| `REDIS_HOST` | Redis服务器地址 | `localhost` |
| `REDIS_PORT` | Redis端口 | `6379` |
| `REDIS_DB` | Redis数据库编号 | `0` |
| `REDIS_PASSWORD` | Redis密码（无密码留空） | `` |
| `REDIS_TTL` | 缓存过期时间（秒） | `1800` (30分钟) |
| `MEMORY_CACHE_MAXSIZE` | 内存缓存最大条目数 | `1000` |
| `MEMORY_CACHE_TTL` | 内存缓存过期时间（秒） | `1800` |

---

## 🚀 使用方法

### 1. 启用Redis缓存

```bash
# 编辑 .env 文件
USE_REDIS_CACHE=true

# 重启服务
./start_with_venv.sh
```

### 2. 使用内存缓存（默认）

```bash
# 编辑 .env 文件
USE_REDIS_CACHE=false

# 重启服务
./start_with_venv.sh
```

### 3. 代码中使用缓存

```python
from utils.cache import get_cache

# 获取缓存实例（自动根据配置返回Memory或Redis）
cache = get_cache()

# 设置缓存
cache.set("my_key", {"data": "value"}, ttl=3600)

# 获取缓存
value = cache.get("my_key")

# 删除缓存
cache.delete("my_key")

# 清空所有缓存
cache.clear()

# 检查key是否存在
if cache.exists("my_key"):
    print("Key exists!")
```

---

## 📊 缓存架构

### 缓存抽象层

```
┌─────────────────┐
│  Application    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CacheBackend   │ ← 抽象接口
│  (ABC)          │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐  ┌──────┐
│Memory│  │Redis │
│Cache │  │Cache │
└──────┘  └──────┘
```

### 统一接口

```python
class CacheBackend(ABC):
    def get(key: str) -> Any
    def set(key: str, value: Any, ttl: int)
    def delete(key: str)
    def clear()
    def exists(key: str) -> bool
```

---

## 🔍 监控和调试

### 1. 查看Redis状态

```bash
# 连接Redis CLI
redis-cli

# 查看所有key
127.0.0.1:6379> KEYS *

# 查看某个key的值
127.0.0.1:6379> GET "your_key"

# 查看key的过期时间
127.0.0.1:6379> TTL "your_key"

# 查看Redis信息
127.0.0.1:6379> INFO
```

### 2. 查看内存使用

```bash
redis-cli INFO memory
```

### 3. 监控Redis命令

```bash
redis-cli MONITOR
```

---

## 🧪 测试

### 1. 创建测试脚本

```python
# test_redis_cache.py
from utils.cache import get_cache
from config.config import get_config
import time

config = get_config()

def test_cache():
    print(f"使用缓存: {config.USE_REDIS_CACHE and 'Redis' or 'Memory'}")
    
    cache = get_cache()
    print(f"缓存后端: {cache.get_name()}")
    
    # 测试set/get
    cache.set("test_key", {"data": "hello world"}, ttl=60)
    value = cache.get("test_key")
    print(f"✅ Set/Get: {value}")
    
    # 测试exists
    exists = cache.exists("test_key")
    print(f"✅ Exists: {exists}")
    
    # 测试delete
    cache.delete("test_key")
    value = cache.get("test_key")
    print(f"✅ Delete: {value is None}")
    
    print("✅ 所有测试通过！")

if __name__ == "__main__":
    test_cache()
```

### 2. 运行测试

```bash
# 测试内存缓存
USE_REDIS_CACHE=false python test_redis_cache.py

# 测试Redis缓存
USE_REDIS_CACHE=true python test_redis_cache.py
```

---

## 🔄 迁移Memory缓存到Redis

### 1. 更新chat_memory.py

已自动集成，无需手动修改。`AsyncChatMemory` 类内部使用 `get_cache()` 获取缓存实例。

### 2. 缓存Key规范

```python
from utils.cache import hash_key

# Memory检索缓存
memory_key = hash_key("memory", conversation_id=conv_id, query=query, limit=limit)

# 性能监控数据
perf_key = hash_key("performance", request_id=req_id)

# 人格数据
personality_key = hash_key("personality", personality_id=pid)
```

---

## ⚠️ 注意事项

### 1. Redis连接失败降级

如果Redis连接失败，系统会自动降级到内存缓存：

```python
try:
    cache = RedisCache()
except Exception as e:
    log.warning("⚠️ Redis连接失败，降级到内存缓存")
    cache = MemoryCache()
```

### 2. 数据序列化

使用 `pickle` 序列化数据，确保数据类型支持pickle。

### 3. Redis清空数据

```bash
# 清空当前DB
redis-cli FLUSHDB

# 清空所有DB（慎用！）
redis-cli FLUSHALL
```

### 4. Redis安全

生产环境建议：
- 设置Redis密码
- 限制远程访问
- 使用防火墙规则
- 定期备份数据

---

## 📈 性能对比

| 操作 | 内存缓存 | Redis缓存 | 说明 |
|------|----------|-----------|------|
| Get | ~0.001ms | ~0.5-1ms | Redis有网络开销 |
| Set | ~0.001ms | ~0.5-1ms | Redis有网络开销 |
| 持久化 | ❌ | ✅ | Redis数据持久化 |
| 分布式 | ❌ | ✅ | Redis支持多实例共享 |
| 重启恢复 | ❌ | ✅ | Redis数据不丢失 |

### 建议

- **单实例部署**: 使用内存缓存（性能更好）
- **多实例部署**: 必须使用Redis（共享缓存）
- **生产环境**: 推荐使用Redis（数据持久化）

---

## 🔧 故障排查

### 问题1: 无法连接Redis

```bash
# 检查Redis服务状态
redis-cli ping

# 检查端口
netstat -an | grep 6379

# 检查Redis日志
tail -f /usr/local/var/log/redis.log  # macOS
tail -f /var/log/redis/redis-server.log  # Linux
```

### 问题2: 缓存未生效

```bash
# 查看日志确认使用的缓存后端
tail -f logs/app.log | grep "Cache"

# 应该看到类似输出:
# ✅ RedisCache初始化完成 (localhost:6379)
# 或
# ✅ MemoryCache初始化完成 (maxsize=1000, ttl=1800s)
```

### 问题3: Redis内存不足

```bash
# 查看内存使用
redis-cli INFO memory

# 设置内存限制
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

## 📚 相关文档

- [中期优化计划](./MID_TERM_OPTIMIZATION_PLAN.md)
- [统一引擎架构](./UNIFIED_ENGINE_ARCHITECTURE.md)
- [优化总结](./OPTIMIZATION_SUMMARY.md)

---

## ✅ 集成完成清单

- [x] 安装Redis依赖 (redis, hiredis)
- [x] 创建缓存抽象层 (utils/cache.py)
- [x] 实现MemoryCache后端
- [x] 实现RedisCache后端
- [x] 添加配置支持 (config.py, .env)
- [x] 集成到chat_memory
- [x] 创建测试脚本
- [x] 编写文档

---

**实施完成时间**: 2025年10月8日  
**状态**: ✅ 可用（默认使用内存缓存）  
**下一步**: 根据需要切换到Redis缓存

