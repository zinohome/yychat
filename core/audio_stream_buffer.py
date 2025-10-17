"""
Audio Stream Buffer Management for real-time voice chat.

This module provides efficient buffering and management of audio streams
for multiple clients in real-time voice conversations.
"""

import asyncio
import time
from collections import deque
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from utils.log import log


@dataclass
class AudioChunk:
    """Represents an audio chunk with metadata."""
    data: bytes
    timestamp: float
    sequence: int = 0
    client_id: str = ""


class AudioStreamBuffer:
    """
    Manages audio stream buffering for multiple clients.
    
    Provides thread-safe audio chunk management with configurable buffer sizes
    and automatic cleanup for real-time voice chat applications.
    """
    
    def __init__(self, max_size: int = 100, chunk_duration: float = 0.1):
        """
        Initialize the audio stream buffer.
        
        Args:
            max_size: Maximum number of chunks per client buffer
            chunk_duration: Expected duration of each chunk in seconds
        """
        self.max_size = max_size
        self.chunk_duration = chunk_duration
        self.buffers: Dict[str, deque] = {}
        self.locks: Dict[str, asyncio.Lock] = {}
        self.sequence_counters: Dict[str, int] = {}
        self.client_metadata: Dict[str, dict] = {}
        
        log.info(f"AudioStreamBuffer initialized: max_size={max_size}, "
                f"chunk_duration={chunk_duration}")
    
    async def add_chunk(self, client_id: str, audio_chunk: bytes, 
                       sequence: Optional[int] = None) -> bool:
        """
        Add an audio chunk to the client's buffer.
        
        Args:
            client_id: Unique client identifier
            audio_chunk: Audio data chunk
            sequence: Optional sequence number (auto-incremented if None)
            
        Returns:
            bool: True if chunk added successfully, False otherwise
        """
        try:
            # Debug logging
            log.debug(f"add_chunk called with client_id={client_id}, audio_chunk type={type(audio_chunk)}, length={len(audio_chunk) if hasattr(audio_chunk, '__len__') else 'N/A'}")
            log.debug(f"audio_chunk sample: {audio_chunk[:20] if hasattr(audio_chunk, '__getitem__') else 'N/A'}")
            
            # 检查参数类型
            if not isinstance(audio_chunk, bytes):
                log.error(f"Invalid audio_chunk type: {type(audio_chunk)}, expected bytes")
                return False
            
            if not isinstance(client_id, str):
                log.error(f"Invalid client_id type: {type(client_id)}, expected str")
                return False
            
            # Initialize client buffer if not exists
            if client_id not in self.buffers:
                self.buffers[client_id] = deque(maxlen=self.max_size)
                self.locks[client_id] = asyncio.Lock()
                self.sequence_counters[client_id] = 0
                self.client_metadata[client_id] = {
                    'first_chunk_time': time.time(),
                    'last_chunk_time': time.time(),
                    'total_chunks': 0
                }
            
            # Get or increment sequence number
            if sequence is None:
                sequence = self.sequence_counters[client_id]
                self.sequence_counters[client_id] += 1
            
            # Create audio chunk with metadata
            try:
                chunk = AudioChunk(
                    data=audio_chunk,
                    timestamp=time.time(),
                    sequence=sequence,
                    client_id=client_id
                )
                log.debug(f"Created AudioChunk: sequence={sequence}, data_length={len(audio_chunk)}")
            except Exception as chunk_error:
                log.error(f"Failed to create AudioChunk: {type(chunk_error).__name__}: {chunk_error}")
                log.error(f"Parameters: data type={type(audio_chunk)}, timestamp={time.time()}, sequence={sequence}, client_id={client_id}")
                raise
            
            # Add to buffer with lock
            async with self.locks[client_id]:
                self.buffers[client_id].append(chunk)
                
                # Update metadata
                metadata = self.client_metadata[client_id]
                metadata['last_chunk_time'] = chunk.timestamp
                metadata['total_chunks'] += 1
                
                # Log buffer status
                buffer_size = len(self.buffers[client_id])
                if buffer_size % 10 == 0:  # Log every 10 chunks
                    log.debug(f"Client {client_id}: buffer size={buffer_size}, "
                            f"sequence={sequence}")
            
            return True
            
        except Exception as e:
            log.error(f"Failed to add audio chunk for client {client_id}: {type(e).__name__}: {e}")
            log.error(f"Exception details: {repr(e)}")
            import traceback
            log.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def get_complete_audio(self, client_id: str, 
                               clear_buffer: bool = True) -> Optional[bytes]:
        """
        Get complete audio data for a client.
        
        Args:
            client_id: Client identifier
            clear_buffer: Whether to clear the buffer after getting audio
            
        Returns:
            Optional[bytes]: Complete audio data or None if no data
        """
        try:
            if client_id not in self.buffers:
                return None
            
            async with self.locks[client_id]:
                if not self.buffers[client_id]:
                    return None
                
                # Combine all audio chunks
                audio_data = b''.join(chunk.data for chunk in self.buffers[client_id])
                
                if clear_buffer:
                    self.buffers[client_id].clear()
                    self.sequence_counters[client_id] = 0
                
                log.debug(f"Retrieved complete audio for client {client_id}: "
                         f"{len(audio_data)} bytes")
                
                return audio_data
                
        except Exception as e:
            log.error(f"Failed to get complete audio for client {client_id}: {e}")
            return None
    
    async def get_audio_segment(self, client_id: str, 
                               start_time: float, end_time: float) -> Optional[bytes]:
        """
        Get audio segment within a specific time range.
        
        Args:
            client_id: Client identifier
            start_time: Start timestamp
            end_time: End timestamp
            
        Returns:
            Optional[bytes]: Audio segment data or None if no data in range
        """
        try:
            if client_id not in self.buffers:
                return None
            
            async with self.locks[client_id]:
                if not self.buffers[client_id]:
                    return None
                
                # Filter chunks by timestamp
                segment_chunks = [
                    chunk for chunk in self.buffers[client_id]
                    if start_time <= chunk.timestamp <= end_time
                ]
                
                if not segment_chunks:
                    return None
                
                # Combine segment chunks
                audio_data = b''.join(chunk.data for chunk in segment_chunks)
                
                log.debug(f"Retrieved audio segment for client {client_id}: "
                         f"{len(audio_data)} bytes, {len(segment_chunks)} chunks")
                
                return audio_data
                
        except Exception as e:
            log.error(f"Failed to get audio segment for client {client_id}: {e}")
            return None
    
    async def clear_buffer(self, client_id: str):
        """
        Clear buffer for a specific client.
        
        Args:
            client_id: Client identifier
        """
        try:
            if client_id in self.buffers:
                async with self.locks[client_id]:
                    self.buffers[client_id].clear()
                    self.sequence_counters[client_id] = 0
                
                log.debug(f"Cleared buffer for client {client_id}")
                
        except Exception as e:
            log.error(f"Failed to clear buffer for client {client_id}: {e}")
    
    async def clear_all_buffers(self):
        """Clear all client buffers."""
        try:
            for client_id in list(self.buffers.keys()):
                await self.clear_buffer(client_id)
            
            log.info("Cleared all audio buffers")
            
        except Exception as e:
            log.error(f"Failed to clear all buffers: {e}")
    
    def get_buffer_status(self, client_id: str) -> Optional[dict]:
        """
        Get buffer status for a specific client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Optional[dict]: Buffer status information or None if client not found
        """
        if client_id not in self.buffers:
            return None
        
        metadata = self.client_metadata.get(client_id, {})
        buffer_size = len(self.buffers[client_id])
        
        return {
            'client_id': client_id,
            'buffer_size': buffer_size,
            'max_size': self.max_size,
            'sequence': self.sequence_counters.get(client_id, 0),
            'first_chunk_time': metadata.get('first_chunk_time'),
            'last_chunk_time': metadata.get('last_chunk_time'),
            'total_chunks': metadata.get('total_chunks', 0),
            'buffer_utilization': buffer_size / self.max_size if self.max_size > 0 else 0
        }
    
    def get_all_buffer_status(self) -> List[dict]:
        """
        Get buffer status for all clients.
        
        Returns:
            List[dict]: List of buffer status for all clients
        """
        return [
            self.get_buffer_status(client_id) 
            for client_id in self.buffers.keys()
        ]
    
    def get_active_clients(self) -> List[str]:
        """
        Get list of clients with active buffers.
        
        Returns:
            List[str]: List of client IDs with non-empty buffers
        """
        return [
            client_id for client_id, buffer in self.buffers.items()
            if len(buffer) > 0
        ]
    
    async def cleanup_inactive_clients(self, timeout_seconds: float = 300.0):
        """
        Clean up buffers for inactive clients.
        
        Args:
            timeout_seconds: Timeout in seconds for considering a client inactive
        """
        try:
            current_time = time.time()
            inactive_clients = []
            
            for client_id, metadata in self.client_metadata.items():
                last_activity = metadata.get('last_chunk_time', 0)
                if current_time - last_activity > timeout_seconds:
                    inactive_clients.append(client_id)
            
            for client_id in inactive_clients:
                await self.clear_buffer(client_id)
                # Remove from metadata
                if client_id in self.client_metadata:
                    del self.client_metadata[client_id]
                if client_id in self.locks:
                    del self.locks[client_id]
                if client_id in self.sequence_counters:
                    del self.sequence_counters[client_id]
            
            if inactive_clients:
                log.info(f"Cleaned up {len(inactive_clients)} inactive clients: {inactive_clients}")
                
        except Exception as e:
            log.error(f"Failed to cleanup inactive clients: {e}")
    
    def get_statistics(self) -> dict:
        """
        Get buffer management statistics.
        
        Returns:
            dict: Statistics about buffer management
        """
        total_clients = len(self.buffers)
        active_clients = len(self.get_active_clients())
        total_chunks = sum(len(buffer) for buffer in self.buffers.values())
        
        return {
            'total_clients': total_clients,
            'active_clients': active_clients,
            'total_chunks': total_chunks,
            'max_size': self.max_size,
            'chunk_duration': self.chunk_duration
        }
