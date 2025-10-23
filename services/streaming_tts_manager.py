import asyncio
import base64
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List
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
        self.current_seq = 0  # 当前序列号
        self.executor = ThreadPoolExecutor(max_workers=3)  # 线程池处理TTS
    
    def process_streaming_text(self, text_chunk: str, client_id: str, 
                             session_id: str, message_id: str, voice: str = "shimmer"):
        """
        处理流式文本，智能分块并立即TTS（非阻塞）
        
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
            
            # 处理完整的分块（线程池执行，不等待）
            for i, segment in enumerate(segments[:-1]):  # 除了最后一个
                self.executor.submit(self._synthesize_and_send_sync, segment, client_id, session_id, message_id, voice, self.current_seq)
                self.current_seq += 1
            
            # 保留最后一个不完整的分块
            self.pending_segments = [segments[-1]] if segments else []
        
        # 检查是否需要强制分块（无标点符号但达到长度阈值）
        elif self.segmenter.should_force_split(current_text):
            # 强制分块
            segments = self.segmenter.segment_with_force_split(current_text)
            
            # 处理完整的分块（线程池执行，不等待）
            for i, segment in enumerate(segments[:-1]):  # 除了最后一个
                self.executor.submit(self._synthesize_and_send_sync, segment, client_id, session_id, message_id, voice, self.current_seq)
                self.current_seq += 1
            
            # 保留最后一个不完整的分块
            self.pending_segments = [segments[-1]] if segments else []
    
    async def finalize_tts(self, client_id: str, session_id: str, message_id: str, voice: str = "shimmer"):
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
                await self._synthesize_and_send(remaining_text, client_id, session_id, message_id, voice, self.current_seq)
                self.current_seq += 1
        
        # 发送完成信号
        await websocket_manager.send_synthesis_complete(client_id, session_id=session_id, message_id=message_id)
        log.info(f"TTS streaming completed: client_id={client_id}, session_id={session_id}, total_segments={self.current_seq}")
    
    def _synthesize_and_send_sync(self, text: str, client_id: str, session_id: str, 
                                 message_id: str, voice: str, seq: int):
        """
        合成并发送TTS音频（同步版本，用于线程池）
        
        Args:
            text: 文本内容
            client_id: 客户端ID
            session_id: 会话ID
            message_id: 消息ID
            voice: 语音类型
            seq: 序列号
        """
        try:
            # 在新的事件循环中运行异步函数
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._synthesize_and_send(text, client_id, session_id, message_id, voice, seq))
            finally:
                loop.close()
            
        except Exception as e:
            log.error(f"TTS synthesis failed: {e}")
    
    async def _synthesize_and_send(self, text: str, client_id: str, session_id: str, 
                                 message_id: str, voice: str, seq: int):
        """
        合成并发送TTS音频（异步版本）
        
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
    
    def reset(self):
        """重置管理器状态"""
        self.pending_segments = []
        self.is_processing = False
        self.current_seq = 0
