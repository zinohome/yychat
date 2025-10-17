"""
Connection Pool Management for real-time voice chat.

This module provides efficient connection lifecycle management
with automatic cleanup and activity tracking for WebSocket connections.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Set
from websockets import WebSocketServerProtocol
from utils.log import log


@dataclass
class ConnectionInfo:
    """Connection metadata and state information"""
    client_id: str
    websocket: WebSocketServerProtocol
    connected_at: float
    last_activity: float
    message_count: int = 0
    is_active: bool = True
    metadata: Dict = field(default_factory=dict)
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()
        self.message_count += 1
    
    def is_idle(self, timeout_seconds: float = 300.0) -> bool:
        """Check if connection is idle"""
        return time.time() - self.last_activity > timeout_seconds
    
    def get_duration(self) -> float:
        """Get connection duration in seconds"""
        return time.time() - self.connected_at


class ConnectionPool:
    """
    Manages WebSocket connections with lifecycle tracking and automatic cleanup.
    
    Provides efficient connection management with activity monitoring,
    automatic cleanup of idle connections, and connection statistics.
    """
    
    def __init__(self, max_connections: int = 100, cleanup_interval: int = 60):
        """
        Initialize the connection pool.
        
        Args:
            max_connections: Maximum number of concurrent connections
            cleanup_interval: Cleanup task interval in seconds
        """
        self.max_connections = max_connections
        self.cleanup_interval = cleanup_interval
        self.connections: Dict[str, ConnectionInfo] = {}
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Statistics
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'dropped_connections': 0,
            'cleanup_runs': 0,
            'last_cleanup': 0
        }
        
        log.info(f"ConnectionPool initialized: max_connections={max_connections}, "
                f"cleanup_interval={cleanup_interval}s")
    
    async def start(self):
        """Start the connection pool and cleanup task"""
        if self.is_running:
            log.warning("ConnectionPool already running")
            return
        
        self.is_running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        log.info("ConnectionPool started")
    
    async def stop(self):
        """Stop the connection pool and cleanup task"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        log.info("ConnectionPool stopped")
    
    async def add_connection(self, client_id: str, websocket: WebSocketServerProtocol) -> bool:
        """
        Add a new connection to the pool.
        
        Args:
            client_id: Unique client identifier
            websocket: WebSocket connection
            
        Returns:
            bool: True if connection added successfully, False if pool is full
        """
        try:
            # Check if pool is full
            if len(self.connections) >= self.max_connections:
                log.warning(f"Connection pool full, dropping connection: {client_id}")
                self.stats['dropped_connections'] += 1
                return False
            
            # Create connection info
            connection_info = ConnectionInfo(
                client_id=client_id,
                websocket=websocket,
                connected_at=time.time(),
                last_activity=time.time()
            )
            
            # Add to pool
            self.connections[client_id] = connection_info
            self.stats['total_connections'] += 1
            self.stats['active_connections'] = len(self.connections)
            
            log.info(f"Connection added to pool: {client_id}, "
                    f"total: {len(self.connections)}/{self.max_connections}")
            
            return True
            
        except Exception as e:
            log.error(f"Failed to add connection {client_id}: {e}")
            return False
    
    async def remove_connection(self, client_id: str) -> bool:
        """
        Remove a connection from the pool.
        
        Args:
            client_id: Client identifier
            
        Returns:
            bool: True if connection removed successfully
        """
        try:
            if client_id in self.connections:
                connection_info = self.connections[client_id]
                duration = connection_info.get_duration()
                
                # Close WebSocket if still open
                if not connection_info.websocket.closed:
                    await connection_info.websocket.close()
                
                # Remove from pool
                del self.connections[client_id]
                self.stats['active_connections'] = len(self.connections)
                
                log.info(f"Connection removed from pool: {client_id}, "
                        f"duration: {duration:.2f}s, total: {len(self.connections)}")
                
                return True
            else:
                log.warning(f"Connection not found in pool: {client_id}")
                return False
                
        except Exception as e:
            log.error(f"Failed to remove connection {client_id}: {e}")
            return False
    
    async def update_activity(self, client_id: str) -> bool:
        """
        Update connection activity timestamp.
        
        Args:
            client_id: Client identifier
            
        Returns:
            bool: True if activity updated successfully
        """
        try:
            if client_id in self.connections:
                self.connections[client_id].update_activity()
                return True
            else:
                log.warning(f"Connection not found for activity update: {client_id}")
                return False
                
        except Exception as e:
            log.error(f"Failed to update activity for {client_id}: {e}")
            return False
    
    def get_connection(self, client_id: str) -> Optional[ConnectionInfo]:
        """
        Get connection information.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Optional[ConnectionInfo]: Connection info or None if not found
        """
        return self.connections.get(client_id)
    
    def get_active_connections(self) -> List[str]:
        """
        Get list of active connection IDs.
        
        Returns:
            List[str]: List of active client IDs
        """
        return list(self.connections.keys())
    
    def get_connection_count(self) -> int:
        """
        Get current connection count.
        
        Returns:
            int: Number of active connections
        """
        return len(self.connections)
    
    def is_connection_active(self, client_id: str) -> bool:
        """
        Check if connection is active.
        
        Args:
            client_id: Client identifier
            
        Returns:
            bool: True if connection is active
        """
        return client_id in self.connections and self.connections[client_id].is_active
    
    async def _cleanup_loop(self):
        """Background cleanup task"""
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_idle_connections()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Cleanup loop error: {e}")
    
    async def _cleanup_idle_connections(self):
        """Clean up idle connections"""
        try:
            current_time = time.time()
            idle_timeout = 300.0  # 5 minutes
            idle_connections = []
            
            # Find idle connections
            for client_id, connection_info in self.connections.items():
                if connection_info.is_idle(idle_timeout):
                    idle_connections.append(client_id)
            
            # Remove idle connections
            for client_id in idle_connections:
                await self.remove_connection(client_id)
            
            # Update statistics
            self.stats['cleanup_runs'] += 1
            self.stats['last_cleanup'] = current_time
            
            if idle_connections:
                log.info(f"Cleaned up {len(idle_connections)} idle connections")
                
        except Exception as e:
            log.error(f"Cleanup error: {e}")
    
    async def cleanup_all_connections(self):
        """Clean up all connections"""
        try:
            client_ids = list(self.connections.keys())
            for client_id in client_ids:
                await self.remove_connection(client_id)
            
            log.info(f"Cleaned up all {len(client_ids)} connections")
            
        except Exception as e:
            log.error(f"Failed to cleanup all connections: {e}")
    
    def get_statistics(self) -> dict:
        """
        Get connection pool statistics.
        
        Returns:
            dict: Pool statistics
        """
        current_time = time.time()
        active_connections = len(self.connections)
        
        # Calculate average connection duration
        total_duration = 0
        for connection_info in self.connections.values():
            total_duration += connection_info.get_duration()
        
        avg_duration = total_duration / active_connections if active_connections > 0 else 0
        
        return {
            'max_connections': self.max_connections,
            'active_connections': active_connections,
            'total_connections': self.stats['total_connections'],
            'dropped_connections': self.stats['dropped_connections'],
            'cleanup_runs': self.stats['cleanup_runs'],
            'last_cleanup': self.stats['last_cleanup'],
            'average_duration': avg_duration,
            'pool_utilization': active_connections / self.max_connections if self.max_connections > 0 else 0,
            'is_running': self.is_running
        }
    
    def get_connection_details(self, client_id: str) -> Optional[dict]:
        """
        Get detailed connection information.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Optional[dict]: Connection details or None if not found
        """
        connection_info = self.get_connection(client_id)
        if not connection_info:
            return None
        
        return {
            'client_id': connection_info.client_id,
            'connected_at': connection_info.connected_at,
            'last_activity': connection_info.last_activity,
            'message_count': connection_info.message_count,
            'is_active': connection_info.is_active,
            'duration': connection_info.get_duration(),
            'is_idle': connection_info.is_idle(),
            'metadata': connection_info.metadata
        }
    
    def get_all_connection_details(self) -> List[dict]:
        """
        Get details for all connections.
        
        Returns:
            List[dict]: List of connection details
        """
        return [
            self.get_connection_details(client_id)
            for client_id in self.connections.keys()
        ]
