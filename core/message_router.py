"""
消息路由系统
负责将不同类型的消息路由到对应的处理器
"""

import json
from typing import Dict, Callable, Any, Optional
from utils.log import log
from core.websocket_manager import websocket_manager


class MessageRouter:
    """消息路由器"""
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self.middleware: list = []
    
    def register_handler(self, message_type: str, handler: Callable):
        """
        注册消息处理器
        
        Args:
            message_type: 消息类型
            handler: 处理函数
        """
        if message_type in self.handlers:
            log.warning(f"消息类型 {message_type} 的处理器已存在，将被覆盖")
        
        self.handlers[message_type] = handler
        log.info(f"注册消息处理器: {message_type}")
    
    def register_middleware(self, middleware: Callable):
        """
        注册中间件
        
        Args:
            middleware: 中间件函数
        """
        self.middleware.append(middleware)
        log.info(f"注册中间件: {middleware.__name__}")
    
    async def route_message(self, client_id: str, message: dict) -> bool:
        """
        路由消息到对应的处理器
        
        Args:
            client_id: 客户端ID
            message: 消息内容
            
        Returns:
            bool: 处理是否成功
        """
        try:
            # 验证消息格式
            if not self._validate_message(message):
                await self._send_error_response(client_id, "Invalid message format")
                return False
            
            message_type = message.get("type")
            if not message_type:
                await self._send_error_response(client_id, "Missing message type")
                return False
            
            # 执行中间件
            for middleware in self.middleware:
                try:
                    result = await middleware(client_id, message)
                    if result is False:  # 中间件返回False表示停止处理
                        return False
                except Exception as e:
                    log.error(f"中间件执行失败: {middleware.__name__}, 错误: {e}")
                    continue
            
            # 查找处理器
            if message_type not in self.handlers:
                await self._send_error_response(client_id, f"Unknown message type: {message_type}")
                return False
            
            # 执行处理器
            handler = self.handlers[message_type]
            try:
                await handler(client_id, message)
                log.debug(f"消息处理成功: {client_id} -> {message_type}")
                return True
            except Exception as e:
                log.error(f"消息处理失败: {client_id} -> {message_type}, 错误: {e}")
                await self._send_error_response(client_id, f"Message processing failed: {str(e)}")
                return False
                
        except Exception as e:
            log.error(f"消息路由失败: {client_id}, 错误: {e}")
            await self._send_error_response(client_id, "Message routing failed")
            return False
    
    def _validate_message(self, message: dict) -> bool:
        """
        验证消息格式
        
        Args:
            message: 消息内容
            
        Returns:
            bool: 验证是否通过
        """
        if not isinstance(message, dict):
            return False
        
        # 检查必需字段
        required_fields = ["type"]
        for field in required_fields:
            if field not in message:
                return False
        
        # 检查消息类型
        message_type = message.get("type")
        if not isinstance(message_type, str) or not message_type.strip():
            return False
        
        return True
    
    async def _send_error_response(self, client_id: str, error_message: str):
        """
        发送错误响应
        
        Args:
            client_id: 客户端ID
            error_message: 错误消息
        """
        error_response = {
            "type": "error",
            "error": {
                "message": error_message,
                "type": "message_processing_error",
                "code": "invalid_message"
            },
            "timestamp": __import__("time").time()
        }
        
        await websocket_manager.send_message(client_id, error_response)
    
    def get_registered_handlers(self) -> Dict[str, str]:
        """
        获取已注册的处理器列表
        
        Returns:
            Dict[str, str]: 消息类型到处理器名称的映射
        """
        return {
            message_type: handler.__name__ 
            for message_type, handler in self.handlers.items()
        }
    
    def get_middleware_list(self) -> list:
        """
        获取中间件列表
        
        Returns:
            list: 中间件名称列表
        """
        return [middleware.__name__ for middleware in self.middleware]


# 创建全局消息路由器实例
message_router = MessageRouter()


# 基础消息处理器
async def handle_heartbeat(client_id: str, message: dict):
    """处理心跳消息"""
    await websocket_manager.handle_heartbeat_response(client_id)
    await websocket_manager.send_message(client_id, {
        "type": "heartbeat_response",
        "timestamp": __import__("time").time(),
        "client_id": client_id
    })


async def handle_ping(client_id: str, message: dict):
    """处理ping消息"""
    await websocket_manager.send_message(client_id, {
        "type": "pong",
        "timestamp": __import__("time").time(),
        "client_id": client_id
    })


async def handle_get_status(client_id: str, message: dict):
    """处理状态查询消息"""
    stats = websocket_manager.get_connection_stats()
    await websocket_manager.send_message(client_id, {
        "type": "status_response",
        "data": stats,
        "timestamp": __import__("time").time(),
        "client_id": client_id
    })


# 注册基础处理器
message_router.register_handler("heartbeat", handle_heartbeat)
message_router.register_handler("ping", handle_ping)
message_router.register_handler("get_status", handle_get_status)

# 注册文本消息处理器
from handlers.text_message_handler import handle_text_message
message_router.register_handler("text_message", handle_text_message)

# 注册实时消息处理器
from core.realtime_handler import realtime_handler

async def handle_audio_input(client_id: str, message: dict):
    """处理音频输入消息"""
    return await realtime_handler.handle_message(client_id, message)

async def handle_audio_stream(client_id: str, message: dict):
    """处理音频流消息"""
    return await realtime_handler.handle_message(client_id, message)

async def handle_voice_command(client_id: str, message: dict):
    """处理语音命令消息"""
    return await realtime_handler.handle_message(client_id, message)

async def handle_status_query(client_id: str, message: dict):
    """处理状态查询消息"""
    return await realtime_handler.handle_message(client_id, message)

message_router.register_handler("audio_input", handle_audio_input)
message_router.register_handler("audio_stream", handle_audio_stream)
message_router.register_handler("voice_command", handle_voice_command)
message_router.register_handler("status_query", handle_status_query)
