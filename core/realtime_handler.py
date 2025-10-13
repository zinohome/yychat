"""
实时消息处理器
处理WebSocket实时消息，集成音频、文本和现有功能
"""

import asyncio
import base64
import time
from typing import Dict, Any, Optional, List
from utils.log import log
from core.websocket_manager import websocket_manager
from core.chat_engine import ChatEngine
from core.engine_manager import get_current_engine
from services.audio_service import audio_service
from services.voice_personality_service import voice_personality_service
from schemas.api_schemas import ChatCompletionRequest


class RealtimeMessageHandler:
    """实时消息处理器"""
    
    def __init__(self):
        """初始化实时消息处理器"""
        self.chat_engine = None
        self._initialize_chat_engine()
        log.info("实时消息处理器初始化成功")
    
    def _initialize_chat_engine(self):
        """初始化聊天引擎"""
        try:
            self.chat_engine = get_current_engine()
            if self.chat_engine:
                log.info("实时消息处理器聊天引擎初始化成功")
            else:
                log.warning("聊天引擎未设置，将在首次使用时重试")
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
                return await self._handle_audio_stream(client_id, message)
            elif message_type == "voice_command":
                return await self._handle_voice_command(client_id, message)
            elif message_type == "status_query":
                return await self._handle_status_query(client_id, message)
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
            if not self.chat_engine:
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
            
            # 如果启用了自动回复，继续处理文本
            auto_reply = message.get("auto_reply", True)
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
    
    async def _handle_audio_stream(self, client_id: str, message: dict) -> bool:
        """
        处理音频流
        
        Args:
            client_id: 客户端ID
            message: 消息内容
            
        Returns:
            bool: 处理是否成功
        """
        try:
            # 音频流处理逻辑
            # 这里可以实现实时音频流处理
            log.info(f"处理音频流: {client_id}")
            
            # 发送确认消息
            await websocket_manager.send_message(client_id, {
                "type": "audio_stream_ack",
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            return True
            
        except Exception as e:
            log.error(f"音频流处理失败: {client_id}, 错误: {e}")
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


# 创建全局实时消息处理器实例
realtime_handler = RealtimeMessageHandler()
