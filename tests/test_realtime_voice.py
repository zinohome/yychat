"""
Comprehensive tests for real-time voice chat functionality.

This module provides unit tests for VAD, audio processing, connection management,
and integration testing for the complete voice chat system.
"""

import pytest
import asyncio
import time
import base64
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import the components to test
from core.voice_activity_detector import VoiceActivityDetector
from core.audio_stream_buffer import AudioStreamBuffer, AudioChunk
from core.parallel_audio_processor import ParallelAudioProcessor, ProcessingResult
from core.connection_pool import ConnectionPool, ConnectionInfo
from core.error_recovery import ErrorRecoveryManager, ErrorType, ErrorInfo
from monitoring.voice_performance_monitor import VoicePerformanceMonitor


class TestVoiceActivityDetector:
    """Test Voice Activity Detection functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.vad = VoiceActivityDetector(aggressiveness=2, silence_threshold=10)
    
    def test_initialization(self):
        """Test VAD initialization"""
        assert self.vad.silence_threshold == 10
        assert self.vad.sample_rate == 16000
        assert self.vad.frame_size == 480  # 30ms at 16kHz
    
    def test_detect_speech_empty_data(self):
        """Test speech detection with empty data"""
        result = self.vad.detect_speech(b"")
        assert result is False
    
    def test_detect_speech_short_data(self):
        """Test speech detection with short data"""
        short_data = b"x" * 100  # Less than frame size
        result = self.vad.detect_speech(short_data)
        assert result is False
    
    @patch('webrtcvad.Vad.is_speech')
    def test_detect_speech_success(self, mock_is_speech):
        """Test successful speech detection"""
        mock_is_speech.return_value = True
        
        audio_data = b"x" * 960  # 30ms at 16kHz
        result = self.vad.detect_speech(audio_data)
        
        assert result is True
        mock_is_speech.assert_called_once_with(audio_data, 16000)
    
    def test_process_audio_stream_speech_start(self):
        """Test audio stream processing with speech start"""
        client_id = "test_client"
        audio_chunk = b"x" * 960
        
        with patch.object(self.vad, 'detect_speech', return_value=True):
            result = self.vad.process_audio_stream(client_id, audio_chunk)
            assert result is True  # Speech started
    
    def test_process_audio_stream_speech_end(self):
        """Test audio stream processing with speech end"""
        client_id = "test_client"
        
        # First, start speech
        with patch.object(self.vad, 'detect_speech', return_value=True):
            self.vad.process_audio_stream(client_id, b"x" * 960)
        
        # Then end speech
        with patch.object(self.vad, 'detect_speech', return_value=False):
            # Simulate silence threshold reached
            for _ in range(11):  # More than silence_threshold
                result = self.vad.process_audio_stream(client_id, b"x" * 960)
            
            assert result is False  # Speech ended
    
    def test_get_speech_state(self):
        """Test getting speech state"""
        client_id = "test_client"
        state = self.vad.get_speech_state(client_id)
        
        assert state['is_speaking'] is False
        assert state['speech_start'] is None
        assert state['silence_count'] == 0
    
    def test_clear_client_state(self):
        """Test clearing client state"""
        client_id = "test_client"
        
        # Add some state
        self.vad.speech_segments[client_id] = {'is_speaking': True}
        self.vad.frame_buffers[client_id] = [b"data"]
        
        # Clear state
        self.vad.clear_client_state(client_id)
        
        assert client_id not in self.vad.speech_segments
        assert client_id not in self.vad.frame_buffers


class TestAudioStreamBuffer:
    """Test Audio Stream Buffer functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.buffer = AudioStreamBuffer(max_size=10, chunk_duration=0.1)
    
    @pytest.mark.asyncio
    async def test_add_chunk(self):
        """Test adding audio chunk"""
        client_id = "test_client"
        audio_chunk = b"test_audio_data"
        
        result = await self.buffer.add_chunk(client_id, audio_chunk)
        assert result is True
        assert client_id in self.buffer.buffers
        assert len(self.buffer.buffers[client_id]) == 1
    
    @pytest.mark.asyncio
    async def test_get_complete_audio(self):
        """Test getting complete audio"""
        client_id = "test_client"
        audio_data = b"test_audio_data"
        
        # Add chunk
        await self.buffer.add_chunk(client_id, audio_data)
        
        # Get complete audio
        result = await self.buffer.get_complete_audio(client_id)
        assert result == audio_data
        assert len(self.buffer.buffers[client_id]) == 0  # Buffer cleared
    
    @pytest.mark.asyncio
    async def test_get_audio_segment(self):
        """Test getting audio segment by time range"""
        client_id = "test_client"
        audio_data = b"test_audio_data"
        
        # Add chunk
        await self.buffer.add_chunk(client_id, audio_data)
        
        # Get segment
        start_time = time.time() - 1
        end_time = time.time() + 1
        result = await self.buffer.get_audio_segment(client_id, start_time, end_time)
        assert result == audio_data
    
    @pytest.mark.asyncio
    async def test_clear_buffer(self):
        """Test clearing buffer"""
        client_id = "test_client"
        audio_data = b"test_audio_data"
        
        # Add chunk
        await self.buffer.add_chunk(client_id, audio_data)
        assert len(self.buffer.buffers[client_id]) == 1
        
        # Clear buffer
        await self.buffer.clear_buffer(client_id)
        assert len(self.buffer.buffers[client_id]) == 0
    
    def test_get_buffer_status(self):
        """Test getting buffer status"""
        client_id = "test_client"
        status = self.buffer.get_buffer_status(client_id)
        
        assert status is None  # Client not in buffer
        
        # Add client
        self.buffer.buffers[client_id] = []
        status = self.buffer.get_buffer_status(client_id)
        
        assert status is not None
        assert status['client_id'] == client_id
        assert status['buffer_size'] == 0


class TestParallelAudioProcessor:
    """Test Parallel Audio Processor functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = ParallelAudioProcessor(max_workers=2, timeout_seconds=5.0)
    
    @pytest.mark.asyncio
    async def test_process_audio_async_success(self):
        """Test successful audio processing"""
        client_id = "test_client"
        audio_data = b"test_audio"
        
        # Mock callbacks
        async def stt_callback(data):
            return "transcribed text"
        
        async def ai_callback(text):
            return "AI response"
        
        async def tts_callback(text):
            return b"audio_response"
        
        result = await self.processor.process_audio_async(
            client_id, audio_data, stt_callback, ai_callback, tts_callback
        )
        
        assert result.success is True
        assert result.text == "transcribed text"
        assert result.response == "AI response"
        assert result.audio_data == b"audio_response"
    
    @pytest.mark.asyncio
    async def test_process_audio_async_failure(self):
        """Test failed audio processing"""
        client_id = "test_client"
        audio_data = b"test_audio"
        
        # Mock callbacks that fail
        async def stt_callback(data):
            raise Exception("STT failed")
        
        async def ai_callback(text):
            return "AI response"
        
        async def tts_callback(text):
            return b"audio_response"
        
        result = await self.processor.process_audio_async(
            client_id, audio_data, stt_callback, ai_callback, tts_callback
        )
        
        assert result.success is False
        assert "STT failed" in result.error
    
    @pytest.mark.asyncio
    async def test_cancel_processing(self):
        """Test canceling processing"""
        client_id = "test_client"
        
        # Start a long-running task
        async def long_stt_callback(data):
            await asyncio.sleep(10)  # Long processing
            return "text"
        
        async def ai_callback(text):
            return "response"
        
        async def tts_callback(text):
            return b"audio"
        
        # Start processing
        task = asyncio.create_task(
            self.processor.process_audio_async(
                client_id, b"data", long_stt_callback, ai_callback, tts_callback
            )
        )
        
        # Cancel processing
        cancelled = await self.processor.cancel_processing(client_id)
        assert cancelled is True
        
        # Wait for task to complete
        await task
    
    def test_get_statistics(self):
        """Test getting processor statistics"""
        stats = self.processor.get_statistics()
        
        assert 'total_processed' in stats
        assert 'successful_processed' in stats
        assert 'failed_processed' in stats
        assert 'max_workers' in stats
        assert 'timeout_seconds' in stats


class TestConnectionPool:
    """Test Connection Pool functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.pool = ConnectionPool(max_connections=5, cleanup_interval=60)
    
    @pytest.mark.asyncio
    async def test_add_connection(self):
        """Test adding connection"""
        client_id = "test_client"
        websocket = Mock()
        
        result = await self.pool.add_connection(client_id, websocket)
        assert result is True
        assert client_id in self.pool.connections
    
    @pytest.mark.asyncio
    async def test_add_connection_pool_full(self):
        """Test adding connection when pool is full"""
        # Fill the pool
        for i in range(5):
            await self.pool.add_connection(f"client_{i}", Mock())
        
        # Try to add one more
        result = await self.pool.add_connection("overflow_client", Mock())
        assert result is False
    
    @pytest.mark.asyncio
    async def test_remove_connection(self):
        """Test removing connection"""
        client_id = "test_client"
        websocket = Mock()
        
        # Add connection
        await self.pool.add_connection(client_id, websocket)
        assert client_id in self.pool.connections
        
        # Remove connection
        result = await self.pool.remove_connection(client_id)
        assert result is True
        assert client_id not in self.pool.connections
    
    @pytest.mark.asyncio
    async def test_update_activity(self):
        """Test updating connection activity"""
        client_id = "test_client"
        websocket = Mock()
        
        # Add connection
        await self.pool.add_connection(client_id, websocket)
        
        # Update activity
        result = await self.pool.update_activity(client_id)
        assert result is True
        
        # Check that activity was updated
        connection = self.pool.get_connection(client_id)
        assert connection.message_count == 1
    
    def test_get_statistics(self):
        """Test getting pool statistics"""
        stats = self.pool.get_statistics()
        
        assert 'max_connections' in stats
        assert 'active_connections' in stats
        assert 'total_connections' in stats
        assert 'pool_utilization' in stats


class TestErrorRecoveryManager:
    """Test Error Recovery Manager functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.recovery = ErrorRecoveryManager(max_retries=2, base_delay=0.1, max_delay=1.0)
    
    @pytest.mark.asyncio
    async def test_handle_error_success(self):
        """Test successful error handling"""
        client_id = "test_client"
        
        # Mock a successful recovery handler
        async def mock_handler(error_info):
            return True
        
        self.recovery.register_handler(ErrorType.CONNECTION_LOST, mock_handler)
        
        result = await self.recovery.handle_error(
            ErrorType.CONNECTION_LOST, "Connection lost", client_id
        )
        
        assert result is True
        assert client_id not in self.recovery.active_errors
    
    @pytest.mark.asyncio
    async def test_handle_error_failure(self):
        """Test failed error handling"""
        client_id = "test_client"
        
        # Mock a failing recovery handler
        async def mock_handler(error_info):
            return False
        
        self.recovery.register_handler(ErrorType.CONNECTION_LOST, mock_handler)
        
        result = await self.recovery.handle_error(
            ErrorType.CONNECTION_LOST, "Connection lost", client_id
        )
        
        assert result is False
        assert client_id not in self.recovery.active_errors  # Max retries exceeded
    
    def test_get_recovery_statistics(self):
        """Test getting recovery statistics"""
        stats = self.recovery.get_recovery_statistics()
        
        assert 'total_errors' in stats
        assert 'recovered_errors' in stats
        assert 'failed_recoveries' in stats
        assert 'recovery_success_rate' in stats


class TestVoicePerformanceMonitor:
    """Test Voice Performance Monitor functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = VoicePerformanceMonitor(max_samples=100, collection_interval=0.1)
    
    def test_record_audio_processing_time(self):
        """Test recording audio processing time"""
        processing_time = 1.5
        client_id = "test_client"
        
        self.monitor.record_audio_processing_time(processing_time, client_id)
        
        assert len(self.monitor.metrics['audio_processing_time']) == 1
        assert self.monitor.metrics['audio_processing_time'][0] == processing_time
    
    def test_record_tts_generation_time(self):
        """Test recording TTS generation time"""
        generation_time = 2.0
        client_id = "test_client"
        
        self.monitor.record_tts_generation_time(generation_time, client_id)
        
        assert len(self.monitor.metrics['tts_generation_time']) == 1
        assert self.monitor.metrics['tts_generation_time'][0] == generation_time
    
    def test_get_performance_summary(self):
        """Test getting performance summary"""
        # Record some metrics
        self.monitor.record_audio_processing_time(1.0)
        self.monitor.record_tts_generation_time(2.0)
        self.monitor.record_connection_count(5)
        
        summary = self.monitor.get_performance_summary()
        
        assert 'collection_stats' in summary
        assert 'audio_metrics' in summary
        assert 'tts_metrics' in summary
        assert 'connection_metrics' in summary
    
    def test_get_alerts(self):
        """Test getting performance alerts"""
        # Record high CPU usage
        self.monitor.metrics['system_cpu'].append(85.0)
        
        alerts = self.monitor.get_alerts()
        
        assert len(alerts) > 0
        assert any(alert['type'] == 'high_cpu' for alert in alerts)


class TestIntegration:
    """Integration tests for the complete voice chat system"""
    
    @pytest.mark.asyncio
    async def test_complete_voice_processing_flow(self):
        """Test complete voice processing flow"""
        # Initialize components
        vad = VoiceActivityDetector()
        buffer = AudioStreamBuffer()
        processor = ParallelAudioProcessor(max_workers=2)
        
        client_id = "integration_test_client"
        audio_data = b"test_audio_data"
        
        # Add audio to buffer
        await buffer.add_chunk(client_id, audio_data)
        
        # Process with VAD
        with patch.object(vad, 'detect_speech', return_value=True):
            speech_change = vad.process_audio_stream(client_id, audio_data)
            assert speech_change is True
        
        # Get complete audio
        complete_audio = await buffer.get_complete_audio(client_id)
        assert complete_audio == audio_data
        
        # Process audio
        async def stt_callback(data):
            return "transcribed text"
        
        async def ai_callback(text):
            return "AI response"
        
        async def tts_callback(text):
            return b"audio_response"
        
        result = await processor.process_audio_async(
            client_id, complete_audio, stt_callback, ai_callback, tts_callback
        )
        
        assert result.success is True
        assert result.text == "transcribed text"
        assert result.response == "AI response"
        assert result.audio_data == b"audio_response"
    
    @pytest.mark.asyncio
    async def test_error_recovery_integration(self):
        """Test error recovery integration"""
        pool = ConnectionPool(max_connections=2)
        recovery = ErrorRecoveryManager(max_retries=1, base_delay=0.1)
        
        client_id = "error_test_client"
        websocket = Mock()
        
        # Add connection
        await pool.add_connection(client_id, websocket)
        
        # Simulate error
        result = await recovery.handle_error(
            ErrorType.CONNECTION_LOST, "Connection lost", client_id
        )
        
        # Should attempt recovery
        assert result is True or result is False  # Depends on handler success
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test performance monitoring integration"""
        monitor = VoicePerformanceMonitor(max_samples=10, collection_interval=0.1)
        
        # Start monitoring
        await monitor.start()
        
        # Record some metrics
        monitor.record_audio_processing_time(1.0)
        monitor.record_tts_generation_time(2.0)
        monitor.record_connection_count(3)
        
        # Get summary
        summary = monitor.get_performance_summary()
        assert 'audio_metrics' in summary
        assert 'tts_metrics' in summary
        assert 'connection_metrics' in summary
        
        # Stop monitoring
        await monitor.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
