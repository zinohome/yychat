"""
实时消息处理器
处理WebSocket实时消息，集成音频、文本和现有功能
"""

import asyncio
import base64
import time
import json
import os
import websockets
from typing import Dict, Any, Optional, List
from utils.log import log
from core.websocket_manager import websocket_manager
from core.chat_engine import ChatEngine
from core.engine_manager import get_current_engine
from core.voice_activity_detector import VoiceActivityDetector
from core.audio_stream_buffer import AudioStreamBuffer
from core.parallel_audio_processor import ParallelAudioProcessor
from services.audio_service import audio_service
from services.voice_personality_service import voice_personality_service
from schemas.api_schemas import ChatCompletionRequest
from config.realtime_config import realtime_config


class RealtimeMessageHandler:
    """实时消息处理器"""
    
    def __init__(self):
        """初始化实时消息处理器"""
        self.chat_engine = None
        self._initialized = False
        
        # Initialize VAD and audio processing components
        self.vad = VoiceActivityDetector(aggressiveness=2, silence_threshold=10)
        self.audio_buffer = AudioStreamBuffer(max_size=100, chunk_duration=0.1)
        self.audio_processor = ParallelAudioProcessor(max_workers=4, timeout_seconds=30.0)
        
        # Speech state tracking
        self.speech_segments = {}  # client_id -> speech state
        
        # Realtime API connections
        self.realtime_connections = {}  # client_id -> websocket connection
        self.realtime_tasks = {}  # client_id -> asyncio task
        
        self._initialize_chat_engine()
        log.info("实时消息处理器初始化成功")
    
    def _initialize_chat_engine(self):
        """初始化聊天引擎"""
        try:
            self.chat_engine = get_current_engine()
            if self.chat_engine:
                log.info("实时消息处理器聊天引擎初始化成功")
                self._initialized = True
            else:
                log.debug("聊天引擎未设置，将在首次使用时重试")
        except Exception as e:
            log.error(f"实时消息处理器聊天引擎初始化失败: {e}")
            self.chat_engine = None
    
    async def handle_message(self, client_id: str, message: dict) -> bool:
        """
        处理实时消息
        
        Args:
            client_id: 客户端ID
            message: 消息内容
            
        Returns:
            bool: 处理是否成功
        """
        try:
            message_type = message.get("type")
            log.info(f"实时消息处理器收到消息: {client_id} -> {message_type}")
            
            if not message_type:
                await self._send_error_response(client_id, "Missing message type")
                return False
            
            # 根据消息类型分发处理
            if message_type == "audio_input":
                return await self._handle_audio_input(client_id, message)
            elif message_type == "audio_stream":
                return await self._handle_audio_stream_message(client_id, message)
            elif message_type == "voice_command":
                return await self._handle_voice_command(client_id, message)
            elif message_type == "status_query":
                return await self._handle_status_query(client_id, message)
            elif message_type == "start_realtime_dialogue":
                return await self._handle_start_realtime_dialogue(client_id, message)
            elif message_type == "stop_realtime_dialogue":
                return await self._handle_stop_realtime_dialogue(client_id, message)
            else:
                await self._send_error_response(client_id, f"Unknown message type: {message_type}")
                return False
                
        except Exception as e:
            log.error(f"实时消息处理失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Message processing failed: {str(e)}")
            return False
    
    async def _handle_text_message(self, client_id: str, message: dict) -> bool:
        """
        处理文本消息
        
        Args:
            client_id: 客户端ID
            message: 消息内容
            
        Returns:
            bool: 处理是否成功
        """
        try:
            # 如果引擎未初始化，尝试重新初始化
            if not self._initialized:
                self._initialize_chat_engine()
                if not self.chat_engine:
                    await self._send_error_response(client_id, "Chat engine not available")
                    return False
            
            # 提取消息内容
            text_content = message.get("content", "")
            conversation_id = message.get("conversation_id")
            personality_id = message.get("personality_id")
            use_tools = message.get("use_tools", True)
            stream = message.get("stream", True)
            enable_voice = message.get("enable_voice", False)
            
            if not text_content.strip():
                await self._send_error_response(client_id, "Text content cannot be empty")
                return False
            
            # 构建聊天请求
            chat_request = self._build_chat_request(
                text_content, conversation_id, personality_id, use_tools, stream
            )
            
            # 发送处理开始消息
            await self._send_processing_start(client_id)
            
            # 处理聊天请求
            if stream:
                await self._handle_streaming_response(client_id, chat_request, enable_voice, personality_id)
            else:
                await self._handle_non_streaming_response(client_id, chat_request, enable_voice, personality_id)
            
            return True
            
        except Exception as e:
            log.error(f"文本消息处理失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Text processing failed: {str(e)}")
            return False
    
    async def _handle_audio_input(self, client_id: str, message: dict) -> bool:
        """
        处理音频输入
        
        Args:
            client_id: 客户端ID
            message: 消息内容
            
        Returns:
            bool: 处理是否成功
        """
        try:
            # 提取音频数据
            audio_data_b64 = message.get("audio_data")
            if not audio_data_b64:
                await self._send_error_response(client_id, "Audio data is required")
                return False
            
            # 解码音频数据
            try:
                audio_data = base64.b64decode(audio_data_b64)
            except Exception as e:
                await self._send_error_response(client_id, f"Invalid audio data format: {e}")
                return False
            
            # 发送音频处理开始消息
            await websocket_manager.send_message(client_id, {
                "type": "audio_processing_start",
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            # 语音转文本
            transcribed_text = await audio_service.transcribe_audio(audio_data)
            
            # 发送转录结果
            await websocket_manager.send_message(client_id, {
                "type": "transcription_result",
                "text": transcribed_text,
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            # 如果启用了自动回复，继续处理文本（方案B默认关闭）
            from config.config import get_config
            config = get_config()
            default_auto_reply = getattr(config, "STT_AUTO_REPLY_DEFAULT", False)
            auto_reply = message.get("auto_reply", default_auto_reply)
            if auto_reply:
                # 构建文本消息并处理
                text_message = {
                    "type": "text_message",
                    "content": transcribed_text,
                    "conversation_id": message.get("conversation_id"),
                    "personality_id": message.get("personality_id"),
                    "use_tools": message.get("use_tools", True),
                    "stream": message.get("stream", True),
                    "enable_voice": message.get("enable_voice", True)
                }
                await self._handle_text_message(client_id, text_message)
            
            return True
            
        except Exception as e:
            log.error(f"音频输入处理失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Audio processing failed: {str(e)}")
            return False
    
    async def _handle_audio_stream_message(self, client_id: str, message: dict) -> bool:
        """
        处理音频流消息（WebM格式）- 使用OpenAI Realtime API
        
        Args:
            client_id: 客户端ID
            message: 消息内容
            
        Returns:
            bool: 处理是否成功
        """
        try:
            audio_data = message.get("audio_data")
            audio_format = message.get("format", "unknown")
            
            if not audio_data:
                await self._send_error_response(client_id, "Missing audio data")
                return False
            
            # Decode base64 audio data
            log.info(f"收到音频数据: client={client_id}, format={audio_format}, size={len(audio_data)} bytes (base64)")
            
            try:
                audio_bytes = base64.b64decode(audio_data)
                log.info(f"解码后音频大小: {len(audio_bytes)} bytes")
            except Exception as e:
                log.error(f"Base64 decode failed: {e}")
                await self._send_error_response(client_id, f"Invalid audio data format: {str(e)}")
                return False
            
            # 使用OpenAI Realtime API处理音频流
            log.info(f"开始使用Realtime API处理音频片段: {client_id}")
            await self._process_realtime_audio(client_id, audio_bytes)
            
            # 发送确认消息
            await websocket_manager.send_message(client_id, {
                "type": "audio_stream_ack",
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            return True
            
        except Exception as e:
            log.error(f"音频流消息处理失败: {client_id}, 错误: {e}")
            import traceback
            log.error(f"Traceback: {traceback.format_exc()}")
            await self._send_error_response(client_id, f"Audio stream processing failed: {str(e)}")
            return False
    
    async def _handle_voice_command(self, client_id: str, message: dict) -> bool:
        """
        处理语音命令
        
        Args:
            client_id: 客户端ID
            message: 消息内容
            
        Returns:
            bool: 处理是否成功
        """
        try:
            command = message.get("command", "")
            if not command:
                await self._send_error_response(client_id, "Voice command is required")
                return False
            
            # 处理语音命令
            if command == "start_recording":
                await self._handle_start_recording(client_id)
            elif command == "stop_recording":
                await self._handle_stop_recording(client_id)
            elif command == "clear_conversation":
                await self._handle_clear_conversation(client_id, message)
            elif command == "change_voice":
                await self._handle_change_voice(client_id, message)
            else:
                await self._send_error_response(client_id, f"Unknown voice command: {command}")
                return False
            
            return True
            
        except Exception as e:
            log.error(f"语音命令处理失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Voice command processing failed: {str(e)}")
            return False
    
    async def _handle_status_query(self, client_id: str, message: dict) -> bool:
        """
        处理状态查询
        
        Args:
            client_id: 客户端ID
            message: 消息内容
            
        Returns:
            bool: 处理是否成功
        """
        try:
            query_type = message.get("query_type", "general")
            
            if query_type == "connection":
                stats = websocket_manager.get_connection_stats()
                await websocket_manager.send_message(client_id, {
                    "type": "status_response",
                    "data": stats,
                    "timestamp": time.time(),
                    "client_id": client_id
                })
            elif query_type == "audio_cache":
                cache_stats = audio_service.audio_cache.get_stats()
                await websocket_manager.send_message(client_id, {
                    "type": "audio_cache_stats",
                    "data": cache_stats,
                    "timestamp": time.time(),
                    "client_id": client_id
                })
            else:
                await self._send_error_response(client_id, f"Unknown query type: {query_type}")
                return False
            
            return True
            
        except Exception as e:
            log.error(f"状态查询处理失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Status query processing failed: {str(e)}")
            return False
    
    def _build_chat_request(self, content: str, conversation_id: Optional[str], 
                          personality_id: Optional[str], use_tools: bool, stream: bool) -> ChatCompletionRequest:
        """
        构建聊天请求
        
        Args:
            content: 文本内容
            conversation_id: 对话ID
            personality_id: 人格ID
            use_tools: 是否使用工具
            stream: 是否流式响应
            
        Returns:
            ChatCompletionRequest: 聊天请求对象
        """
        messages = [
            {
                "role": "user",
                "content": content
            }
        ]
        
        return ChatCompletionRequest(
            model="gpt-4o-mini",  # 默认模型
            messages=messages,
            conversation_id=conversation_id,
            personality_id=personality_id,
            use_tools=use_tools,
            stream=stream,
            temperature=0.7,
            max_tokens=1000
        )
    
    async def _handle_streaming_response(self, client_id: str, chat_request: ChatCompletionRequest, 
                                       enable_voice: bool, personality_id: Optional[str]):
        """
        处理流式响应
        
        Args:
            client_id: 客户端ID
            chat_request: 聊天请求
            enable_voice: 是否启用语音
            personality_id: 人格ID
        """
        try:
            # 发送流式响应开始消息
            await websocket_manager.send_message(client_id, {
                "type": "stream_start",
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            # 获取流式响应
            response_stream = await self.chat_engine.generate_response(
                messages=chat_request.messages,
                conversation_id=chat_request.conversation_id or "default",
                personality_id=chat_request.personality_id,
                use_tools=chat_request.use_tools,
                stream=True
            )
            
            full_content = ""
            async for chunk in response_stream:
                if isinstance(chunk, dict) and "content" in chunk:
                    content = chunk["content"]
                    full_content += content
                    
                    # 发送内容块
                    await websocket_manager.send_message(client_id, {
                        "type": "stream_chunk",
                        "content": content,
                        "timestamp": time.time(),
                        "client_id": client_id
                    })
            
            # 发送流式响应结束消息
            await websocket_manager.send_message(client_id, {
                "type": "stream_end",
                "full_content": full_content,
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            # 如果启用语音，生成语音响应
            if enable_voice and full_content.strip():
                await self._handle_voice_response(client_id, full_content, personality_id)
            
        except Exception as e:
            log.error(f"流式响应处理失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Streaming response failed: {str(e)}")
    
    async def _handle_non_streaming_response(self, client_id: str, chat_request: ChatCompletionRequest,
                                           enable_voice: bool, personality_id: Optional[str]):
        """
        处理非流式响应
        
        Args:
            client_id: 客户端ID
            chat_request: 聊天请求
            enable_voice: 是否启用语音
            personality_id: 人格ID
        """
        try:
            # 获取非流式响应
            response = await self.chat_engine.generate_response(
                messages=chat_request.messages,
                conversation_id=chat_request.conversation_id or "default",
                personality_id=chat_request.personality_id,
                use_tools=chat_request.use_tools,
                stream=False
            )
            
            content = response.get("content", "")
            
            # 发送完整响应
            await websocket_manager.send_message(client_id, {
                "type": "text_response",
                "content": content,
                "conversation_id": chat_request.conversation_id,
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            # 如果启用语音，生成语音响应
            if enable_voice and content.strip():
                await self._handle_voice_response(client_id, content, personality_id)
            
        except Exception as e:
            log.error(f"非流式响应处理失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Non-streaming response failed: {str(e)}")
    
    async def _handle_voice_response(self, client_id: str, text: str, personality_id: Optional[str]):
        """
        处理语音响应
        
        Args:
            client_id: 客户端ID
            text: 要转换的文本
            personality_id: 人格ID
        """
        try:
            # 获取对应的语音类型
            voice = voice_personality_service.get_voice_for_personality(personality_id)
            
            # 发送语音生成开始消息
            await websocket_manager.send_message(client_id, {
                "type": "voice_generation_start",
                "voice": voice,
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            # 生成语音
            audio_data = await audio_service.synthesize_speech(text, voice)
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            # 发送语音响应
            await websocket_manager.send_message(client_id, {
                "type": "voice_response",
                "audio_data": audio_b64,
                "voice": voice,
                "text": text,
                "timestamp": time.time(),
                "client_id": client_id
            })
            
        except Exception as e:
            log.error(f"语音响应处理失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Voice response failed: {str(e)}")
    
    async def _handle_start_recording(self, client_id: str):
        """处理开始录音命令"""
        await websocket_manager.send_message(client_id, {
            "type": "recording_started",
            "timestamp": time.time(),
            "client_id": client_id
        })
    
    async def _handle_stop_recording(self, client_id: str):
        """处理停止录音命令"""
        await websocket_manager.send_message(client_id, {
            "type": "recording_stopped",
            "timestamp": time.time(),
            "client_id": client_id
        })
    
    async def _handle_audio_stream(self, client_id: str, audio_chunk: bytes):
        """
        处理实时音频流数据
        
        Args:
            client_id: 客户端ID
            audio_chunk: 音频数据块
        """
        try:
            # Add chunk to buffer
            await self.audio_buffer.add_chunk(client_id, audio_chunk)
            
            # Process with VAD
            speech_change = self.vad.process_audio_stream(client_id, audio_chunk)
            
            if speech_change is True:
                # Speech started
                await self._handle_speech_start(client_id)
            elif speech_change is False:
                # Speech ended
                await self._handle_speech_end(client_id)
                
        except Exception as e:
            import traceback
            log.error(f"音频流处理失败: {client_id}, 错误: {type(e).__name__}: {e}")
            log.error(f"Traceback: {traceback.format_exc()}")
            await self._send_error_response(client_id, f"Audio stream processing failed: {str(e)}")
    
    async def _handle_speech_start(self, client_id: str):
        """处理语音开始"""
        try:
            # Update speech state
            self.speech_segments[client_id] = {
                'is_speaking': True,
                'speech_start': time.time(),
                'last_activity': time.time()
            }
            
            # Notify client
            await websocket_manager.send_message(client_id, {
                "type": "speech_started",
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            log.debug(f"语音开始: {client_id}")
            
        except Exception as e:
            log.error(f"语音开始处理失败: {client_id}, 错误: {e}")
    
    async def _handle_speech_end(self, client_id: str):
        """处理语音结束"""
        try:
            # Get complete audio data
            audio_data = await self.audio_buffer.get_complete_audio(client_id, clear_buffer=True)
            
            if not audio_data:
                log.warning(f"语音结束但无音频数据: {client_id}")
                return
            
            # Update speech state
            if client_id in self.speech_segments:
                self.speech_segments[client_id]['is_speaking'] = False
                speech_duration = time.time() - self.speech_segments[client_id].get('speech_start', time.time())
                log.debug(f"语音结束: {client_id}, 时长: {speech_duration:.2f}s")
            
            # Process complete speech
            await self._process_complete_speech(client_id, audio_data)
            
        except Exception as e:
            log.error(f"语音结束处理失败: {client_id}, 错误: {e}")
    
    async def _process_complete_speech(self, client_id: str, audio_data: bytes):
        """
        处理完整的语音数据
        
        Args:
            client_id: 客户端ID
            audio_data: 完整音频数据
        """
        try:
            # Define callback functions for parallel processing
            async def stt_callback(audio_bytes: bytes) -> str:
                """Speech-to-text callback"""
                return await audio_service.transcribe_audio(audio_bytes)
            
            async def ai_callback(text: str) -> str:
                """AI processing callback"""
                if not self.chat_engine:
                    self._initialize_chat_engine()
                    if not self.chat_engine:
                        raise Exception("Chat engine not available")
                
                # Build chat request
                chat_request = self._build_chat_request(
                    content=text,
                    conversation_id=f"voice_{client_id}",
                    personality_id=None,
                    use_tools=True,
                    stream=False
                )
                
                # Get AI response
                response = await self.chat_engine.create_chat_completion(chat_request)
                return response.choices[0].message.content
            
            async def tts_callback(text: str) -> bytes:
                """Text-to-speech callback"""
                return await audio_service.synthesize_speech(text, voice="alloy")
            
            # Process audio in parallel
            result = await self.audio_processor.process_audio_async(
                client_id=client_id,
                audio_data=audio_data,
                stt_callback=stt_callback,
                ai_callback=ai_callback,
                tts_callback=tts_callback
            )
            
            if result.success:
                # Send text response
                await websocket_manager.send_message(client_id, {
                    "type": "text_response",
                    "text": result.response,
                    "timestamp": time.time(),
                    "client_id": client_id
                })
                
                # Send audio response
                if result.audio_data:
                    audio_b64 = base64.b64encode(result.audio_data).decode('utf-8')
                    await websocket_manager.send_message(client_id, {
                        "type": "voice_response",
                        "audio_data": audio_b64,
                        "text": result.response,
                        "timestamp": time.time(),
                        "client_id": client_id
                    })
                
                log.info(f"语音处理完成: {client_id}, 处理时间: {result.processing_time:.2f}s")
            else:
                log.error(f"语音处理失败: {client_id}, 错误: {result.error}")
                await self._send_error_response(client_id, f"Speech processing failed: {result.error}")
                
        except Exception as e:
            log.error(f"完整语音处理失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Complete speech processing failed: {str(e)}")
    
    async def cleanup_client(self, client_id: str):
        """清理客户端资源"""
        try:
            # Cancel any active processing
            await self.audio_processor.cancel_processing(client_id)
            
            # Clear audio buffer
            await self.audio_buffer.clear_buffer(client_id)
            
            # Clear VAD state
            self.vad.clear_client_state(client_id)
            
            # Clear speech segments
            if client_id in self.speech_segments:
                del self.speech_segments[client_id]
            
            log.debug(f"客户端资源清理完成: {client_id}")
            
        except Exception as e:
            log.error(f"客户端资源清理失败: {client_id}, 错误: {e}")
    
    def get_processing_statistics(self) -> dict:
        """获取处理统计信息"""
        return {
            'vad_stats': self.vad.get_speech_statistics(),
            'buffer_stats': self.audio_buffer.get_statistics(),
            'processor_stats': self.audio_processor.get_statistics(),
            'active_speakers': self.vad.get_active_speakers(),
            'speech_segments': len(self.speech_segments)
        }
    
    async def _handle_clear_conversation(self, client_id: str, message: dict):
        """处理清除对话命令"""
        conversation_id = message.get("conversation_id")
        if conversation_id and self.chat_engine:
            try:
                await self.chat_engine.clear_conversation_memory(conversation_id)
                await websocket_manager.send_message(client_id, {
                    "type": "conversation_cleared",
                    "conversation_id": conversation_id,
                    "timestamp": time.time(),
                    "client_id": client_id
                })
            except Exception as e:
                await self._send_error_response(client_id, f"Failed to clear conversation: {e}")
        else:
            await self._send_error_response(client_id, "Invalid conversation ID")
    
    async def _handle_change_voice(self, client_id: str, message: dict):
        """处理改变语音命令"""
        voice = message.get("voice")
        personality_id = message.get("personality_id")
        
        if voice and personality_id:
            success = voice_personality_service.set_voice_for_personality(personality_id, voice)
            if success:
                await websocket_manager.send_message(client_id, {
                    "type": "voice_changed",
                    "voice": voice,
                    "personality_id": personality_id,
                    "timestamp": time.time(),
                    "client_id": client_id
                })
            else:
                await self._send_error_response(client_id, "Failed to change voice")
        else:
            await self._send_error_response(client_id, "Voice and personality_id are required")
    
    async def _send_processing_start(self, client_id: str):
        """发送处理开始消息"""
        await websocket_manager.send_message(client_id, {
            "type": "processing_start",
            "timestamp": time.time(),
            "client_id": client_id
        })
    
    async def _send_error_response(self, client_id: str, error_message: str):
        """发送错误响应"""
        await websocket_manager.send_message(client_id, {
            "type": "error",
            "error": {
                "message": error_message,
                "type": "realtime_processing_error",
                "code": "processing_failed"
            },
            "timestamp": time.time(),
            "client_id": client_id
        })
    
    async def _handle_start_realtime_dialogue(self, client_id: str, message: dict) -> bool:
        """
        处理开始实时语音对话
        
        Args:
            client_id: 客户端ID
            message: 消息内容
            
        Returns:
            bool: 处理是否成功
        """
        try:
            log.info(f"开始实时语音对话: {client_id}")
            
            # 初始化客户端的语音状态
            if client_id not in self.speech_segments:
                self.speech_segments[client_id] = {
                    "is_active": True,
                    "start_time": time.time(),
                    "last_activity": time.time()
                }
            else:
                self.speech_segments[client_id]["is_active"] = True
                self.speech_segments[client_id]["start_time"] = time.time()
                self.speech_segments[client_id]["last_activity"] = time.time()
            
            # 启动音频流处理
            await self._start_audio_stream_processing(client_id)
            
            # 发送确认消息
            await websocket_manager.send_message(client_id, {
                "type": "realtime_dialogue_started",
                "message": "实时语音对话已启动，请开始说话",
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            log.info(f"实时语音对话启动成功: {client_id}")
            return True
            
        except Exception as e:
            log.error(f"启动实时语音对话失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Failed to start realtime dialogue: {str(e)}")
            return False
    
    async def _handle_stop_realtime_dialogue(self, client_id: str, message: dict) -> bool:
        """
        处理停止实时语音对话
        
        Args:
            client_id: 客户端ID
            message: 消息内容
            
        Returns:
            bool: 处理是否成功
        """
        try:
            log.info(f"停止实时语音对话: {client_id}")
            
            # 停止客户端的语音状态
            if client_id in self.speech_segments:
                self.speech_segments[client_id]["is_active"] = False
                self.speech_segments[client_id]["end_time"] = time.time()
            
            # 清理Realtime API连接
            await self._cleanup_realtime_connection(client_id)
            
            # 发送确认消息
            await websocket_manager.send_message(client_id, {
                "type": "realtime_dialogue_stopped",
                "message": "实时语音对话已停止",
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            log.info(f"实时语音对话停止成功: {client_id}")
            return True
            
        except Exception as e:
            log.error(f"停止实时语音对话失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Failed to stop realtime dialogue: {str(e)}")
            return False
    
    async def _start_audio_stream_processing(self, client_id: str):
        """
        启动音频流处理
        
        Args:
            client_id: 客户端ID
        """
        try:
            log.info(f"启动音频流处理: {client_id}")
            
            # VAD和音频缓冲会在首次使用时自动初始化，无需手动初始化
            # VoiceActivityDetector.process_audio_stream 会在第一次调用时初始化 speech_segments 和 frame_buffers
            # AudioStreamBuffer.add_chunk 会在第一次调用时初始化 buffers, locks, sequence_counters, client_metadata
            # 这样可以确保所有相关字典都被正确初始化，避免初始化不完整导致的 KeyError
            
            # 启动并行处理器
            if client_id not in self.audio_processor.processing_tasks:
                self.audio_processor.processing_tasks[client_id] = []
            
            # 发送音频流启动指令到前端
            await websocket_manager.send_message(client_id, {
                "type": "start_audio_stream",
                "message": "请开始说话，系统正在监听",
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            log.info(f"音频流处理启动成功: {client_id}")
            
        except Exception as e:
            log.error(f"启动音频流处理失败: {client_id}, 错误: {e}")
    
    async def _process_realtime_audio(self, client_id: str, audio_data: bytes):
        """
        使用OpenAI Realtime API处理音频数据
        
        Args:
            client_id: 客户端ID
            audio_data: 音频数据
        """
        try:
            # 如果客户端没有Realtime连接，创建一个
            if client_id not in self.realtime_connections:
                await self._create_realtime_connection(client_id)
            
            # 发送音频数据到Realtime API
            if client_id in self.realtime_connections:
                websocket = self.realtime_connections[client_id]
                
                # 发送音频数据
                audio_message = {
                    "type": "conversation.item.input_audio_buffer.append",
                    "audio": base64.b64encode(audio_data).decode('utf-8')
                }
                
                await websocket.send(json.dumps(audio_message))
                log.debug(f"发送音频数据到Realtime API: {client_id}")
            
        except Exception as e:
            log.error(f"Realtime API音频处理失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Realtime audio processing failed: {str(e)}")
    
    async def _create_realtime_connection(self, client_id: str):
        """
        为客户端创建Realtime API连接
        
        Args:
            client_id: 客户端ID
        """
        try:
            # 获取OpenAI API密钥 - 使用config.py中的配置
            from config.config import Config
            api_key = Config.OPENAI_API_KEY
            if not api_key:
                raise Exception("OpenAI API key not configured")
            
            # 构建Realtime API URL
            url = realtime_config.get_realtime_url()
            headers = {
                "Authorization": f"Bearer {api_key}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            # 建立WebSocket连接
            websocket = await websockets.connect(url, extra_headers=headers)
            self.realtime_connections[client_id] = websocket
            
            # 启动消息处理任务
            task = asyncio.create_task(self._handle_realtime_messages(client_id, websocket))
            self.realtime_tasks[client_id] = task
            
            # 发送会话创建消息
            session_create = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": "你是一个友好的AI助手，可以进行实时语音对话。",
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 200
                    },
                    "tools": [],
                    "tool_choice": "auto",
                    "temperature": 0.8,
                    "max_response_output_tokens": 4096
                }
            }
            
            await websocket.send(json.dumps(session_create))
            log.info(f"Realtime API连接已建立: {client_id}")
            
        except Exception as e:
            log.error(f"创建Realtime API连接失败: {client_id}, 错误: {e}")
            raise
    
    async def _handle_realtime_messages(self, client_id: str, websocket):
        """
        处理Realtime API返回的消息
        
        Args:
            client_id: 客户端ID
            websocket: WebSocket连接
        """
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._process_realtime_response(client_id, data)
                except json.JSONDecodeError as e:
                    log.error(f"解析Realtime API消息失败: {e}")
                except Exception as e:
                    log.error(f"处理Realtime API消息失败: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            log.info(f"Realtime API连接已关闭: {client_id}")
        except Exception as e:
            log.error(f"Realtime API消息处理异常: {client_id}, 错误: {e}")
        finally:
            # 清理连接
            await self._cleanup_realtime_connection(client_id)
    
    async def _process_realtime_response(self, client_id: str, data: dict):
        """
        处理Realtime API响应
        
        Args:
            client_id: 客户端ID
            data: 响应数据
        """
        try:
            message_type = data.get("type")
            
            if message_type == "conversation.item.output_audio_buffer.delta":
                # 处理音频输出
                audio_data = data.get("delta", "")
                if audio_data:
                    # 发送音频数据到前端
                    await websocket_manager.send_message(client_id, {
                        "type": "audio_stream",
                        "audio": audio_data,
                        "message_id": f"realtime_{client_id}_{int(time.time())}",
                        "session_id": f"realtime_{client_id}",
                        "timestamp": time.time()
                    })
            
            elif message_type == "conversation.item.output_text.delta":
                # 处理文本输出
                text_delta = data.get("delta", "")
                if text_delta:
                    # 发送文本数据到前端
                    await websocket_manager.send_message(client_id, {
                        "type": "stream_chunk",
                        "content": text_delta,
                        "timestamp": time.time(),
                        "client_id": client_id
                    })
            
            elif message_type == "conversation.item.output_text.committed":
                # 处理文本提交
                text = data.get("text", "")
                if text:
                    await websocket_manager.send_message(client_id, {
                        "type": "stream_end",
                        "full_content": text,
                        "timestamp": time.time(),
                        "client_id": client_id
                    })
            
            elif message_type == "error":
                # 处理错误
                error_info = data.get("error", {})
                error_message = error_info.get("message", "Unknown error")
                await self._send_error_response(client_id, f"Realtime API error: {error_message}")
            
        except Exception as e:
            log.error(f"处理Realtime API响应失败: {client_id}, 错误: {e}")
    
    async def _cleanup_realtime_connection(self, client_id: str):
        """
        清理Realtime API连接
        
        Args:
            client_id: 客户端ID
        """
        try:
            # 关闭WebSocket连接
            if client_id in self.realtime_connections:
                websocket = self.realtime_connections[client_id]
                await websocket.close()
                del self.realtime_connections[client_id]
            
            # 取消任务
            if client_id in self.realtime_tasks:
                task = self.realtime_tasks[client_id]
                task.cancel()
                del self.realtime_tasks[client_id]
            
            log.info(f"Realtime API连接已清理: {client_id}")
            
        except Exception as e:
            log.error(f"清理Realtime API连接失败: {client_id}, 错误: {e}")


# 创建全局实时消息处理器实例
realtime_handler = RealtimeMessageHandler()
