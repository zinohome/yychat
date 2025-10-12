# YYChat 后端语音功能实施 To-Do List

**项目**: YYChat 语音助手后端实施  
**方案**: 借鉴Chainlit设计，自建实现  
**版本**: v1.0  
**日期**: 2025年1月

---

## 🎯 阶段1：基础WebSocket通信层（第1-2周）

### 1.1 项目依赖和配置
- [ ] **添加WebSocket依赖**
  ```bash
  # 在requirements.txt中添加
  websockets>=11.0.3
  python-multipart>=0.0.6
  ```
  - [ ] 更新requirements.txt文件
  - [ ] 安装新依赖：`pip install -r requirements.txt`
  - [ ] 验证依赖安装成功

- [ ] **创建WebSocket配置**
  ```python
  # config/websocket_config.py
  class WebSocketConfig:
      MAX_CONNECTIONS = 100
      HEARTBEAT_INTERVAL = 30
      CONNECTION_TIMEOUT = 300
      MESSAGE_SIZE_LIMIT = 1024 * 1024  # 1MB
  ```
  - [ ] 创建websocket_config.py文件
  - [ ] 定义WebSocket相关配置参数
  - [ ] 集成到现有config系统

### 1.2 WebSocket管理器实现
- [ ] **创建WebSocket管理器类**
  ```python
  # core/websocket_manager.py
  class WebSocketManager:
      def __init__(self):
          self.active_connections: Dict[str, WebSocket] = {}
          self.connection_metadata: Dict[str, dict] = {}
      
      async def connect(self, websocket: WebSocket, client_id: str):
          # 实现连接逻辑
      
      async def disconnect(self, client_id: str):
          # 实现断开逻辑
      
      async def send_message(self, client_id: str, message: dict):
          # 实现消息发送逻辑
      
      async def broadcast_message(self, message: dict, exclude: List[str] = None):
          # 实现广播消息逻辑
  ```
  - [ ] 创建websocket_manager.py文件
  - [ ] 实现连接管理功能
  - [ ] 实现消息发送功能
  - [ ] 实现广播功能
  - [ ] 添加连接状态监控
  - [ ] 编写单元测试

- [ ] **实现连接生命周期管理**
  - [ ] 连接建立时的初始化逻辑
  - [ ] 连接断开时的清理逻辑
  - [ ] 心跳检测机制
  - [ ] 连接超时处理
  - [ ] 异常连接处理

### 1.3 WebSocket端点实现
- [ ] **创建WebSocket端点**
  ```python
  # app.py
  @app.websocket("/ws/chat")
  async def websocket_chat(websocket: WebSocket, client_id: str = None):
      # 实现WebSocket端点
  ```
  - [ ] 在app.py中添加WebSocket端点
  - [ ] 实现连接认证逻辑
  - [ ] 实现消息接收处理
  - [ ] 实现错误处理
  - [ ] 添加日志记录

- [ ] **实现消息路由系统**
  ```python
  # core/message_router.py
  class MessageRouter:
      def __init__(self):
          self.handlers: Dict[str, callable] = {}
      
      def register_handler(self, message_type: str, handler: callable):
          # 注册消息处理器
      
      async def route_message(self, client_id: str, message: dict):
          # 路由消息到对应处理器
  ```
  - [ ] 创建message_router.py文件
  - [ ] 实现消息类型注册
  - [ ] 实现消息路由逻辑
  - [ ] 添加消息验证
  - [ ] 编写路由测试

### 1.4 基础消息处理
- [ ] **实现文本消息处理**
  ```python
  # handlers/text_message_handler.py
  class TextMessageHandler:
      async def handle(self, client_id: str, message: dict):
          # 处理文本消息
  ```
  - [ ] 创建text_message_handler.py文件
  - [ ] 实现文本消息处理逻辑
  - [ ] 集成现有chat_engine
  - [ ] 实现流式响应
  - [ ] 添加错误处理

- [ ] **实现连接状态消息**
  - [ ] 连接建立确认消息
  - [ ] 心跳响应消息
  - [ ] 连接状态更新消息
  - [ ] 错误状态消息

---

## 🎯 阶段2：音频处理服务（第3-4周）

### 2.1 音频服务基础架构
- [ ] **创建音频服务类**
  ```python
  # services/audio_service.py
  class AudioService:
      def __init__(self):
          self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
          self.audio_cache = AudioCache()
      
      async def transcribe_audio(self, audio_data: bytes) -> str:
          # 语音转文本
      
      async def synthesize_speech(self, text: str, voice: str = "alloy") -> bytes:
          # 文本转语音
  ```
  - [ ] 创建audio_service.py文件
  - [ ] 实现OpenAI音频API集成
  - [ ] 实现音频缓存机制
  - [ ] 添加音频格式转换
  - [ ] 编写音频服务测试

- [ ] **实现音频缓存系统**
  ```python
  # services/audio_cache.py
  class AudioCache:
      def __init__(self, max_size: int = 100):
          self.cache: Dict[str, bytes] = {}
          self.max_size = max_size
      
      async def get(self, key: str) -> Optional[bytes]:
          # 获取缓存音频
      
      async def set(self, key: str, audio_data: bytes):
          # 设置缓存音频
  ```
  - [ ] 创建audio_cache.py文件
  - [ ] 实现LRU缓存算法
  - [ ] 实现缓存大小限制
  - [ ] 添加缓存统计
  - [ ] 编写缓存测试

### 2.2 语音转文本功能
- [ ] **实现STT处理**
  - [ ] 音频格式验证
  - [ ] 音频大小限制检查
  - [ ] OpenAI Whisper API调用
  - [ ] 转录结果处理
  - [ ] 错误处理和重试机制

- [ ] **实现音频预处理**
  ```python
  # utils/audio_utils.py
  class AudioUtils:
      @staticmethod
      def validate_audio_format(audio_data: bytes) -> bool:
          # 验证音频格式
      
      @staticmethod
      def convert_audio_format(audio_data: bytes, target_format: str) -> bytes:
          # 转换音频格式
  ```
  - [ ] 创建audio_utils.py文件
  - [ ] 实现音频格式验证
  - [ ] 实现音频格式转换
  - [ ] 实现音频压缩
  - [ ] 编写音频工具测试

### 2.3 文本转语音功能
- [ ] **实现TTS处理**
  - [ ] 文本长度验证
  - [ ] 语音选择逻辑
  - [ ] OpenAI TTS API调用
  - [ ] 音频数据返回
  - [ ] 错误处理机制

- [ ] **实现语音个性化**
  ```python
  # services/voice_personality_service.py
  class VoicePersonalityService:
      def __init__(self):
          self.voice_mapping = {
              "friendly": "alloy",
              "professional": "onyx",
              "health_assistant": "nova"
          }
      
      def get_voice_for_personality(self, personality_id: str) -> str:
          # 根据人格获取语音
  ```
  - [ ] 创建voice_personality_service.py文件
  - [ ] 实现人格到语音的映射
  - [ ] 集成personality_manager
  - [ ] 实现语音设置持久化
  - [ ] 编写语音个性化测试

### 2.4 音频API端点
- [ ] **创建音频转录端点**
  ```python
  # app.py
  @app.post("/v1/audio/transcriptions")
  async def create_transcription(audio_file: UploadFile = File(...)):
      # 实现音频转录端点
  ```
  - [ ] 在app.py中添加转录端点
  - [ ] 实现文件上传处理
  - [ ] 实现音频验证
  - [ ] 实现转录结果返回
  - [ ] 添加端点测试

- [ ] **创建语音合成端点**
  ```python
  # app.py
  @app.post("/v1/audio/speech")
  async def create_speech(request: SpeechRequest):
      # 实现语音合成端点
  ```
  - [ ] 在app.py中添加合成端点
  - [ ] 实现请求参数验证
  - [ ] 实现语音合成
  - [ ] 实现音频流返回
  - [ ] 添加端点测试

---

## 🎯 阶段3：实时消息处理（第5-6周）

### 3.1 实时消息处理器
- [ ] **创建实时消息处理器**
  ```python
  # core/realtime_handler.py
  class RealtimeMessageHandler:
      def __init__(self, chat_engine, websocket_manager, audio_service):
          self.chat_engine = chat_engine
          self.websocket_manager = websocket_manager
          self.audio_service = audio_service
      
      async def handle_message(self, client_id: str, message: dict):
          # 处理实时消息
  ```
  - [ ] 创建realtime_handler.py文件
  - [ ] 实现消息类型分发
  - [ ] 集成现有chat_engine
  - [ ] 实现流式响应处理
  - [ ] 编写处理器测试

- [ ] **实现消息类型处理**
  - [ ] 文本消息处理
  - [ ] 音频消息处理
  - [ ] 语音命令处理
  - [ ] 状态查询处理
  - [ ] 错误消息处理

### 3.2 音频消息处理
- [ ] **实现音频输入处理**
  ```python
  async def _handle_audio_input(self, client_id: str, message: dict):
      # 1. 接收音频数据
      audio_data = base64.b64decode(message["audio_data"])
      
      # 2. 语音转文本
      text = await self.audio_service.transcribe_audio(audio_data)
      
      # 3. 构建消息并处理
      # 4. 发送确认和响应
  ```
  - [ ] 实现音频数据解码
  - [ ] 实现语音转文本调用
  - [ ] 实现文本消息构建
  - [ ] 实现确认消息发送
  - [ ] 添加音频处理测试

- [ ] **实现音频流处理**
  ```python
  async def _handle_audio_stream(self, client_id: str, audio_chunk: bytes):
      # 处理音频流数据
      # 实现音频缓冲和实时转录
  ```
  - [ ] 实现音频流缓冲
  - [ ] 实现实时转录
  - [ ] 实现语音活动检测
  - [ ] 实现流式响应
  - [ ] 添加流处理测试

### 3.3 语音输出处理
- [ ] **实现语音响应处理**
  ```python
  async def _handle_voice_response(self, client_id: str, text: str, voice: str = "alloy"):
      # 1. 发送文本响应
      # 2. 生成语音
      # 3. 发送音频响应
  ```
  - [ ] 实现文本响应发送
  - [ ] 实现语音合成调用
  - [ ] 实现音频响应发送
  - [ ] 实现语音设置应用
  - [ ] 添加语音响应测试

- [ ] **实现流式语音输出**
  ```python
  async def _stream_voice_response(self, client_id: str, text: str):
      # 分段生成语音，实现流式播放
  ```
  - [ ] 实现文本分段
  - [ ] 实现分段语音合成
  - [ ] 实现流式音频发送
  - [ ] 实现播放状态管理
  - [ ] 添加流式语音测试

### 3.4 与现有功能集成
- [ ] **记忆管理集成**
  ```python
  async def _enhance_with_memory(self, conversation_id: str, messages: List[dict]):
      # 获取历史记忆并增强消息
      memory_result = await self.chat_engine.get_conversation_memory(conversation_id)
      # 构建增强的消息
  ```
  - [ ] 集成记忆检索功能
  - [ ] 实现消息增强逻辑
  - [ ] 实现记忆存储
  - [ ] 添加记忆集成测试

- [ ] **工具调用集成**
  ```python
  async def _handle_tool_calls_async(self, tool_calls, conversation_id):
      # 异步处理工具调用
      tasks = [asyncio.create_task(self.tool_manager.execute_tool_async(tool_call)) 
               for tool_call in tool_calls]
      results = await asyncio.gather(*tasks)
  ```
  - [ ] 实现异步工具调用
  - [ ] 实现工具结果语音播报
  - [ ] 实现工具调用状态通知
  - [ ] 添加工具调用测试

- [ ] **MCP调用集成**
  ```python
  async def _handle_mcp_calls_async(self, mcp_calls, conversation_id):
      # 异步处理MCP调用
  ```
  - [ ] 实现异步MCP调用
  - [ ] 实现MCP结果语音播报
  - [ ] 实现MCP调用状态通知
  - [ ] 添加MCP调用测试

---

## 🎯 阶段4：实时语音对话（第7-8周）

### 4.1 实时音频流处理
- [ ] **创建音频流处理器**
  ```python
  # core/audio_stream_handler.py
  class AudioStreamHandler:
      def __init__(self):
          self.audio_buffers: Dict[str, List[bytes]] = {}
          self.vad = webrtcvad.Vad(2)
      
      async def process_audio_chunk(self, client_id: str, audio_chunk: bytes):
          # 处理音频块
  ```
  - [ ] 创建audio_stream_handler.py文件
  - [ ] 实现音频缓冲管理
  - [ ] 实现语音活动检测
  - [ ] 实现音频段处理
  - [ ] 编写流处理测试

- [ ] **实现语音活动检测**
  ```python
  def _detect_speech_activity(self, audio_chunk: bytes) -> bool:
      # 使用WebRTC VAD检测语音活动
      return self.vad.is_speech(audio_chunk, 16000)
  ```
  - [ ] 安装webrtcvad依赖
  - [ ] 实现VAD检测逻辑
  - [ ] 实现阈值配置
  - [ ] 实现检测结果处理
  - [ ] 编写VAD测试

### 4.2 实时响应优化
- [ ] **实现低延迟响应**
  - [ ] 优化音频处理管道
  - [ ] 实现并行处理
  - [ ] 实现响应缓存
  - [ ] 实现延迟监控
  - [ ] 编写延迟测试

- [ ] **实现流式TTS**
  ```python
  async def _stream_tts_response(self, client_id: str, text: str):
      # 分段生成语音，实现流式播放
      words = text.split()
      chunk_size = 10
      
      for i in range(0, len(words), chunk_size):
          chunk_text = ' '.join(words[i:i+chunk_size])
          audio_data = await self.audio_service.synthesize_speech(chunk_text)
          # 发送音频块
  ```
  - [ ] 实现文本分段逻辑
  - [ ] 实现分段语音合成
  - [ ] 实现流式音频发送
  - [ ] 实现播放状态管理
  - [ ] 编写流式TTS测试

### 4.3 连接管理优化
- [ ] **实现连接池管理**
  ```python
  # core/connection_pool.py
  class ConnectionPool:
      def __init__(self, max_connections: int = 100):
          self.max_connections = max_connections
          self.connections: Dict[str, ConnectionInfo] = {}
      
      async def acquire_connection(self, client_id: str) -> ConnectionInfo:
          # 获取连接
      
      async def release_connection(self, client_id: str):
          # 释放连接
  ```
  - [ ] 创建connection_pool.py文件
  - [ ] 实现连接池管理
  - [ ] 实现连接状态跟踪
  - [ ] 实现连接清理
  - [ ] 编写连接池测试

- [ ] **实现错误恢复机制**
  ```python
  async def _handle_connection_error(self, client_id: str, error: Exception):
      # 处理连接错误
      # 实现自动重连
      # 实现状态恢复
  ```
  - [ ] 实现错误检测
  - [ ] 实现自动重连
  - [ ] 实现状态恢复
  - [ ] 实现错误通知
  - [ ] 编写错误处理测试

---

## 🎯 阶段5：性能优化和测试（第9-10周）

### 5.1 性能优化
- [ ] **音频压缩优化**
  ```python
  # utils/audio_compression.py
  class AudioCompressor:
      @staticmethod
      def compress_audio(audio_data: bytes, quality: int = 80) -> bytes:
          # 实现音频压缩
  ```
  - [ ] 创建audio_compression.py文件
  - [ ] 实现音频压缩算法
  - [ ] 实现质量配置
  - [ ] 实现压缩测试
  - [ ] 编写压缩工具测试

- [ ] **缓存优化**
  ```python
  # services/smart_cache.py
  class SmartCache:
      def __init__(self):
          self.text_cache: Dict[str, str] = {}
          self.audio_cache: Dict[str, bytes] = {}
          self.tts_cache: Dict[str, bytes] = {}
  ```
  - [ ] 创建smart_cache.py文件
  - [ ] 实现多级缓存
  - [ ] 实现缓存策略
  - [ ] 实现缓存统计
  - [ ] 编写缓存测试

- [ ] **并发优化**
  - [ ] 实现异步处理池
  - [ ] 实现任务队列
  - [ ] 实现负载均衡
  - [ ] 实现资源监控
  - [ ] 编写并发测试

### 5.2 监控和日志
- [ ] **实现性能监控**
  ```python
  # monitoring/voice_monitor.py
  class VoiceMonitor:
      def __init__(self):
          self.metrics = {
              'connection_count': 0,
              'audio_processing_time': [],
              'tts_generation_time': [],
              'error_count': 0
          }
  ```
  - [ ] 创建voice_monitor.py文件
  - [ ] 实现性能指标收集
  - [ ] 实现实时监控
  - [ ] 实现告警机制
  - [ ] 编写监控测试

- [ ] **实现详细日志**
  ```python
  # utils/voice_logger.py
  class VoiceLogger:
      def __init__(self):
          self.logger = structlog.get_logger("voice_agents")
      
      def log_audio_processing(self, client_id: str, duration: float):
          # 记录音频处理日志
  ```
  - [ ] 创建voice_logger.py文件
  - [ ] 实现结构化日志
  - [ ] 实现日志轮转
  - [ ] 实现日志分析
  - [ ] 编写日志测试

### 5.3 测试和验证
- [ ] **单元测试**
  ```python
  # tests/test_websocket_manager.py
  async def test_websocket_connection():
      # 测试WebSocket连接
  ```
  - [ ] 测试WebSocket管理器
  - [ ] 测试音频服务
  - [ ] 测试消息处理器
  - [ ] 测试实时处理器
  - [ ] 测试错误处理

- [ ] **集成测试**
  ```python
  # tests/test_voice_integration.py
  async def test_voice_chat_flow():
      # 测试完整语音聊天流程
  ```
  - [ ] 测试语音输入流程
  - [ ] 测试语音输出流程
  - [ ] 测试实时对话流程
  - [ ] 测试错误恢复流程
  - [ ] 测试性能指标

- [ ] **压力测试**
  ```python
  # tests/test_voice_load.py
  async def test_concurrent_connections():
      # 测试并发连接
  ```
  - [ ] 测试并发连接数
  - [ ] 测试音频处理负载
  - [ ] 测试内存使用
  - [ ] 测试CPU使用
  - [ ] 测试网络带宽

---

## 🎯 阶段6：部署和文档（第11-12周）

### 6.1 部署准备
- [ ] **Docker配置**
  ```dockerfile
  # Dockerfile.voice
  FROM python:3.11-slim
  
  # 安装音频处理依赖
  RUN apt-get update && apt-get install -y \
      ffmpeg \
      libsndfile1 \
      && rm -rf /var/lib/apt/lists/*
  
  # 复制应用代码
  COPY . /app
  WORKDIR /app
  
  # 安装Python依赖
  RUN pip install -r requirements.txt
  
  # 启动应用
  CMD ["python", "app.py"]
  ```
  - [ ] 创建Dockerfile.voice
  - [ ] 配置音频处理依赖
  - [ ] 配置环境变量
  - [ ] 配置端口映射
  - [ ] 测试Docker构建

- [ ] **环境配置**
  ```yaml
  # docker-compose.voice.yml
  version: '3.8'
  services:
    yychat-voice:
      build:
        context: .
        dockerfile: Dockerfile.voice
      ports:
        - "9800:9800"
        - "9801:9801"  # WebSocket端口
      environment:
        - OPENAI_API_KEY=${OPENAI_API_KEY}
        - YYCHAT_API_KEY=${YYCHAT_API_KEY}
      volumes:
        - ./logs:/app/logs
        - ./audio_cache:/app/audio_cache
  ```
  - [ ] 创建docker-compose.voice.yml
  - [ ] 配置服务依赖
  - [ ] 配置数据卷
  - [ ] 配置网络
  - [ ] 测试容器部署

### 6.2 文档编写
- [ ] **API文档**
  ```markdown
  # Voice Agents API Documentation
  
  ## WebSocket Endpoints
  - `/ws/chat` - 实时语音聊天
  
  ## REST Endpoints
  - `POST /v1/audio/transcriptions` - 音频转录
  - `POST /v1/audio/speech` - 语音合成
  ```
  - [ ] 编写WebSocket API文档
  - [ ] 编写REST API文档
  - [ ] 编写错误码文档
  - [ ] 编写示例代码
  - [ ] 生成OpenAPI规范

- [ ] **部署文档**
  ```markdown
  # Voice Agents Deployment Guide
  
  ## 系统要求
  - Python 3.11+
  - 4GB+ RAM
  - 音频处理库
  
  ## 安装步骤
  1. 安装依赖
  2. 配置环境变量
  3. 启动服务
  ```
  - [ ] 编写安装指南
  - [ ] 编写配置说明
  - [ ] 编写故障排除
  - [ ] 编写性能调优
  - [ ] 编写监控指南

### 6.3 最终测试
- [ ] **端到端测试**
  - [ ] 测试完整语音对话流程
  - [ ] 测试多用户并发
  - [ ] 测试长时间运行
  - [ ] 测试错误恢复
  - [ ] 测试性能指标

- [ ] **用户验收测试**
  - [ ] 测试语音识别准确率
  - [ ] 测试语音合成质量
  - [ ] 测试实时响应速度
  - [ ] 测试用户体验
  - [ ] 收集用户反馈

---

## 📊 进度跟踪

### 每周检查点
- [ ] **第1周**: WebSocket基础架构完成
- [ ] **第2周**: 消息路由系统完成
- [ ] **第3周**: 音频服务基础完成
- [ ] **第4周**: 音频API端点完成
- [ ] **第5周**: 实时消息处理完成
- [ ] **第6周**: 音频消息处理完成
- [ ] **第7周**: 实时音频流处理完成
- [ ] **第8周**: 连接管理优化完成
- [ ] **第9周**: 性能优化完成
- [ ] **第10周**: 测试和验证完成
- [ ] **第11周**: 部署准备完成
- [ ] **第12周**: 文档和最终测试完成

### 关键里程碑
- [ ] **里程碑1**: WebSocket通信层完成（第2周）
- [ ] **里程碑2**: 基础语音功能完成（第4周）
- [ ] **里程碑3**: 实时语音对话完成（第8周）
- [ ] **里程碑4**: 生产就绪完成（第12周）

---

## 🚨 风险控制

### 技术风险
- [ ] **音频处理延迟**: 实现性能监控和优化
- [ ] **WebSocket连接稳定性**: 实现重连机制
- [ ] **内存使用**: 实现资源监控和限制
- [ ] **并发处理**: 实现连接池和负载均衡

### 缓解措施
- [ ] 每个阶段完成后进行代码审查
- [ ] 关键功能实现后立即测试
- [ ] 定期进行性能基准测试
- [ ] 建立回滚机制

---

**负责人**: 后端开发团队  
**预计完成时间**: 12周  
**资源需求**: 2-3名开发人员，1名测试人员
