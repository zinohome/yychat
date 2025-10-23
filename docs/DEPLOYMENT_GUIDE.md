# YYChat 部署指南

## 📋 概述

本指南将帮助您使用Docker部署YYChat项目，所有硬编码参数已替换为可配置的环境变量。

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo-url>
cd yychat

# 复制环境变量模板
cp env.example .env
```

### 2. 配置环境变量

编辑 `.env` 文件，配置必要的参数：

```bash
# 必须配置的API密钥
OPENAI_API_KEY=your-openai-api-key-here
YYCHAT_API_KEY=your-yychat-api-key-here

# 可选：外部服务API密钥
TAVILY_API_KEY=your-tavily-api-key-here
MEM0_API_KEY=your-mem0-api-key-here
```

### 3. 使用Docker Compose部署

```bash
# 复制Docker Compose配置
cp docker-compose.example.yml docker-compose.yml

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f yychat
```

## 🔧 配置说明

### 核心配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `OPENAI_API_KEY` | - | OpenAI API密钥（必需） |
| `YYCHAT_API_KEY` | yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4 | YYChat API密钥 |
| `SERVER_HOST` | 0.0.0.0 | 服务器监听地址 |
| `SERVER_PORT` | 8000 | 服务器端口 |

### AI模型配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `OPENAI_MODEL` | gpt-4.1 | OpenAI模型 |
| `OPENAI_BASE_URL` | https://api.openai.com/v1 | OpenAI API基础URL |
| `OPENAI_TEMPERATURE` | 0.75 | 模型温度 |
| `OPENAI_MAX_TOKENS` | 16384 | 最大token数 |

### 音频处理配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `AUDIO_MAX_SIZE_MB` | 25 | 音频文件最大大小（MB） |
| `TEXT_MAX_LENGTH` | 4096 | 文本最大长度 |
| `DEFAULT_WHISPER_MODEL` | whisper-1 | 默认语音转文本模型 |
| `DEFAULT_TTS_MODEL` | tts-1 | 默认文本转语音模型 |
| `DEFAULT_VOICE` | shimmer | 默认语音 |

### 实时语音配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `REALTIME_VOICE_ENABLED` | true | 启用实时语音 |
| `REALTIME_VOICE_MODEL` | gpt-4o-realtime-preview-2024-12-17 | 实时语音模型 |
| `REALTIME_VOICE_SAMPLE_RATE` | 24000 | 音频采样率 |
| `REALTIME_VOICE_CHANNELS` | 1 | 音频声道数 |

### 性能优化配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `OPENAI_API_TIMEOUT` | 30.0 | OpenAI API超时时间 |
| `MAX_CONNECTIONS` | 100 | 最大连接数 |
| `AUDIO_PROCESSOR_MAX_WORKERS` | 4 | 音频处理器最大工作线程数 |
| `CHUNK_SPLIT_THRESHOLD` | 100 | 流式响应分块阈值 |

### 缓存配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `USE_REDIS_CACHE` | false | 启用Redis缓存 |
| `REDIS_HOST` | localhost | Redis主机 |
| `REDIS_PORT` | 6379 | Redis端口 |
| `MEMORY_CACHE_MAXSIZE` | 1000 | 内存缓存最大条目数 |

## 🐳 Docker部署选项

### 选项1：基础部署（无Redis）

```bash
docker-compose up -d yychat
```

### 选项2：完整部署（包含Redis）

```bash
# 启用Redis缓存
echo "USE_REDIS_CACHE=true" >> .env
echo "REDIS_PASSWORD=your-redis-password" >> .env

# 启动所有服务
docker-compose --profile redis up -d
```

### 选项3：生产环境部署

```bash
# 使用生产环境配置
cp env.example .env.production

# 编辑生产环境配置
vim .env.production

# 使用生产环境配置启动
docker-compose --env-file .env.production up -d
```

## 🔍 监控和调试

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查API文档
curl http://localhost:8000/docs
```

### 日志查看

```bash
# 查看实时日志
docker-compose logs -f yychat

# 查看性能监控
docker-compose logs yychat | grep "PERF"

# 查看错误日志
docker-compose logs yychat | grep "ERROR"
```

### 性能监控

```bash
# 查看性能统计
curl http://localhost:8000/v1/performance/stats

# 查看最近性能数据
curl http://localhost:8000/v1/performance/recent?count=10
```

## 🛠️ 自定义配置

### 修改默认语音

```bash
# 在.env文件中设置
DEFAULT_VOICE=alloy  # 可选: alloy, echo, fable, onyx, nova, shimmer
```

### 调整音频处理参数

```bash
# 音频文件大小限制
AUDIO_MAX_SIZE_MB=50

# 音频压缩质量
AUDIO_COMPRESSION_QUALITY=80

# 音频块大小
AUDIO_CHUNK_SIZE_KB=64
```

### 调整超时设置

```bash
# 连接超时
CONNECTION_TIMEOUT=60

# WebSocket超时
WEBSOCKET_RECEIVE_TIMEOUT=10.0

# 实时语音超时
REALTIME_CONNECTION_TIMEOUT=60
```

## 🔧 故障排除

### 常见问题

1. **服务启动失败**
   ```bash
   # 检查环境变量
   docker-compose config
   
   # 查看详细错误
   docker-compose logs yychat
   ```

2. **API密钥错误**
   ```bash
   # 验证API密钥配置
   grep -E "OPENAI_API_KEY|YYCHAT_API_KEY" .env
   ```

3. **音频处理失败**
   ```bash
   # 检查音频配置
   curl -X POST http://localhost:8000/v1/audio/test
   ```

### 性能优化

1. **启用Redis缓存**
   ```bash
   USE_REDIS_CACHE=true
   REDIS_HOST=redis
   ```

2. **调整工作线程数**
   ```bash
   AUDIO_PROCESSOR_MAX_WORKERS=8
   ```

3. **优化内存使用**
   ```bash
   MEMORY_CACHE_MAXSIZE=2000
   AUDIO_BUFFER_SIZE=200
   ```

## 📊 生产环境建议

### 安全配置

```bash
# 使用强密码
YYCHAT_API_KEY=your-strong-api-key-here
REDIS_PASSWORD=your-strong-redis-password

# 启用SSL验证
VERIFY_SSL=true
```

### 性能配置

```bash
# 生产环境优化
OPENAI_API_TIMEOUT=60.0
MAX_CONNECTIONS=200
AUDIO_PROCESSOR_MAX_WORKERS=8
ENABLE_PERFORMANCE_MONITOR=true
```

### 监控配置

```bash
# 启用详细监控
PERFORMANCE_LOG_ENABLED=true
PERFORMANCE_SAMPLING_RATE=1.0
VERBOSE_LOGGING=true
```

## 📚 更多信息

- [API文档](http://localhost:8000/docs)
- [性能监控](http://localhost:8000/v1/performance/stats)
- [健康检查](http://localhost:8000/health)

## 🆘 支持

如果遇到问题，请检查：

1. 环境变量配置是否正确
2. API密钥是否有效
3. 网络连接是否正常
4. 日志中的错误信息

更多帮助请参考项目文档或提交Issue。
