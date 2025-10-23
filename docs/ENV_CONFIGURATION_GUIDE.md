# YYChat 环境变量配置指南

## 📋 配置文件说明

YYChat 项目提供了三个环境变量配置文件，适用于不同的使用场景：

### 1. `env.example` - 原始配置文件
- **用途**: 项目原有的环境变量配置
- **特点**: 包含基础配置项
- **适用场景**: 了解项目基本配置

### 2. `env.example.full` - 完整配置文件
- **用途**: 包含所有可配置的环境变量
- **特点**: 87个配置项，覆盖所有功能模块
- **适用场景**: 生产环境、需要完整功能配置

### 3. `env.example.simple` - 精简配置文件
- **用途**: 包含关键配置项的精简版本
- **特点**: 63个配置项，保留核心功能
- **适用场景**: 快速部署、开发测试、Docker部署

## 🚀 快速开始

### 方法一：使用精简配置（推荐）
```bash
# 复制精简配置文件
cp env.example.simple .env

# 编辑配置文件，至少设置以下关键配置
nano .env
```

**必须配置的项**：
```bash
OPENAI_API_KEY=your-openai-api-key-here
```

**推荐配置的项**：
```bash
MEM0_API_KEY=your-mem0-api-key-here
MEM0_BASE_URL=http://your-mem0-server:8765
```

### 方法二：使用完整配置
```bash
# 复制完整配置文件
cp env.example.full .env

# 根据需要编辑所有配置项
nano .env
```

## 📊 配置项分类

### 🔑 核心API密钥配置（必须）
- `OPENAI_API_KEY`: OpenAI API密钥
- `YYCHAT_API_KEY`: YYChat API密钥（有默认值）
- `TAVILY_API_KEY`: 外部服务API密钥

### 🤖 AI模型配置（推荐）
- `OPENAI_MODEL`: OpenAI模型名称
- `OPENAI_BASE_URL`: OpenAI API基础URL
- `OPENAI_TEMPERATURE`: 模型温度参数
- `OPENAI_MAX_TOKENS`: 最大token数量

### 🧠 记忆管理配置（推荐）
- `MEM0_API_KEY`: Mem0 API密钥
- `MEM0_BASE_URL`: Mem0服务地址
- `ENABLE_MEMORY_RETRIEVAL`: 是否启用记忆检索
- `MEMORY_RETRIEVAL_LIMIT`: 记忆检索数量限制

### 💾 数据存储配置（推荐）
- `VECTOR_STORE_PROVIDER`: 向量存储提供商
- `CHROMA_PERSIST_DIRECTORY`: ChromaDB持久化目录
- `CHROMA_COLLECTION_NAME`: ChromaDB集合名称

### 🚀 服务器配置（必须）
- `SERVER_HOST`: 服务器监听地址
- `SERVER_PORT`: 服务器监听端口

### 💬 聊天引擎配置（推荐）
- `CHAT_ENGINE`: 聊天引擎类型
- `DEFAULT_PERSONALITY`: 默认人格配置
- `STREAM_DEFAULT`: 是否默认启用流式响应
- `USE_TOOLS_DEFAULT`: 是否默认启用工具调用

### 🎤 实时语音配置（可选）
- `REALTIME_VOICE_ENABLED`: 实时语音功能开关
- `REALTIME_VOICE_MODEL`: 实时语音模型

### ⚡ 性能优化配置（可选）
- `OPENAI_API_TIMEOUT`: OpenAI API总超时时间
- `OPENAI_CONNECT_TIMEOUT`: OpenAI连接超时时间
- `OPENAI_API_RETRIES`: OpenAI API重试次数
- `MAX_CONNECTIONS`: 最大连接数

### 📊 缓存配置（可选）
- `USE_REDIS_CACHE`: 是否启用Redis缓存
- `REDIS_HOST`: Redis服务器地址
- `REDIS_PORT`: Redis服务器端口
- `REDIS_TTL`: Redis缓存TTL

### 📈 监控和日志配置（可选）
- `ENABLE_PERFORMANCE_MONITOR`: 是否启用性能监控
- `LOG_LEVEL`: 日志级别
- `LOG_FILE_NAME`: 日志文件名

### 🎵 音频处理配置（可选）
- `AUDIO_MAX_SIZE_MB`: 音频文件大小限制
- `TEXT_MAX_LENGTH`: 文本长度限制
- `VOICE_SPEED_MIN`: 最小语速
- `VOICE_SPEED_MAX`: 最大语速
- `AUDIO_COMPRESSION_QUALITY`: 音频压缩质量

### 🎤 语音和模型默认配置（可选）
- `DEFAULT_WHISPER_MODEL`: 默认语音转文本模型
- `DEFAULT_TTS_MODEL`: 默认文本转语音模型
- `DEFAULT_VOICE`: 默认语音
- `DEFAULT_CHAT_MODEL`: 默认聊天模型

## 🐳 Docker部署配置

### 使用Docker Compose
```bash
# 复制精简配置
cp env.example.simple .env

# 编辑配置
nano .env

# 启动服务
docker-compose up -d
```

### 环境变量优先级
1. `.env` 文件中的配置
2. 系统环境变量
3. 配置文件中的默认值

## 🔧 配置验证

### 验证配置文件完整性
```bash
python3 scripts/validate_env_examples.py
```

### 验证配置项正确性
```bash
python3 scripts/validate_config.py
```

## 📝 配置建议

### 开发环境
- 使用 `env.example.simple`
- 设置 `DEBUG_MODE=true`
- 设置 `LOG_LEVEL=DEBUG`
- 设置 `VERBOSE_LOGGING=true`

### 生产环境
- 使用 `env.example.full`
- 设置 `DEBUG_MODE=false`
- 设置 `LOG_LEVEL=INFO`
- 设置 `ENABLE_PERFORMANCE_MONITOR=true`
- 配置Redis缓存

### Docker环境
- 使用 `env.example.simple`
- 通过环境变量覆盖关键配置
- 设置 `SERVER_HOST=0.0.0.0`

## 🚨 注意事项

1. **安全性**: 不要将包含真实API密钥的 `.env` 文件提交到版本控制系统
2. **默认值**: 所有配置项都有合理的默认值，可以根据需要覆盖
3. **类型转换**: 配置项会自动进行类型转换（int, float, bool）
4. **环境变量**: 支持通过系统环境变量覆盖配置文件中的值

## 📚 相关文档

- [部署指南](DEPLOYMENT_GUIDE.md)
- [硬编码参数重构报告](HARDCODED_PARAMETERS_REFACTORING.md)
- [Docker Compose配置](docker-compose.example.yml)
