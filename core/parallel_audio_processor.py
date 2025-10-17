"""
Parallel Audio Processing for real-time voice chat.

This module provides efficient parallel processing of audio streams
using thread pools to avoid blocking the main event loop.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Optional, Callable, Any, List
from dataclasses import dataclass
from utils.log import log


@dataclass
class ProcessingResult:
    """Result of audio processing operation."""
    success: bool
    text: Optional[str] = None
    response: Optional[str] = None
    audio_data: Optional[bytes] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    client_id: str = ""


class ParallelAudioProcessor:
    """
    Manages parallel audio processing using thread pools.
    
    Provides non-blocking audio processing with task cancellation support
    for real-time voice chat applications.
    """
    
    def __init__(self, max_workers: int = 4, timeout_seconds: float = 30.0):
        """
        Initialize the parallel audio processor.
        
        Args:
            max_workers: Maximum number of worker threads
            timeout_seconds: Timeout for processing tasks
        """
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processing_tasks: Dict[str, Future] = {}
        self.processing_stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'cancelled_processed': 0,
            'total_processing_time': 0.0
        }
        
        log.info(f"ParallelAudioProcessor initialized: max_workers={max_workers}, "
                f"timeout={timeout_seconds}s")
    
    async def process_audio_async(self, client_id: str, audio_data: bytes,
                                 stt_callback: Callable[[bytes], str],
                                 ai_callback: Callable[[str], str],
                                 tts_callback: Callable[[str], bytes]) -> ProcessingResult:
        """
        Process audio data asynchronously using thread pool.
        
        Args:
            client_id: Unique client identifier
            audio_data: Audio data to process
            stt_callback: Speech-to-text callback function
            ai_callback: AI processing callback function
            tts_callback: Text-to-speech callback function
            
        Returns:
            ProcessingResult: Result of the processing operation
        """
        start_time = time.time()
        
        try:
            # Cancel existing task for this client if any
            if client_id in self.processing_tasks:
                self.processing_tasks[client_id].cancel()
                self.processing_stats['cancelled_processed'] += 1
                log.debug(f"Cancelled existing processing task for client {client_id}")
            
            # Create new processing task
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(
                self.executor,
                self._process_audio_sync,
                client_id,
                audio_data,
                stt_callback,
                ai_callback,
                tts_callback
            )
            
            self.processing_tasks[client_id] = future
            
            # Wait for completion with timeout
            try:
                result = await asyncio.wait_for(future, timeout=self.timeout_seconds)
                processing_time = time.time() - start_time
                result.processing_time = processing_time
                
                # Update statistics
                self.processing_stats['total_processed'] += 1
                if result.success:
                    self.processing_stats['successful_processed'] += 1
                else:
                    self.processing_stats['failed_processed'] += 1
                
                self.processing_stats['total_processing_time'] += processing_time
                
                log.debug(f"Audio processing completed for client {client_id}: "
                         f"success={result.success}, time={processing_time:.2f}s")
                
                return result
                
            except asyncio.TimeoutError:
                log.warning(f"Audio processing timeout for client {client_id}")
                return ProcessingResult(
                    success=False,
                    error="Processing timeout",
                    processing_time=time.time() - start_time,
                    client_id=client_id
                )
                
        except Exception as e:
            log.error(f"Audio processing failed for client {client_id}: {e}")
            return ProcessingResult(
                success=False,
                error=str(e),
                processing_time=time.time() - start_time,
                client_id=client_id
            )
        finally:
            # Clean up task reference
            if client_id in self.processing_tasks:
                del self.processing_tasks[client_id]
    
    def _process_audio_sync(self, client_id: str, audio_data: bytes,
                           stt_callback: Callable[[bytes], str],
                           ai_callback: Callable[[str], str],
                           tts_callback: Callable[[str], bytes]) -> ProcessingResult:
        """
        Synchronous audio processing (runs in thread pool).
        
        Args:
            client_id: Client identifier
            audio_data: Audio data to process
            stt_callback: Speech-to-text callback
            ai_callback: AI processing callback
            tts_callback: Text-to-speech callback
            
        Returns:
            ProcessingResult: Processing result
        """
        try:
            # Step 1: Speech-to-Text
            log.debug(f"Starting STT for client {client_id}")
            text = stt_callback(audio_data)
            if not text or not text.strip():
                return ProcessingResult(
                    success=False,
                    error="No text detected in audio",
                    client_id=client_id
                )
            
            log.debug(f"STT completed for client {client_id}: '{text[:50]}...'")
            
            # Step 2: AI Processing
            log.debug(f"Starting AI processing for client {client_id}")
            response = ai_callback(text)
            if not response or not response.strip():
                return ProcessingResult(
                    success=False,
                    error="No AI response generated",
                    client_id=client_id
                )
            
            log.debug(f"AI processing completed for client {client_id}: '{response[:50]}...'")
            
            # Step 3: Text-to-Speech
            log.debug(f"Starting TTS for client {client_id}")
            audio_response = tts_callback(response)
            if not audio_response:
                return ProcessingResult(
                    success=False,
                    error="No audio response generated",
                    client_id=client_id
                )
            
            log.debug(f"TTS completed for client {client_id}: {len(audio_response)} bytes")
            
            return ProcessingResult(
                success=True,
                text=text,
                response=response,
                audio_data=audio_response,
                client_id=client_id
            )
            
        except Exception as e:
            log.error(f"Sync audio processing failed for client {client_id}: {e}")
            return ProcessingResult(
                success=False,
                error=str(e),
                client_id=client_id
            )
    
    async def cancel_processing(self, client_id: str) -> bool:
        """
        Cancel processing for a specific client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            bool: True if task was cancelled, False if not found
        """
        if client_id in self.processing_tasks:
            future = self.processing_tasks[client_id]
            cancelled = future.cancel()
            if cancelled:
                del self.processing_tasks[client_id]
                self.processing_stats['cancelled_processed'] += 1
                log.debug(f"Cancelled processing for client {client_id}")
            return cancelled
        
        return False
    
    async def cancel_all_processing(self):
        """Cancel all active processing tasks."""
        cancelled_count = 0
        for client_id in list(self.processing_tasks.keys()):
            if await self.cancel_processing(client_id):
                cancelled_count += 1
        
        log.info(f"Cancelled {cancelled_count} processing tasks")
    
    def get_processing_status(self, client_id: str) -> Optional[dict]:
        """
        Get processing status for a specific client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Optional[dict]: Processing status or None if not found
        """
        if client_id not in self.processing_tasks:
            return None
        
        future = self.processing_tasks[client_id]
        return {
            'client_id': client_id,
            'running': not future.done(),
            'cancelled': future.cancelled(),
            'done': future.done(),
            'exception': future.exception() is not None
        }
    
    def get_all_processing_status(self) -> List[dict]:
        """
        Get processing status for all clients.
        
        Returns:
            List[dict]: List of processing status for all clients
        """
        return [
            self.get_processing_status(client_id)
            for client_id in self.processing_tasks.keys()
        ]
    
    def get_active_clients(self) -> List[str]:
        """
        Get list of clients with active processing.
        
        Returns:
            List[str]: List of client IDs with active processing
        """
        return [
            client_id for client_id, future in self.processing_tasks.items()
            if not future.done()
        ]
    
    def get_statistics(self) -> dict:
        """
        Get processing statistics.
        
        Returns:
            dict: Processing statistics
        """
        total = self.processing_stats['total_processed']
        successful = self.processing_stats['successful_processed']
        failed = self.processing_stats['failed_processed']
        cancelled = self.processing_stats['cancelled_processed']
        total_time = self.processing_stats['total_processing_time']
        
        return {
            'total_processed': total,
            'successful_processed': successful,
            'failed_processed': failed,
            'cancelled_processed': cancelled,
            'success_rate': successful / total if total > 0 else 0,
            'average_processing_time': total_time / total if total > 0 else 0,
            'active_tasks': len(self.processing_tasks),
            'max_workers': self.max_workers,
            'timeout_seconds': self.timeout_seconds
        }
    
    async def shutdown(self):
        """Shutdown the processor and cleanup resources."""
        try:
            # Cancel all active tasks
            await self.cancel_all_processing()
            
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            log.info("ParallelAudioProcessor shutdown completed")
            
        except Exception as e:
            log.error(f"Error during processor shutdown: {e}")
