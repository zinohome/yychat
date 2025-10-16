# TTS流式播放优化方案

## 问题分析

### 当前问题
1. **TTS断句不连贯**：32KB字节分片，在句子中间切断
2. **按钮状态闪烁**：每段TTS播放完成就更新状态
3. **TTS响应延迟**：等所有SSE文本输出完才开始TTS

### 优化目标
1. **智能TTS分块**：按标点符号分块，语义连贯
2. **流式TTS响应**：SSE流式输出时立即TTS，响应迅速
3. **简化按钮状态**：避免TTS播放过程中的状态闪烁

## 技术方案

### 1. 智能TTS分块器

**新增文件**: `services/tts_segmenter.py`

```python
import re
from typing import List, Tuple

class TTSSegmenter:
    """TTS智能分块器"""
    
    def __init__(self):
        # 中文标点符号
        self.chinese_punctuation = r'[。！？，、；：]'
        # 英文标点符号
        self.english_punctuation = r'[.!?,;:]'
        # 所有标点符号
        self.all_punctuation = r'[。！？，、；：.!?,;:]'
    
    def segment_text(self, text: str) -> List[str]:
        """
        按标点符号智能分块文本
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 分块后的文本列表
        """
        if not text or not text.strip():
            return []
        
        # 按标点符号分割
        segments = re.split(f'({self.all_punctuation})', text)
        
        # 重新组合，保留标点符号
        result = []
        current_segment = ""
        
        for i, part in enumerate(segments):
            if not part.strip():
                continue
                
            current_segment += part
            
            # 如果包含标点符号，或者到达末尾
            if re.search(self.all_punctuation, part) or i == len(segments) - 1:
                if current_segment.strip():
                    result.append(current_segment.strip())
                    current_segment = ""
        
        return result
    
    def should_trigger_tts(self, text: str) -> bool:
        """
        判断是否应该触发TTS
        
        Args:
            text: 当前文本
            
        Returns:
            bool: 是否应该触发TTS
        """
        # 检查是否包含标点符号
        return bool(re.search(self.all_punctuation, text))
```

### 2. 流式TTS管理器

**新增文件**: `services/streaming_tts_manager.py`

```python
import asyncio
import base64
from typing import AsyncGenerator, List
from services.tts_segmenter import TTSSegmenter
from services.audio_service import AudioService
from core.websocket_manager import websocket_manager
from utils.log import log

class StreamingTTSManager:
    """流式TTS管理器"""
    
    def __init__(self):
        self.segmenter = TTSSegmenter()
        self.audio_service = AudioService()
        self.pending_segments = []
        self.is_processing = False
    
    async def process_streaming_text(self, text_chunk: str, client_id: str, 
                                   session_id: str, message_id: str, voice: str = "alloy"):
        """
        处理流式文本，智能分块并立即TTS
        
        Args:
            text_chunk: 文本块
            client_id: 客户端ID
            session_id: 会话ID
            message_id: 消息ID
            voice: 语音类型
        """
        # 添加到待处理队列
        self.pending_segments.append(text_chunk)
        current_text = "".join(self.pending_segments)
        
        # 检查是否应该触发TTS
        if self.segmenter.should_trigger_tts(current_text):
            # 分块处理
            segments = self.segmenter.segment_text(current_text)
            
            # 处理完整的分块
            for i, segment in enumerate(segments[:-1]):  # 除了最后一个
                await self._synthesize_and_send(segment, client_id, session_id, message_id, voice, i)
            
            # 保留最后一个不完整的分块
            self.pending_segments = [segments[-1]] if segments else []
    
    async def finalize_tts(self, client_id: str, session_id: str, message_id: str, voice: str = "alloy"):
        """
        完成TTS处理，处理剩余的文本
        
        Args:
            client_id: 客户端ID
            session_id: 会话ID
            message_id: 消息ID
            voice: 语音类型
        """
        if self.pending_segments:
            remaining_text = "".join(self.pending_segments)
            if remaining_text.strip():
                await self._synthesize_and_send(remaining_text, client_id, session_id, message_id, voice, 0)
        
        # 发送完成信号
        await websocket_manager.send_synthesis_complete(client_id, session_id=session_id, message_id=message_id)
        log.info(f"TTS streaming completed: client_id={client_id}, session_id={session_id}")
    
    async def _synthesize_and_send(self, text: str, client_id: str, session_id: str, 
                                 message_id: str, voice: str, seq: int):
        """
        合成并发送TTS音频
        
        Args:
            text: 文本内容
            client_id: 客户端ID
            session_id: 会话ID
            message_id: 消息ID
            voice: 语音类型
            seq: 序列号
        """
        try:
            # 合成语音
            audio_data = await self.audio_service.synthesize_speech(text, voice)
            
            # 发送音频流
            await websocket_manager.send_audio_stream(
                client_id,
                session_id=session_id,
                message_id=message_id,
                payload_base64=base64.b64encode(audio_data).decode("utf-8"),
                codec="audio/mpeg",
                seq=seq
            )
            
            log.debug(f"TTS segment sent: text='{text[:50]}...', seq={seq}")
            
        except Exception as e:
            log.error(f"TTS synthesis failed: {e}")
```

### 3. 修改SSE流式处理

**修改文件**: `app.py`

```python
# 在SSE流式处理中集成流式TTS
async def stream_generator():
    try:
        # ... 现有SSE处理逻辑 ...
        
        # 初始化流式TTS管理器
        tts_manager = StreamingTTSManager()
        
        # 流式响应处理
        async for chunk in response_stream:
            if chunk.get("content"):
                content = chunk["content"]
                full_content_parts.append(content)
                
                # 发送SSE内容
                yield f"data: {json.dumps(chunk)}\n\n"
                
                # 流式TTS处理
                if enable_voice and client_id:
                    await tts_manager.process_streaming_text(
                        content, client_id, session_id, message_id, voice
                    )
        
        # 完成TTS处理
        if enable_voice and client_id:
            await tts_manager.finalize_tts(client_id, session_id, message_id, voice)
            
    except Exception as e:
        # ... 错误处理 ...
```

### 4. 简化按钮状态管理

**修改文件**: `assets/js/unified_button_state_manager.js`

```javascript
class UnifiedButtonStateManager {
    constructor() {
        this.GLOBAL_STATES = {
            IDLE: 'idle',
            TEXT_PROCESSING: 'text_processing',  // 文本处理中（SSE + TTS）
            RECORDING: 'recording',
            VOICE_PROCESSING: 'voice_processing',
            CALLING: 'calling'
        };
        
        // 简化状态，移除中间状态
        this.currentState = this.GLOBAL_STATES.IDLE;
    }
    
    // 简化的状态映射
    getButtonStyles(state) {
        const states = {
            [this.GLOBAL_STATES.IDLE]: {
                textButton: { backgroundColor: '#1890ff', borderColor: '#1890ff' },
                textLoading: false,
                textDisabled: false,
                recordButton: { backgroundColor: '#1890ff', borderColor: '#1890ff' },
                recordDisabled: false,
                callButton: { backgroundColor: '#52c41a', borderColor: '#52c41a' },
                callDisabled: false
            },
            
            [this.GLOBAL_STATES.TEXT_PROCESSING]: {
                textButton: { backgroundColor: '#1890ff', borderColor: '#1890ff' },
                textLoading: true,
                textDisabled: true,
                recordButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                recordDisabled: true,
                callButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                callDisabled: true
            },
            
            [this.GLOBAL_STATES.RECORDING]: {
                textButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                textLoading: false,
                textDisabled: true,
                recordButton: { backgroundColor: '#ff4d4f', borderColor: '#ff4d4f' },
                recordDisabled: false,
                callButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                callDisabled: true
            },
            
            [this.GLOBAL_STATES.VOICE_PROCESSING]: {
                textButton: { backgroundColor: '#1890ff', borderColor: '#1890ff' },
                textLoading: true,
                textDisabled: true,
                recordButton: { backgroundColor: '#faad14', borderColor: '#faad14' },
                recordDisabled: true,
                callButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                callDisabled: true
            },
            
            [this.GLOBAL_STATES.CALLING]: {
                textButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                textLoading: false,
                textDisabled: true,
                recordButton: { backgroundColor: '#d9d9d9', borderColor: '#d9d9d9' },
                recordDisabled: true,
                callButton: { backgroundColor: '#ff4d4f', borderColor: '#ff4d4f' },
                callDisabled: false
            }
        };
        
        return states[state] || states[this.GLOBAL_STATES.IDLE];
    }
}
```

### 5. 修改状态更新逻辑

**修改文件**: `app.py` (clientside callback)

```javascript
// 简化的状态更新逻辑
function(text_clicks, sse_event, recording_event, current_state) {
    const ctx = dash_clientside.callback_context;
    if (!ctx.triggered || !window.unifiedButtonStateManager) {
        return window.dash_clientside.no_update;
    }
    
    const triggeredId = ctx.triggered[0].prop_id.split('.')[0];
    const manager = window.unifiedButtonStateManager;
    const now = Date.now();
    let newState = current_state || {state: 'idle', timestamp: 0};
    
    // 文本按钮点击
    if (triggeredId === 'ai-chat-x-send-btn') {
        if (!manager.checkInputContent()) return window.dash_clientside.no_update;
        newState = {
            state: 'text_processing',  // 简化：直接进入处理状态
            timestamp: now,
            metadata: {from_scenario: 'text', auto_play: manager.getAutoPlaySetting()}
        };
    }
    // SSE完成 + TTS完成
    else if (triggeredId === 'ai-chat-x-sse-completed-receiver') {
        newState = {state: 'idle', timestamp: now, metadata: {}};
    }
    // 外部事件处理...
    
    return newState;
}
```

## 实现步骤

### Phase 1: 创建TTS分块器 (1小时)
1. 创建 `services/tts_segmenter.py`
2. 实现智能分块逻辑
3. 测试分块效果

### Phase 2: 创建流式TTS管理器 (2小时)
1. 创建 `services/streaming_tts_manager.py`
2. 实现流式TTS处理逻辑
3. 集成WebSocket音频发送

### Phase 3: 修改SSE处理 (1小时)
1. 修改 `app.py` 中的SSE流式处理
2. 集成流式TTS管理器
3. 测试流式TTS效果

### Phase 4: 简化按钮状态 (1小时)
1. 修改 `unified_button_state_manager.js`
2. 简化状态映射
3. 修改状态更新逻辑

### Phase 5: 测试验证 (1小时)
1. 测试智能分块效果
2. 测试流式TTS响应
3. 测试按钮状态稳定性

## 预期效果

### 1. **TTS连贯性**
- 按标点符号分块，语义连贯
- 避免句子中间切断

### 2. **响应速度**
- SSE流式输出时立即TTS
- 不需要等所有文本输出完

### 3. **按钮状态稳定**
- 简化状态管理
- 避免TTS播放过程中的闪烁

### 4. **用户体验**
- 语音输出更自然
- 按钮状态更稳定
- 响应更迅速

## 技术优势

1. **语义感知**：按标点符号分块，保持语义完整性
2. **流式响应**：边输出边TTS，响应迅速
3. **状态简化**：减少中间状态，避免闪烁
4. **可扩展性**：支持更多分块策略和语音类型

这个方案怎么样？需要我开始实现吗？
