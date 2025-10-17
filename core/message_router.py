"""
消息路由系统
负责将不同类型的消息路由到对应的处理器
"""

import json
import time
from typing import Dict, Callable, Any, Optional, List
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
            # 首先检查连接是否仍然活跃
            if not websocket_manager.is_connection_active(client_id):
                log.warning(f"客户端连接已不活跃，跳过消息处理: {client_id}")
                return False
            
            # 验证消息格式
            if not self._validate_message(message):
                await self._send_error_response(client_id, "Invalid message format")
                return False
            
            # 防串台验证：检查消息中的client_id是否匹配
            message_client_id = message.get("client_id")
            if message_client_id and message_client_id != client_id:
                log.warning(f"消息client_id不匹配: 消息中={message_client_id}, 连接中={client_id}")
                await self._send_error_response(client_id, "Client ID mismatch")
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
                # 注释掉心跳消息处理成功的日志，减少日志噪音
                if message_type not in ['heartbeat', 'heartbeat_response']:
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
        验证消息格式和防串台机制
        
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
        
        # 防串台验证：检查client_id
        client_id = message.get("client_id")
        if client_id and not isinstance(client_id, str):
            log.warning(f"无效的client_id类型: {type(client_id)}")
            return False
        
        # 防串台验证：检查session_id
        session_id = message.get("session_id")
        if session_id and not isinstance(session_id, str):
            log.warning(f"无效的session_id类型: {type(session_id)}")
            return False
        
        return True
    
    async def _handle_interrupt(self, client_id: str, message: dict):
        """
        处理中断消息
        """
        try:
            session_id = message.get("session_id")
            message_id = message.get("message_id")
            interrupt_type = message.get("interrupt_type", "user_interrupt")
            
            log.info(f"收到中断请求: client_id={client_id}, session_id={session_id}, message_id={message_id}, type={interrupt_type}")
            
            # 发送中断确认通知
            await websocket_manager.send_interrupt_notification(
                client_id,
                session_id=session_id,
                message_id=message_id,
                interrupt_type=interrupt_type
            )
            
            # 这里可以添加更多中断逻辑，比如停止正在进行的TTS等
            log.info(f"中断处理完成: {client_id}")
            
        except Exception as e:
            log.error(f"处理中断消息失败: {e}")
            raise
    
    async def _send_error_response(self, client_id: str, error_message: str):
        """
        发送错误响应
        
        Args:
            client_id: 客户端ID
            error_message: 错误消息
        """
        # 检查连接是否仍然活跃
        if not websocket_manager.is_connection_active(client_id):
            log.warning(f"客户端连接已不活跃，跳过错误响应发送: {client_id}")
            return
        
        error_response = {
            "type": "error",
            "error": {
                "message": error_message,
                "type": "message_processing_error",
                "code": "invalid_message"
            },
            "timestamp": __import__("time").time()
        }
        
        try:
            await websocket_manager.send_message(client_id, error_response)
        except Exception as e:
            log.warning(f"发送错误响应失败: {client_id}, 错误: {e}")
    
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


# 注意：消息处理器注册已移至app.py的lifespan事件中，避免重复注册

# 导出处理器函数供lifespan使用
async def handle_audio_input(client_id: str, message: dict):
    """处理音频输入消息"""
    try:
        from core.realtime_handler import realtime_handler
        return await realtime_handler.handle_message(client_id, message)
    except Exception as e:
        log.error(f"音频输入处理失败: {client_id}, 错误: {e}")
        from core.websocket_manager import websocket_manager
        await websocket_manager.send_message(client_id, {
            "type": "error",
            "message": f"Audio processing failed: {str(e)}",
            "timestamp": time.time()
        })
        return False

async def handle_audio_stream(client_id: str, message: dict):
    """处理音频流消息"""
    from core.realtime_handler import realtime_handler
    return await realtime_handler.handle_message(client_id, message)

async def handle_voice_command(client_id: str, message: dict):
    """处理语音命令消息"""
    from core.realtime_handler import realtime_handler
    return await realtime_handler.handle_message(client_id, message)

async def handle_status_query(client_id: str, message: dict):
    """处理状态查询消息"""
    from core.realtime_handler import realtime_handler
    return await realtime_handler.handle_message(client_id, message)
