"""
文本消息处理器
处理WebSocket文本消息，集成现有的chat_engine
"""

import json
import time
from typing import Dict, Any, Optional
from utils.log import log
from config.config import get_config
from core.websocket_manager import websocket_manager
from core.chat_engine import ChatEngine
from core.engine_manager import get_current_engine
from schemas.api_schemas import ChatCompletionRequest


class TextMessageHandler:
    """文本消息处理器"""
    
    def __init__(self):
        self.chat_engine = None
        self._initialized = False
        log.info("文本消息处理器创建完成（延迟初始化）")
    
    def _initialize_chat_engine(self):
        """初始化聊天引擎"""
        try:
            self.chat_engine = get_current_engine()
            if self.chat_engine:
                log.info("文本消息处理器初始化成功")
                self._initialized = True
            else:
                log.debug("聊天引擎未设置，将在首次使用时重试")
        except Exception as e:
            log.error(f"文本消息处理器初始化失败: {e}")
            self.chat_engine = None
    
    async def handle(self, client_id: str, message: dict) -> bool:
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
            
            # 验证消息格式
            if not self._validate_text_message(message):
                await self._send_error_response(client_id, "Invalid text message format")
                return False
            
            # 提取消息内容
            text_content = message.get("content", "")
            conversation_id = message.get("conversation_id")
            personality_id = message.get("personality_id")
            use_tools = message.get("use_tools", True)
            stream = message.get("stream", True)
            
            # 构建聊天请求
            chat_request = self._build_chat_request(
                text_content, conversation_id, personality_id, use_tools, stream
            )
            
            # 发送处理开始消息
            await self._send_processing_start(client_id)
            
            # 处理聊天请求
            if stream:
                await self._handle_streaming_response(client_id, chat_request)
            else:
                await self._handle_non_streaming_response(client_id, chat_request)
            
            return True
            
        except Exception as e:
            log.error(f"文本消息处理失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Text processing failed: {str(e)}")
            return False
    
    def _validate_text_message(self, message: dict) -> bool:
        """
        验证文本消息格式
        
        Args:
            message: 消息内容
            
        Returns:
            bool: 验证是否通过
        """
        if not isinstance(message, dict):
            return False
        
        # 检查必需字段
        if "content" not in message:
            return False
        
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            return False
        
        return True
    
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
    
    async def _handle_streaming_response(self, client_id: str, chat_request: ChatCompletionRequest):
        """
        处理流式响应
        
        Args:
            client_id: 客户端ID
            chat_request: 聊天请求
        """
        try:
            # 根据配置决定是否通过WS发送文本流事件（方案B默认关闭）
            config = get_config()
            ws_text_enabled = getattr(config, "VOICE_DISABLE_WS_TEXT", True) is False
            if ws_text_enabled:
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
                    if ws_text_enabled:
                        # 发送内容块（仅在允许WS文本时）
                        await websocket_manager.send_message(client_id, {
                            "type": "stream_chunk",
                            "content": content,
                            "timestamp": time.time(),
                            "client_id": client_id
                        })
            
            if ws_text_enabled:
                # 发送流式响应结束消息
                await websocket_manager.send_message(client_id, {
                    "type": "stream_end",
                    "full_content": full_content,
                    "timestamp": time.time(),
                    "client_id": client_id
                })
            
        except Exception as e:
            log.error(f"流式响应处理失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Streaming response failed: {str(e)}")
    
    async def _handle_non_streaming_response(self, client_id: str, chat_request: ChatCompletionRequest):
        """
        处理非流式响应
        
        Args:
            client_id: 客户端ID
            chat_request: 聊天请求
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
            
            # 非流式文本通过WS返回也受同一开关控制（默认关闭）
            config = get_config()
            if getattr(config, "VOICE_DISABLE_WS_TEXT", True) is False:
                await websocket_manager.send_message(client_id, {
                    "type": "text_response",
                    "content": response.get("content", ""),
                    "conversation_id": chat_request.conversation_id,
                    "timestamp": time.time(),
                    "client_id": client_id
                })
            
        except Exception as e:
            log.error(f"非流式响应处理失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, f"Non-streaming response failed: {str(e)}")
    
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
                "type": "text_processing_error",
                "code": "text_processing_failed"
            },
            "timestamp": time.time(),
            "client_id": client_id
        })


# 创建全局文本消息处理器实例
text_message_handler = TextMessageHandler()


# 注册到消息路由器
async def handle_text_message(client_id: str, message: dict):
    """处理文本消息的包装函数"""
    await text_message_handler.handle(client_id, message)
