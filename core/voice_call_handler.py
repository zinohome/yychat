"""
语音通话处理器
专门处理实时语音通话功能，使用OpenAI Realtime API
"""

import asyncio
import base64
import time
import json
import os
import ssl
import websockets
from typing import Dict, Any, Optional
from utils.log import log
from core.websocket_manager import websocket_manager
from config.realtime_config import realtime_config
from adapters.personality_adapter import personality_adapter


class VoiceCallHandler:
    """语音通话处理器 - 专门处理实时语音通话"""
    
    def __init__(self):
        """初始化语音通话处理器"""
        # 活跃的语音通话连接
        self.active_calls = {}  # client_id -> call_info
        # Realtime API连接
        self.realtime_connections = {}  # client_id -> websocket
        # 消息处理任务
        self.message_tasks = {}  # client_id -> asyncio task
        # 🔧 关键修复：避免重复发送AI回复（response.audio_transcript.done 和 response.done 都会包含相同文本）
        self._assistant_text_sent = {}  # client_id -> {text: timestamp} 记录已发送的AI回复文本
        # 注意：OpenAI Realtime API在同一个连接中自动维护对话上下文
        # 不需要手动管理对话历史
        # 注意：只处理完成消息（completed/done），不处理delta增量消息，每轮对话只获取两次完整文本（用户一次，AI一次）
        
        log.info("语音通话处理器初始化完成")
    
    async def start_voice_call(self, client_id: str) -> bool:
        """
        开始语音通话
        
        Args:
            client_id: 客户端ID
            
        Returns:
            bool: 是否成功
        """
        try:
            log.info(f"开始语音通话: {client_id}")
            
            # 检查是否已有活跃通话
            if client_id in self.active_calls:
                log.warning(f"客户端 {client_id} 已有活跃通话")
                return False
            
            # 创建Realtime API连接
            success = await self._create_realtime_connection(client_id)
            if not success:
                return False
            
            # 记录通话信息
            self.active_calls[client_id] = {
                "start_time": time.time(),
                "status": "active",
                "message_count": 0
            }
            
            # 发送确认消息
            await websocket_manager.send_message(client_id, {
                "type": "voice_call_started",
                "message": "语音通话已开始，请开始说话",
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            log.info(f"语音通话启动成功: {client_id}")
            return True
            
        except Exception as e:
            log.error(f"启动语音通话失败: {client_id}, 错误: {e}")
            await self._send_error(client_id, f"启动语音通话失败: {str(e)}")
            return False
    
    async def stop_voice_call(self, client_id: str) -> bool:
        """
        停止语音通话
        
        Args:
            client_id: 客户端ID
            
        Returns:
            bool: 是否成功
        """
        try:
            log.info(f"🛑 停止语音通话: {client_id}")
            
            # 如果有活跃的Realtime连接，先发送停止响应信号
            if client_id in self.realtime_connections:
                try:
                    websocket = self.realtime_connections[client_id]
                    # 发送停止响应信号到OpenAI
                    stop_message = {
                        "type": "response.cancel"
                    }
                    await websocket.send(json.dumps(stop_message))
                    log.info(f"🛑 已发送停止响应信号到OpenAI: {client_id}")
                except Exception as e:
                    log.warning(f"发送停止信号失败: {client_id}, 错误: {e}")
            
            # 清理连接
            await self._cleanup_connection(client_id)
            
            # 移除通话记录
            if client_id in self.active_calls:
                del self.active_calls[client_id]
            
            # OpenAI Realtime API在连接关闭时自动清理上下文
            
            # 发送停止播放指令到前端
            await websocket_manager.send_message(client_id, {
                "type": "stop_playback",
                "message": "停止所有语音播放",
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            # 发送确认消息
            await websocket_manager.send_message(client_id, {
                "type": "voice_call_stopped",
                "message": "语音通话已停止",
                "timestamp": time.time(),
                "client_id": client_id
            })
            
            log.info(f"✅ 语音通话停止成功: {client_id}")
            return True
            
        except Exception as e:
            log.error(f"停止语音通话失败: {client_id}, 错误: {e}")
            await self._send_error(client_id, f"停止语音通话失败: {str(e)}")
            return False
    
    async def handle_audio_stream(self, client_id: str, audio_data: str = None, audio_base64: str = None) -> bool:
        """
        处理音频流数据 - 基于OpenAI Voice Agents最佳实践
        
        Args:
            client_id: 客户端ID
            audio_data: base64编码的音频数据（旧格式）
            audio_base64: base64编码的音频数据（新格式）
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查是否有活跃通话
            if client_id not in self.active_calls:
                log.warning(f"客户端 {client_id} 没有活跃的语音通话")
                return False
            
            # 检查Realtime连接
            if client_id not in self.realtime_connections:
                log.warning(f"客户端 {client_id} 没有Realtime API连接")
                return False
            
            # 获取音频数据（兼容两种格式）
            actual_audio_data = audio_base64 if audio_base64 else audio_data
            if not actual_audio_data:
                log.warning(f"客户端 {client_id} 没有提供音频数据")
                return False
            
            # 基于文档的优化：实时音频流处理
            websocket = self.realtime_connections[client_id]
            
            # 发送音频数据到Realtime API - 使用正确的消息格式
            audio_message = {
                "type": "input_audio_buffer.append",
                "audio": actual_audio_data
            }
            
            await websocket.send(json.dumps(audio_message))
            
            # 更新通话统计
            self.active_calls[client_id]["message_count"] += 1
            self.active_calls[client_id]["last_audio_time"] = time.time()
            
            # 检查音频数据质量
            audio_size = len(actual_audio_data)
            # 计算音频时间长度：PCM16格式，16kHz采样率，2字节/样本
            audio_duration_ms = (audio_size / 2) / 16000 * 1000  # 转换为毫秒
            
            if audio_size < 4000:  # 提高最小音频数据要求
                log.warning(f"⚠️ 音频数据太小: {client_id}, 大小: {audio_size}字节, 时长: {audio_duration_ms:.1f}ms, 建议至少4000字节")
            elif audio_size > 50000:
                log.warning(f"⚠️ 音频数据太大: {client_id}, 大小: {audio_size}字节, 时长: {audio_duration_ms:.1f}ms")
            elif audio_duration_ms < 100:
                log.warning(f"⚠️ 音频时长不足: {client_id}, 大小: {audio_size}字节, 时长: {audio_duration_ms:.1f}ms, 需要至少100ms")
            
            # 每100个音频包记录一次质量信息
            if self.active_calls[client_id]["message_count"] % 100 == 0:
                log.info(f"🎵 音频质量检查: {client_id}, 大小: {audio_size}字节, 时长: {audio_duration_ms:.1f}ms, 计数: {self.active_calls[client_id]['message_count']}")
            
            # 基于官方文档：让服务器端VAD自动处理语音检测
            # 不主动触发response.create，让turn_detection自动处理
            
            log.debug(f"发送音频数据到Realtime API: {client_id}, 数据大小: {len(actual_audio_data)}")
            #log.debug(f"音频消息内容: {audio_message}")
            return True
            
        except Exception as e:
            log.error(f"处理音频流失败: {client_id}, 错误: {e}")
            await self._send_error(client_id, f"处理音频流失败: {str(e)}")
            return False
    
    async def handle_audio_complete(self, client_id: str) -> bool:
        """
        处理音频完成信号 - 用户停止说话
        
        Args:
            client_id: 客户端ID
            
        Returns:
            bool: 是否成功
        """
        try:
            if client_id not in self.active_calls:
                log.warning(f"客户端 {client_id} 没有活跃的通话")
                return False
            
            if client_id not in self.realtime_connections:
                log.warning(f"客户端 {client_id} 没有Realtime API连接")
                return False
            
            websocket = self.realtime_connections[client_id]
            
            # 发送音频完成信号到Realtime API
            complete_message = {
                "type": "input_audio_buffer.commit"
            }
            
            await websocket.send(json.dumps(complete_message))
            log.info(f"🎤 用户停止说话，提交音频: {client_id}")
            
            # OpenAI Realtime API会自动维护对话上下文，无需手动记录
            
            # OpenAI Realtime API会自动处理音频并创建响应
            # 无需手动触发 response.create，避免重复响应
            log.debug(f"音频已提交，等待OpenAI自动响应: {client_id}")
            
            return True
            
        except Exception as e:
            log.error(f"处理音频完成失败: {client_id}, 错误: {e}")
            await self._send_error(client_id, f"处理音频完成失败: {str(e)}")
            return False
    
    async def handle_interrupt(self, client_id: str) -> bool:
        """
        处理打断信号 - 用户开始说话打断AI回复
        
        Args:
            client_id: 客户端ID
            
        Returns:
            bool: 是否成功
        """
        try:
            if client_id not in self.active_calls:
                log.warning(f"客户端 {client_id} 没有活跃的通话")
                return False
            
            if client_id not in self.realtime_connections:
                log.warning(f"客户端 {client_id} 没有Realtime API连接")
                return False
            
            websocket = self.realtime_connections[client_id]
            
            # 发送取消信号到Realtime API，停止当前响应
            cancel_message = {
                "type": "response.cancel"
            }
            
            await websocket.send(json.dumps(cancel_message))
            log.info(f"🛑 用户打断AI回复，停止当前响应: {client_id}")
            
            # 发送确认消息到前端
            await websocket_manager.send_message(client_id, {
                "type": "interrupt_confirmed",
                "message": "已停止当前回复，等待新的输入",
                "timestamp": time.time()
            })
            
            return True
            
        except Exception as e:
            log.error(f"处理打断信号失败: {client_id}, 错误: {e}")
            await self._send_error(client_id, f"处理打断信号失败: {str(e)}")
            return False
    
    async def _create_realtime_connection(self, client_id: str) -> bool:
        """
        创建Realtime API连接 - 基于OpenAI Voice Agents最佳实践
        
        Args:
            client_id: 客户端ID
            
        Returns:
            bool: 是否成功
        """
        try:
            # 获取OpenAI API密钥 - 使用realtime_config中的配置
            api_key = realtime_config.OPENAI_API_KEY
            if not api_key:
                raise Exception("OpenAI API key not configured")
            
            # 构建连接URL和头部
            url = realtime_config.get_realtime_url()
            headers = {
                "Authorization": f"Bearer {api_key}",
                "OpenAI-Beta": "realtime=v1",
                "User-Agent": "YYChat-VoiceAgent/1.0"
            }
            
            # 建立WebSocket连接 - 修复SSL和参数问题
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            websocket = await websockets.connect(
                url, 
                additional_headers=headers,
                ping_interval=20,  # 保持连接活跃
                ping_timeout=10,   # 快速检测断线
                close_timeout=5,    # 快速关闭
                ssl=ssl_context  # 使用自定义SSL上下文（仅用于开发环境）
            )
            self.realtime_connections[client_id] = websocket
            
            # 启动消息处理任务
            task = asyncio.create_task(self._handle_realtime_messages(client_id, websocket))
            self.message_tasks[client_id] = task
            
            # 连接建立后，立即发送session.update配置
            await self._configure_session(client_id, websocket)
            
            log.info(f"Realtime API连接已建立: {client_id}")
            return True
            
        except Exception as e:
            log.error(f"创建Realtime API连接失败: {client_id}, 错误: {e}")
            # 发送错误消息到前端
            await self._send_error(client_id, f"语音通话连接失败: {str(e)}")
            return False
    
    async def _configure_session(self, client_id: str, websocket):
        """
        配置Realtime API会话 - 动态使用当前personality
        
        Args:
            client_id: 客户端ID
            websocket: WebSocket连接
        """
        try:
            # 获取当前personality配置
            personality_config = self._get_current_personality_config()
            
            # 基于personality配置会话
            instructions = personality_config["instructions"]
            log.info(f"🎯 发送给OpenAI的instructions: {instructions[:200]}...")
            
            # 根据官方文档，session.update的正确格式
            # 注意：OpenAI Realtime API不支持session.messages参数
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["audio", "text"],
                    "instructions": instructions,
                    "voice": "shimmer",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.2,  # 进一步降低阈值，适应低音量环境
                        "prefix_padding_ms": 600,  # 增加前缀填充，捕获更多语音
                        "silence_duration_ms": 400,  # 增加静音时间，确保完整语音
                        "idle_timeout_ms": 30000,  # 添加空闲超时
                        "create_response": True,  # 允许创建响应
                        "interrupt_response": True  # 允许打断响应
                    },
                    "input_audio_transcription": {
                        "model": "whisper-1"  # 启用转录功能
                    },
                    "tools": [],
                    "tool_choice": "none",
                    "temperature": 0.8,
                    "max_response_output_tokens": 4096
                }
            }
            
            await websocket.send(json.dumps(session_config))
            log.debug(f"会话配置已发送: {client_id}")
            log.info(f"📤 发送的session配置: {json.dumps(session_config, ensure_ascii=False)[:300]}...")
            
        except Exception as e:
            log.error(f"配置会话失败: {client_id}, 错误: {e}")
            raise
    
    def _get_current_personality_config(self) -> Dict[str, Any]:
        """
        获取当前personality配置
        
        Returns:
            Dict[str, Any]: personality配置
        """
        try:
            # 尝试获取当前用户选择的personality
            # 这里可以从session或用户配置中获取
            # 暂时使用health_assistant作为默认值
            personality_id = "health_assistant"
            
            # 通过personality_adapter获取配置
            personality_config = personality_adapter.get_personality_for_realtime(personality_id)
            
            if not personality_config:
                log.warning("无法获取personality配置，使用默认配置")
                return self._get_default_personality_config()
            
            log.info(f"成功获取personality配置: {personality_id}")
            instructions = personality_config.get('instructions', '')
            log.debug(f"Personality instructions: {instructions[:200]}...")
            log.info(f"🎯 当前使用的instructions: {instructions[:100]}...")
            return personality_config
            
        except Exception as e:
            log.error(f"获取personality配置失败: {e}")
            return self._get_default_personality_config()
    
    def _get_default_personality_config(self) -> Dict[str, Any]:
        """
        获取默认personality配置
        
        Returns:
            Dict[str, Any]: 默认配置
        """
        return {
            "instructions": "你是一个友好的AI助手，可以进行实时语音对话。请直接回答用户的问题，保持简洁自然。",
            "voice": "shimmer",
            "allowed_tools": []
        }
    
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
                    await self._process_realtime_response(client_id, data, websocket)
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
            await self._cleanup_connection(client_id)
    
    async def _process_realtime_response(self, client_id: str, data: dict, websocket):
        """
        处理Realtime API响应
        
        Args:
            client_id: 客户端ID
            data: 响应数据
            websocket: WebSocket连接
        """
        try:
            message_type = data.get("type")
            
            # 处理日志显示，截断过长的delta内容
            log_data = data.copy()
            if "delta" in log_data and isinstance(log_data["delta"], str):
                delta_content = log_data["delta"]
                if len(delta_content) > 15:
                    log_data["delta"] = delta_content[:15] + "..."
            
            log.debug(f"收到Realtime API消息: {client_id}, 类型: {message_type}, 数据: {log_data}")
            
            # 🔍 调试：记录所有消息类型，特别是转录相关的
            if "transcription" in message_type.lower() or "input_audio" in message_type.lower():
                log.info(f"🔍 [调试] 收到可能与转录相关的消息: {client_id}, 类型: {message_type}")
            
            if message_type == "response.audio.delta":
                # 处理音频输出 - 语音通话的核心功能
                audio_data = data.get("delta", "")
                if audio_data:
                    log.info(f"🎵 收到AI音频数据: {client_id}, 数据大小: {len(audio_data)}")
                    await websocket_manager.send_message(client_id, {
                        "type": "audio_stream",
                        "audio": audio_data,
                        "message_id": f"voice_call_{client_id}_{int(time.time())}",
                        "session_id": f"voice_call_{client_id}",
                        "timestamp": time.time()
                    })
            
            # 🔧 关键修复：移除所有delta增量处理，只处理完成消息
            # 不处理 response.text.delta、response.audio_transcript.delta 等增量消息
            # 只处理完成消息（completed/done），每轮对话只获取两次完整文本（用户一次，AI一次）
            
            elif message_type == "input_audio_buffer.speech_started":
                # 服务器端VAD检测到语音开始
                log.info(f"🎤 服务器端VAD检测到语音开始: {client_id}")
                
            elif message_type == "input_audio_buffer.speech_stopped":
                # 服务器端VAD检测到语音结束
                log.info(f"🎤 服务器端VAD检测到语音结束: {client_id}")
            
            elif message_type == "conversation.item.input_audio_transcription.completed":
                # 🔧 用户转录完成 - OpenAI Realtime API的完成消息（每轮对话只获取一次完整文本）
                # 根据OpenAI文档：https://platform.openai.com/docs/guides/realtime-conversations
                # 这是用户语音转文本的完成消息，包含完整的transcript字段
                transcribed_text = data.get("transcript", "")  # OpenAI文档：字段名是 transcript
                log.info(f"📝 [用户转录完成] 收到conversation.item.input_audio_transcription.completed: {client_id}, 文本长度: {len(transcribed_text) if transcribed_text else 0}")
                
                if transcribed_text and realtime_config.VOICE_CALL_SEND_TRANSCRIPTION:
                    current_time = time.time()
                    log.info(f"📝 [用户转录] 完整文本: {client_id}, 文本: {transcribed_text[:50]}...")
                    await websocket_manager.send_message(client_id, {
                        "type": "transcription_result",
                        "text": transcribed_text,  # 用户转录文本
                        "timestamp": current_time,
                        "client_id": client_id,
                        "scenario": "voice_call",
                        "message_id": f"voice-call-user-{client_id}-{int(current_time * 1000)}",
                        "role": "user"  # 明确标识为用户消息
                    })
                    log.info(f"✅ [用户转录] 已发送完整文本到前端: {client_id}, 文本长度: {len(transcribed_text)}")
                else:
                    log.warning(f"⚠️ [用户转录] 未发送: 文本为空={not transcribed_text}, 配置禁用={not realtime_config.VOICE_CALL_SEND_TRANSCRIPTION}")
            
            elif message_type == "input_audio_buffer.transcription.completed":
                # 备用：旧版API的消息类型（兼容性）
                transcribed_text = data.get("text", "")  # 旧版API可能使用text字段
                log.info(f"📝 [用户转录完成-旧版] 收到input_audio_buffer.transcription.completed: {client_id}, 文本长度: {len(transcribed_text) if transcribed_text else 0}")
                
                if transcribed_text and realtime_config.VOICE_CALL_SEND_TRANSCRIPTION:
                    current_time = time.time()
                    log.info(f"📝 [用户转录-旧版] 完整文本: {client_id}, 文本: {transcribed_text[:50]}...")
                    await websocket_manager.send_message(client_id, {
                        "type": "transcription_result",
                        "text": transcribed_text,
                        "timestamp": current_time,
                        "client_id": client_id,
                        "scenario": "voice_call",
                        "message_id": f"voice-call-user-{client_id}-{int(current_time * 1000)}",
                        "role": "user"  # 明确标识为用户消息
                    })
                    log.info(f"✅ [用户转录-旧版] 已发送完整文本到前端: {client_id}, 文本长度: {len(transcribed_text)}")
            
            elif message_type == "input_audio_buffer.transcription.failed":
                # 转录失败
                error = data.get("error", {})
                error_message = error.get("message", "Unknown error")
                log.warning(f"⚠️ 用户转录失败: {client_id}, 错误: {error_message}")
                
            elif message_type == "response.audio_transcript.done":
                # 🔧 AI音频转录完成 - OpenAI Realtime API的完成消息（每轮对话只获取一次完整文本）
                # 根据OpenAI文档：这是AI回复音频转文本的完成消息，包含完整的transcript字段
                assistant_text = data.get("transcript", "")  # OpenAI文档：字段名是 transcript
                log.info(f"🔍 [AI转录完成] 收到response.audio_transcript.done: {client_id}, transcript长度: {len(assistant_text) if assistant_text else 0}")
                
                if assistant_text and realtime_config.VOICE_CALL_INCLUDE_ASSISTANT_TEXT:
                    # 🔧 关键修复：检查是否已经发送过相同的文本（避免重复显示，因为response.done可能也会包含相同文本）
                    current_time = time.time()
                    if client_id not in self._assistant_text_sent:
                        self._assistant_text_sent[client_id] = {}
                    
                    # 检查是否在5秒内发送过相同文本（同一轮对话的AI回复）
                    text_key = assistant_text.strip()
                    if text_key in self._assistant_text_sent[client_id]:
                        sent_time = self._assistant_text_sent[client_id][text_key]
                        if current_time - sent_time < 5.0:  # 5秒内的重复文本不发送
                            log.info(f"⚠️ [AI转录] 已发送过相同的文本（{current_time - sent_time:.2f}秒前），跳过发送: {client_id}")
                            return
                    
                    # 记录已发送的文本和时间戳
                    self._assistant_text_sent[client_id][text_key] = current_time
                    # 清理5秒前的记录（避免内存泄漏）
                    for key, ts in list(self._assistant_text_sent[client_id].items()):
                        if current_time - ts > 5.0:
                            del self._assistant_text_sent[client_id][key]
                    
                    display_text = assistant_text[:50] + "..." if len(assistant_text) > 50 else assistant_text
                    log.info(f"📝 [AI转录] 完整文本: {client_id}, 文本: {display_text}")
                    # 发送AI回复文本到前端
                    await websocket_manager.send_message(client_id, {
                        "type": "transcription_result",
                        "text": assistant_text,  # AI回复文本
                        "assistant_text": assistant_text,  # 明确标识为AI回复
                        "timestamp": current_time,
                        "client_id": client_id,
                        "scenario": "voice_call",
                        "message_id": f"voice-call-assistant-{client_id}-{int(current_time * 1000)}",
                        "role": "assistant"  # 明确标识为AI回复
                    })
                    log.info(f"✅ [AI转录] 已发送完整文本到前端: {client_id}, 文本长度: {len(assistant_text)}")
            
            elif message_type == "response.done":
                # 🔧 响应完成 - 作为备选方案（如果response.audio_transcript.done没有包含文本）
                # 根据OpenAI文档：response.done包含完整的响应信息，包括AI回复的transcript
                # 注意：如果response.audio_transcript.done已经发送了文本，这里会被跳过（避免重复）
                log.info(f"🔍 [响应完成] 收到response.done: {client_id}")
                response_data = data.get("response", {})
                output_items = response_data.get("output", [])
                assistant_text = None
                
                # 从response.output中提取AI回复文本（作为备选方案）
                for item in output_items:
                    if item.get("role") == "assistant":
                        content_list = item.get("content", [])
                        for content_item in content_list:
                            if content_item.get("type") == "audio":
                                transcript = content_item.get("transcript", "")
                                if transcript:
                                    assistant_text = transcript
                                    log.info(f"🔍 [响应完成] 从response.output中提取到transcript: {client_id}, 文本长度: {len(transcript)}, 文本: {transcript[:100]}")
                                    break
                        if assistant_text:
                            break
                
                if assistant_text and realtime_config.VOICE_CALL_INCLUDE_ASSISTANT_TEXT:
                    # 🔧 关键修复：检查是否已经发送过相同的文本（避免重复显示）
                    current_time = time.time()
                    if client_id not in self._assistant_text_sent:
                        self._assistant_text_sent[client_id] = {}
                    
                    # 检查是否在5秒内发送过相同文本（同一轮对话的AI回复）
                    text_key = assistant_text.strip()
                    if text_key in self._assistant_text_sent[client_id]:
                        sent_time = self._assistant_text_sent[client_id][text_key]
                        if current_time - sent_time < 5.0:  # 5秒内的重复文本不发送
                            log.info(f"⚠️ [响应完成] 已发送过相同的文本（{current_time - sent_time:.2f}秒前），跳过发送: {client_id}")
                            return
                    
                    # 记录已发送的文本和时间戳
                    self._assistant_text_sent[client_id][text_key] = current_time
                    # 清理5秒前的记录（避免内存泄漏）
                    for key, ts in list(self._assistant_text_sent[client_id].items()):
                        if current_time - ts > 5.0:
                            del self._assistant_text_sent[client_id][key]
                    
                    display_text = assistant_text[:50] + "..." if len(assistant_text) > 50 else assistant_text
                    log.info(f"📝 [响应完成] 完整文本: {client_id}, 文本: {display_text}")
                    # 发送AI回复文本到前端
                    await websocket_manager.send_message(client_id, {
                        "type": "transcription_result",
                        "text": assistant_text,  # AI回复文本
                        "assistant_text": assistant_text,  # 明确标识为AI回复
                        "timestamp": current_time,
                        "client_id": client_id,
                        "scenario": "voice_call",
                        "message_id": f"voice-call-assistant-{client_id}-{int(current_time * 1000)}",
                        "role": "assistant"  # 明确标识为AI回复
                    })
                    log.info(f"✅ [响应完成] 已发送完整文本到前端: {client_id}, 文本长度: {len(assistant_text)}")
                else:
                    log.debug(f"[响应完成] 未找到AI回复文本: {client_id}")
                
            elif message_type == "response.created":
                # 响应创建
                log.debug(f"响应创建: {client_id}")
                
            elif message_type == "input_audio_buffer.speech_started":
                # 检测到语音开始
                log.debug(f"检测到语音开始: {client_id}")
                
            elif message_type == "input_audio_buffer.speech_stopped":
                # 检测到语音结束
                log.debug(f"检测到语音结束: {client_id}")
                
            elif message_type == "session.created":
                # 会话已创建
                log.info(f"📋 收到session.created事件: {client_id}")
                
            elif message_type == "session.updated":
                # 会话配置已更新
                log.info(f"✅ 会话配置已更新: {client_id}")
                
            elif message_type == "error":
                # 处理错误
                error_info = data.get("error", {})
                error_message = error_info.get("message", "Unknown error")
                await self._send_error(client_id, f"Realtime API错误: {error_message}")
            
        except Exception as e:
            log.error(f"处理Realtime API响应失败: {client_id}, 错误: {e}")
    
    async def _cleanup_connection(self, client_id: str):
        """
        清理连接
        
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
            if client_id in self.message_tasks:
                task = self.message_tasks[client_id]
                task.cancel()
                del self.message_tasks[client_id]
            
            # 清理AI回复文本相关数据
            if client_id in self._assistant_text_sent:
                del self._assistant_text_sent[client_id]
            
            log.info(f"连接已清理: {client_id}")
            
        except Exception as e:
            log.error(f"清理连接失败: {client_id}, 错误: {e}")
    
    async def _send_error(self, client_id: str, error_message: str):
        """
        发送错误消息
        
        Args:
            client_id: 客户端ID
            error_message: 错误消息
        """
        try:
            await websocket_manager.send_message(client_id, {
                "type": "error",
                "error": {
                    "message": error_message,
                    "type": "voice_call_error",
                    "code": "processing_failed"
                },
                "timestamp": time.time(),
                "client_id": client_id
            })
        except Exception as e:
            log.error(f"发送错误消息失败: {client_id}, 错误: {e}")
    
    def get_active_calls(self) -> Dict[str, Any]:
        """
        获取活跃通话列表
        
        Returns:
            Dict: 活跃通话信息
        """
        return self.active_calls.copy()
    
    def is_call_active(self, client_id: str) -> bool:
        """
        检查是否有活跃通话
        
        Args:
            client_id: 客户端ID
            
        Returns:
            bool: 是否有活跃通话
        """
        return client_id in self.active_calls


# 创建全局语音通话处理器实例
voice_call_handler = VoiceCallHandler()
