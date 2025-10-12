# YYChat Voice Agents 实施计划

**项目**: YYChat 语音助手后端实施计划  
**版本**: v1.0  
**日期**: 2025年1月  
**目标**: 在现有yychat架构基础上实现完整的语音助手功能

---

## 📋 项目概述

### 目标
将yychat从纯文本聊天服务升级为支持语音交互的智能助手，包括：
- 语音输入识别（STT）
- 语音输出合成（TTS）
- 实时语音对话
- 与现有功能（记忆、人格、工具、MCP）的完整集成

### 技术架构
```
用户语音 → 前端STT → WebSocket → yychat后端 → AI处理 → TTS → 语音输出
```

---

## 🎯 实施阶段

### 阶段1：基础语音功能（2-3周）

#### 1.1 WebSocket实时通信层
**目标**: 建立实时通信基础设施

**任务清单**:
- [ ] 添加WebSocket依赖
  ```bash
  pip install websockets fastapi[all]
  ```

- [ ] 创建WebSocket管理器
  ```python
  # core/websocket_manager.py
  class WebSocketManager:
      def __init__(self):
          self.active_connections: Dict[str, WebSocket] = {}
      
      async def connect(self, websocket: WebSocket, client_id: str):
          await websocket.accept()
          self.active_connections[client_id] = websocket
      
      async def disconnect(self, client_id: str):
          if client_id in self.active_connections:
              del self.active_connections[client_id]
      
      async def send_message(self, client_id: str, message: dict):
          if client_id in self.active_connections:
              await self.active_connections[client_id].send_text(json.dumps(message))
  ```

- [ ] 添加WebSocket端点
  ```python
  # app.py
  from fastapi import WebSocket, WebSocketDisconnect
  
  @app.websocket("/ws/chat")
  async def websocket_chat(websocket: WebSocket, client_id: str = None):
      if not client_id:
          client_id = str(uuid.uuid4())
      
      await websocket_manager.connect(websocket, client_id)
      try:
          while True:
              data = await websocket.receive_text()
              message = json.loads(data)
              await handle_realtime_message(client_id, message)
      except WebSocketDisconnect:
          await websocket_manager.disconnect(client_id)
  ```

#### 1.2 音频处理服务
**目标**: 集成OpenAI音频API

**任务清单**:
- [ ] 创建音频服务类
  ```python
  # services/audio_service.py
  class AudioService:
      def __init__(self):
          self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
      
      async def transcribe_audio(self, audio_data: bytes) -> str:
          """语音转文本"""
          audio_file = io.BytesIO(audio_data)
          audio_file.name = "audio.wav"
          
          response = await asyncio.to_thread(
              self.openai_client.audio.transcriptions.create,
              model="whisper-1",
              file=audio_file
          )
          return response.text
      
      async def synthesize_speech(self, text: str, voice: str = "alloy") -> bytes:
          """文本转语音"""
          response = await asyncio.to_thread(
              self.openai_client.audio.speech.create,
              model="tts-1",
              voice=voice,
              input=text
          )
          return response.content
  ```

- [ ] 添加音频API端点
  ```python
  # app.py
  @app.post("/v1/audio/transcriptions")
  async def create_transcription(audio_file: UploadFile = File(...)):
      audio_data = await audio_file.read()
      text = await audio_service.transcribe_audio(audio_data)
      return {"text": text}
  
  @app.post("/v1/audio/speech")
  async def create_speech(request: SpeechRequest):
      audio_data = await audio_service.synthesize_speech(
          request.text, 
          request.voice
      )
      return StreamingResponse(
          io.BytesIO(audio_data),
          media_type="audio/mpeg"
      )
  ```

#### 1.3 实时消息处理
**目标**: 实现实时消息处理逻辑

**任务清单**:
- [ ] 创建实时消息处理器
  ```python
  # core/realtime_handler.py
  class RealtimeMessageHandler:
      def __init__(self, chat_engine, websocket_manager):
          self.chat_engine = chat_engine
          self.websocket_manager = websocket_manager
      
      async def handle_message(self, client_id: str, message: dict):
          message_type = message.get("type")
          
          if message_type == "text_input":
              await self._handle_text_input(client_id, message)
          elif message_type == "audio_input":
              await self._handle_audio_input(client_id, message)
          elif message_type == "voice_command":
              await self._handle_voice_command(client_id, message)
      
      async def _handle_text_input(self, client_id: str, message: dict):
          # 处理文本输入，复用现有逻辑
          response = await self.chat_engine.generate_response(
              messages=message["messages"],
              conversation_id=message.get("conversation_id"),
              personality_id=message.get("personality_id"),
              use_tools=message.get("use_tools", True),
              stream=True
          )
          
          # 流式发送响应
          async for chunk in response:
              await self.websocket_manager.send_message(client_id, {
                  "type": "text_response",
                  "data": chunk
              })
  ```

### 阶段2：语音功能集成（2-3周）

#### 2.1 语音输入处理
**目标**: 实现完整的语音输入流程

**任务清单**:
- [ ] 扩展消息处理器支持音频
  ```python
  async def _handle_audio_input(self, client_id: str, message: dict):
      # 1. 接收音频数据
      audio_data = base64.b64decode(message["audio_data"])
      
      # 2. 语音转文本
      text = await audio_service.transcribe_audio(audio_data)
      
      # 3. 构建消息
      messages = message.get("messages", [])
      messages.append({"role": "user", "content": text})
      
      # 4. 发送确认
      await self.websocket_manager.send_message(client_id, {
          "type": "transcription_complete",
          "text": text
      })
      
      # 5. 处理文本消息
      await self._handle_text_input(client_id, {
          "messages": messages,
          "conversation_id": message.get("conversation_id"),
          "personality_id": message.get("personality_id"),
          "use_tools": message.get("use_tools", True)
      })
  ```

- [ ] 添加音频流处理
  ```python
  async def _handle_audio_stream(self, client_id: str, audio_chunk: bytes):
      # 处理音频流数据
      # 实现音频缓冲和实时转录
      pass
  ```

#### 2.2 语音输出处理
**目标**: 实现语音输出功能

**任务清单**:
- [ ] 扩展响应处理器支持TTS
  ```python
  async def _handle_text_response(self, client_id: str, text: str, voice: str = "alloy"):
      # 1. 发送文本响应
      await self.websocket_manager.send_message(client_id, {
          "type": "text_response",
          "text": text
      })
      
      # 2. 生成语音
      audio_data = await audio_service.synthesize_speech(text, voice)
      
      # 3. 发送音频响应
      await self.websocket_manager.send_message(client_id, {
          "type": "audio_response",
          "audio_data": base64.b64encode(audio_data).decode(),
          "text": text
      })
  ```

- [ ] 添加语音配置
  ```python
  # config/audio_config.py
  class AudioConfig:
      DEFAULT_VOICE = "alloy"
      SUPPORTED_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
      AUDIO_FORMAT = "mp3"
      SAMPLE_RATE = 24000
      CHUNK_SIZE = 1024
  ```

#### 2.3 与现有功能集成
**目标**: 确保语音功能与现有功能完美集成

**任务清单**:
- [ ] 记忆管理集成
  ```python
  # 在实时消息处理中集成记忆
  async def _handle_text_input(self, client_id: str, message: dict):
      conversation_id = message.get("conversation_id", "default")
      
      # 获取历史记忆
      memory_result = await self.chat_engine.get_conversation_memory(conversation_id)
      
      # 构建增强的消息
      enhanced_messages = self._build_enhanced_messages(
          message["messages"], 
          memory_result.get("memories", [])
      )
      
      # 处理消息...
  ```

- [ ] 人格化集成
  ```python
  # 根据人格选择语音风格
  async def _get_voice_for_personality(self, personality_id: str) -> str:
      personality_config = await self.personality_manager.get_personality(personality_id)
      return personality_config.get("voice", "alloy")
  ```

- [ ] 工具调用集成
  ```python
  # 工具调用结果语音播报
  async def _handle_tool_call_result(self, client_id: str, tool_result: dict):
      # 生成工具调用结果的语音描述
      description = self._format_tool_result_for_speech(tool_result)
      
      # 语音播报
      await self._handle_text_response(client_id, description)
  ```

### 阶段3：实时语音对话（3-4周）

#### 3.1 实时音频流处理
**目标**: 实现真正的实时语音对话

**任务清单**:
- [ ] 实现音频流缓冲
  ```python
  # core/audio_stream_handler.py
  class AudioStreamHandler:
      def __init__(self):
          self.audio_buffers: Dict[str, List[bytes]] = {}
          self.vad = webrtcvad.Vad(2)  # 语音活动检测
      
      async def process_audio_chunk(self, client_id: str, audio_chunk: bytes):
          # 添加到缓冲区
          if client_id not in self.audio_buffers:
              self.audio_buffers[client_id] = []
          
          self.audio_buffers[client_id].append(audio_chunk)
          
          # 检测语音活动
          if self._detect_speech_activity(audio_chunk):
              await self._process_speech_segment(client_id)
      
      async def _process_speech_segment(self, client_id: str):
          # 处理完整的语音段
          audio_data = b''.join(self.audio_buffers[client_id])
          self.audio_buffers[client_id] = []
          
          # 转录并处理
          text = await audio_service.transcribe_audio(audio_data)
          # ... 处理逻辑
  ```

- [ ] 实现语音活动检测
  ```python
  def _detect_speech_activity(self, audio_chunk: bytes) -> bool:
      # 使用WebRTC VAD检测语音活动
      return self.vad.is_speech(audio_chunk, 16000)
  ```

#### 3.2 实时响应优化
**目标**: 优化实时响应性能

**任务清单**:
- [ ] 实现流式TTS
  ```python
  async def _stream_tts_response(self, client_id: str, text: str):
      # 分段生成语音，实现流式播放
      words = text.split()
      chunk_size = 10  # 每10个词一段
      
      for i in range(0, len(words), chunk_size):
          chunk_text = ' '.join(words[i:i+chunk_size])
          audio_data = await audio_service.synthesize_speech(chunk_text)
          
          await self.websocket_manager.send_message(client_id, {
              "type": "audio_chunk",
              "audio_data": base64.b64encode(audio_data).decode(),
              "is_final": i + chunk_size >= len(words)
          })
  ```

- [ ] 优化工具调用为异步
  ```python
  # 修改工具调用为异步，避免阻塞实时流
  async def _handle_tool_calls_async(self, tool_calls, conversation_id):
      tasks = []
      for tool_call in tool_calls:
          task = asyncio.create_task(
              self.tool_manager.execute_tool_async(tool_call)
          )
          tasks.append(task)
      
      results = await asyncio.gather(*tasks)
      return results
  ```

#### 3.3 错误处理和恢复
**目标**: 确保实时对话的稳定性

**任务清单**:
- [ ] 实现连接管理
  ```python
  class ConnectionManager:
      def __init__(self):
          self.connections: Dict[str, ConnectionInfo] = {}
      
      async def handle_disconnect(self, client_id: str):
          # 清理资源
          if client_id in self.connections:
              connection = self.connections[client_id]
              await connection.cleanup()
              del self.connections[client_id]
  ```

- [ ] 实现错误恢复
  ```python
  async def _handle_audio_error(self, client_id: str, error: Exception):
      await self.websocket_manager.send_message(client_id, {
          "type": "error",
          "message": "音频处理错误，请重试",
          "error_type": "audio_processing_error"
      })
  ```

### 阶段4：性能优化和测试（2-3周）

#### 4.1 性能优化
**目标**: 优化语音交互性能

**任务清单**:
- [ ] 音频压缩优化
  ```python
  # 实现音频压缩以减少传输延迟
  def compress_audio(self, audio_data: bytes) -> bytes:
      # 使用更高效的音频编码
      pass
  ```

- [ ] 缓存优化
  ```python
  # 缓存常用语音片段
  class AudioCache:
      def __init__(self):
          self.cache: Dict[str, bytes] = {}
      
      async def get_cached_audio(self, text: str) -> Optional[bytes]:
          return self.cache.get(text)
  ```

#### 4.2 测试和验证
**目标**: 确保功能完整性和稳定性

**任务清单**:
- [ ] 单元测试
  ```python
  # test/test_audio_service.py
  async def test_transcribe_audio():
      audio_service = AudioService()
      # 测试语音转文本
      pass
  
  async def test_synthesize_speech():
      audio_service = AudioService()
      # 测试文本转语音
      pass
  ```

- [ ] 集成测试
  ```python
  # test/test_realtime_chat.py
  async def test_realtime_voice_chat():
      # 测试完整的实时语音对话流程
      pass
  ```

---

## 🔧 技术实现细节

### 依赖管理
```python
# requirements.txt 新增依赖
websockets>=11.0.3
webrtcvad>=2.0.10
pydub>=0.25.1
asyncio-mqtt>=0.13.0
```

### 配置管理
```python
# config/voice_config.py
class VoiceConfig:
    # WebSocket配置
    WS_MAX_CONNECTIONS = 100
    WS_HEARTBEAT_INTERVAL = 30
    WS_TIMEOUT = 300
    
    # 音频配置
    AUDIO_CHUNK_SIZE = 1024
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHANNELS = 1
    
    # 语音活动检测
    VAD_AGGRESSIVENESS = 2
    VAD_FRAME_DURATION = 30  # ms
    
    # TTS配置
    TTS_VOICE = "alloy"
    TTS_MODEL = "tts-1"
    TTS_SPEED = 1.0
```

### 数据库扩展
```python
# models/voice_conversation.py
class VoiceConversation(BaseModel):
    id: str
    client_id: str
    conversation_id: str
    audio_transcript: str
    audio_response: str
    voice_settings: dict
    created_at: datetime
    updated_at: datetime
```

---

## 📊 性能指标

### 目标性能
- **延迟**: < 200ms (端到端)
- **并发**: 支持100个同时连接
- **音频质量**: 24kHz采样率，MP3格式
- **准确率**: 语音识别 > 95%

### 监控指标
- WebSocket连接数
- 音频处理延迟
- 错误率
- 内存使用率

---

## 🚀 部署计划

### 开发环境
1. 本地开发测试
2. Docker容器化
3. 集成测试环境

### 生产环境
1. 负载均衡配置
2. 音频文件存储
3. 监控和日志

---

## 📝 风险评估

### 技术风险
- **音频质量**: 网络条件影响音频传输质量
- **延迟**: 实时性要求高，需要优化网络和算法
- **并发**: 大量并发连接可能影响性能

### 缓解措施
- 实现音频质量自适应
- 使用CDN加速音频传输
- 实现连接池和负载均衡

---

## 🎯 成功标准

### 功能完整性
- [ ] 支持语音输入识别
- [ ] 支持语音输出合成
- [ ] 支持实时语音对话
- [ ] 与现有功能完整集成

### 性能标准
- [ ] 端到端延迟 < 200ms
- [ ] 支持100并发连接
- [ ] 语音识别准确率 > 95%
- [ ] 系统稳定性 > 99%

### 用户体验
- [ ] 语音交互自然流畅
- [ ] 错误处理友好
- [ ] 支持多种语音设置
- [ ] 跨平台兼容性

---

**实施负责人**: 开发团队  
**预计完成时间**: 10-13周  
**资源需求**: 2-3名开发人员，1名测试人员
