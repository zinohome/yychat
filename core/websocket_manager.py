"""
WebSocket管理器
负责管理WebSocket连接、消息发送和连接状态监控
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from utils.log import log
from config.websocket_config import websocket_config


class ConnectionInfo:
    """连接信息类"""
    
    def __init__(self, websocket: WebSocket, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.connected_at = time.time()
        self.last_heartbeat = time.time()
        self.message_count = 0
        self.is_active = True
        self.metadata = {}
    
    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = time.time()
    
    def increment_message_count(self):
        """增加消息计数"""
        self.message_count += 1
    
    def is_connection_stale(self, timeout: int = None) -> bool:
        """检查连接是否过期"""
        if timeout is None:
            timeout = websocket_config.CONNECTION_TIMEOUT
        return time.time() - self.last_heartbeat > timeout


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, ConnectionInfo] = {}
        self.connection_metadata: Dict[str, dict] = {}
        self._cleanup_task = None
        self._cleanup_started = False
    
    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """
        建立WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
            client_id: 客户端ID
            
        Returns:
            bool: 连接是否成功
        """
        try:
            # 启动清理任务（如果还没有启动）
            if not self._cleanup_started:
                self._start_cleanup_task()
            
            # 检查连接数限制
            if len(self.active_connections) >= websocket_config.MAX_CONNECTIONS:
                log.warning(f"连接数已达上限 {websocket_config.MAX_CONNECTIONS}，拒绝新连接")
                return False
            
            # 如果客户端已存在，先断开旧连接
            if client_id in self.active_connections:
                await self.disconnect(client_id)
            
            # 接受WebSocket连接
            await websocket.accept()
            
            # 创建连接信息
            connection_info = ConnectionInfo(websocket, client_id)
            self.active_connections[client_id] = connection_info
            
            log.info(f"WebSocket连接已建立: {client_id}")
            
            # 发送连接确认消息（直接发送，避免递归调用）
            try:
                connection_established_message = {
                    "type": "connection_established",
                    "client_id": client_id,
                    "timestamp": time.time(),
                    "message": "连接已建立"
                }
                message_str = json.dumps(connection_established_message)
                await websocket.send_text(message_str)
                connection_info.increment_message_count()
                log.debug(f"连接确认消息已发送到 {client_id}")
            except Exception as e:
                log.warning(f"发送连接确认消息失败: {client_id}, 错误: {e}")
            
            return True
            
        except Exception as e:
            log.error(f"WebSocket连接失败: {client_id}, 错误: {e}")
            return False
    
    async def disconnect(self, client_id: str):
        """
        断开WebSocket连接
        
        Args:
            client_id: 客户端ID
        """
        if client_id in self.active_connections:
            connection_info = self.active_connections[client_id]
            
            # 标记连接为不活跃，避免重复处理
            connection_info.is_active = False
            
            try:
                # 尝试发送断开连接消息（如果连接仍然可用）
                await self.send_message(client_id, {
                    "type": "connection_closed",
                    "client_id": client_id,
                    "timestamp": time.time(),
                    "message": "连接已关闭"
                })
            except Exception as e:
                # 连接可能已经关闭，这是正常的
                log.debug(f"发送断开连接消息失败（连接可能已关闭）: {client_id}, 错误: {e}")
            
            try:
                # 尝试关闭WebSocket连接
                await connection_info.websocket.close()
            except Exception as e:
                # 连接可能已经关闭，这是正常的
                log.debug(f"关闭WebSocket连接时出错（连接可能已关闭）: {client_id}, 错误: {e}")
            
            finally:
                # 清理连接信息
                del self.active_connections[client_id]
                if client_id in self.connection_metadata:
                    del self.connection_metadata[client_id]
                
                log.info(f"WebSocket连接已断开: {client_id}")
    
    async def send_message(self, client_id: str, message: dict) -> bool:
        """
        发送消息给指定客户端
        
        Args:
            client_id: 客户端ID
            message: 消息内容
            
        Returns:
            bool: 发送是否成功
        """
        # 首先检查客户端是否存在
        if client_id not in self.active_connections:
            log.warning(f"客户端不存在: {client_id}")
            return False
        
        connection_info = self.active_connections[client_id]
        
        # 检查连接是否仍然活跃
        if not connection_info.is_active:
            log.warning(f"客户端连接已不活跃: {client_id}")
            return False
        
        try:
            # 检查消息大小
            message_str = json.dumps(message)
            if len(message_str) > websocket_config.MESSAGE_SIZE_LIMIT:
                log.error(f"消息过大: {len(message_str)} bytes")
                return False
            
            # 发送前输出结构化日志，便于排查串音
            msg_type = message.get("type", "unknown")
            session_id = message.get("session_id") or message.get("conversation_id")
            message_id = message.get("message_id")
            log.debug(
                f"WS下行 | type={msg_type} client_id={client_id} session_id={session_id} message_id={message_id}"
            )

            # 发送消息
            await connection_info.websocket.send_text(message_str)
            connection_info.increment_message_count()
            return True
            
        except WebSocketDisconnect:
            log.info(f"客户端已断开连接: {client_id}")
            # 标记连接为不活跃，避免重复处理
            connection_info.is_active = False
            await self.disconnect(client_id)
            return False
        except Exception as e:
            log.error(f"发送消息失败: {client_id}, 错误: {e}")
            # 对于某些错误，标记连接为不活跃
            if "close message has been sent" in str(e) or "not connected" in str(e):
                connection_info.is_active = False
            return False
    
    async def broadcast_message(self, message: dict, exclude: List[str] = None) -> int:
        """
        广播消息给所有连接的客户端
        
        Args:
            message: 消息内容
            exclude: 排除的客户端ID列表
            
        Returns:
            int: 成功发送的客户端数量
        """
        if exclude is None:
            exclude = []
        
        success_count = 0
        failed_clients = []
        
        for client_id in list(self.active_connections.keys()):
            if client_id not in exclude:
                if await self.send_message(client_id, message):
                    success_count += 1
                else:
                    failed_clients.append(client_id)
        
        if failed_clients:
            log.warning(f"广播消息失败的客户端: {failed_clients}")
        
        log.info(f"广播消息完成: 成功 {success_count}/{len(self.active_connections)}")
        return success_count
    
    async def send_heartbeat(self, client_id: str) -> bool:
        """
        发送心跳消息
        
        Args:
            client_id: 客户端ID
            
        Returns:
            bool: 发送是否成功
        """
        return await self.send_message(client_id, {
            "type": "heartbeat",
            "timestamp": time.time(),
            "client_id": client_id
        })
    
    async def handle_heartbeat_response(self, client_id: str):
        """
        处理心跳响应
        
        Args:
            client_id: 客户端ID
        """
        if client_id in self.active_connections:
            self.active_connections[client_id].update_heartbeat()
            log.debug(f"收到心跳响应: {client_id}")
    
    def get_connection_info(self, client_id: str) -> Optional[ConnectionInfo]:
        """
        获取连接信息
        
        Args:
            client_id: 客户端ID
            
        Returns:
            ConnectionInfo: 连接信息对象
        """
        return self.active_connections.get(client_id)
    
    def is_connection_active(self, client_id: str) -> bool:
        """
        检查连接是否活跃
        
        Args:
            client_id: 客户端ID
            
        Returns:
            bool: 连接是否活跃
        """
        if client_id not in self.active_connections:
            return False
        
        connection_info = self.active_connections[client_id]
        return connection_info.is_active
    
    def get_connection_count(self) -> int:
        """
        获取当前连接数
        
        Returns:
            int: 连接数
        """
        return len(self.active_connections)
    
    def get_connection_stats(self) -> dict:
        """
        获取连接统计信息
        
        Returns:
            dict: 统计信息
        """
        total_connections = len(self.active_connections)
        active_connections = sum(1 for conn in self.active_connections.values() if conn.is_active)
        total_messages = sum(conn.message_count for conn in self.active_connections.values())
        
        return {
            "total_connections": total_connections,
            "active_connections": active_connections,
            "total_messages": total_messages,
            "max_connections": websocket_config.MAX_CONNECTIONS,
            "uptime": time.time() - min((conn.connected_at for conn in self.active_connections.values()), default=time.time())
        }
    
    def _start_cleanup_task(self):
        """启动清理任务"""
        if not self._cleanup_started:
            self._cleanup_started = True
            try:
                loop = asyncio.get_running_loop()
                self._cleanup_task = loop.create_task(self._cleanup_stale_connections())
            except RuntimeError:
                # 如果没有运行的事件循环，延迟启动
                log.warning("没有运行的事件循环，清理任务将在首次连接时启动")
    
    async def _cleanup_stale_connections(self):
        """清理过期连接"""
        while True:
            try:
                await asyncio.sleep(websocket_config.HEARTBEAT_INTERVAL)
                
                stale_clients = []
                for client_id, connection_info in self.active_connections.items():
                    if connection_info.is_connection_stale():
                        stale_clients.append(client_id)
                
                for client_id in stale_clients:
                    log.warning(f"清理过期连接: {client_id}")
                    await self.disconnect(client_id)
                
                if stale_clients:
                    log.info(f"清理了 {len(stale_clients)} 个过期连接")
                    
            except Exception as e:
                log.error(f"清理过期连接时出错: {e}")
    
    async def shutdown(self):
        """关闭WebSocket管理器"""
        log.info("正在关闭WebSocket管理器...")
        
        # 取消清理任务
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # 断开所有连接
        for client_id in list(self.active_connections.keys()):
            await self.disconnect(client_id)
        
        log.info("WebSocket管理器已关闭")


# 创建全局WebSocket管理器实例
websocket_manager = WebSocketManager()
