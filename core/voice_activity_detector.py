"""
Voice Activity Detection (VAD) system for real-time voice chat.

This module provides intelligent speech detection capabilities to automatically
identify when users start and stop speaking during real-time voice conversations.
"""

import webrtcvad
import time
from typing import List, Optional, Tuple
from utils.log import log


class VoiceActivityDetector:
    """
    Voice Activity Detector using WebRTC VAD algorithm.
    
    Provides frame-level speech detection with configurable aggressiveness
    and silence detection thresholds for real-time voice chat applications.
    """
    
    def __init__(self, aggressiveness: int = 2, silence_threshold: int = 10):
        """
        Initialize the Voice Activity Detector.
        
        Args:
            aggressiveness: VAD aggressiveness level (0-3, higher = more aggressive)
            silence_threshold: Number of consecutive silent frames to consider speech ended
        """
        self.vad = webrtcvad.Vad(aggressiveness)
        self.silence_threshold = silence_threshold
        self.sample_rate = 16000  # 16kHz sample rate
        self.frame_duration = 30  # 30ms frames
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)
        
        # State tracking
        self.speech_segments = {}  # client_id -> speech state
        self.frame_buffers = {}    # client_id -> frame buffer
        
        log.info(f"VoiceActivityDetector initialized: aggressiveness={aggressiveness}, "
                f"silence_threshold={silence_threshold}, frame_size={self.frame_size}")
    
    def detect_speech(self, audio_data: bytes) -> bool:
        """
        Detect if audio data contains speech.
        
        Args:
            audio_data: Raw audio data (16-bit PCM, 16kHz, mono)
            
        Returns:
            bool: True if speech detected, False otherwise
        """
        if len(audio_data) < self.frame_size * 2:
            return False
        
        try:
            return self.vad.is_speech(audio_data, self.sample_rate)
        except Exception as e:
            log.error(f"VAD detection failed: {e}")
            return False
    
    def process_audio_stream(self, client_id: str, audio_chunk: bytes) -> Optional[bool]:
        """
        Process audio stream and detect speech activity.
        
        Args:
            client_id: Unique client identifier
            audio_chunk: Audio data chunk
            
        Returns:
            Optional[bool]: True if speech started, False if speech ended, None if no change
        """
        # Initialize client state if not exists
        if client_id not in self.speech_segments:
            self.speech_segments[client_id] = {
                'is_speaking': False,
                'speech_start': None,
                'silence_count': 0,
                'last_activity': time.time()
            }
            self.frame_buffers[client_id] = []
        
        segment = self.speech_segments[client_id]
        buffer = self.frame_buffers[client_id]
        
        # Add chunk to buffer
        buffer.append(audio_chunk)
        
        # Process complete frames (30ms each)
        frame_size_bytes = self.frame_size * 2  # 16-bit samples
        speech_detected = False
        
        while len(buffer) >= frame_size_bytes:
            frame_data = buffer[:frame_size_bytes]
            buffer = buffer[frame_size_bytes:]
            
            # Detect speech in this frame
            if self.detect_speech(frame_data):
                speech_detected = True
                segment['silence_count'] = 0
                segment['last_activity'] = time.time()
            else:
                segment['silence_count'] += 1
        
        # Update buffer
        self.frame_buffers[client_id] = buffer
        
        # Determine speech state changes
        if speech_detected and not segment['is_speaking']:
            # Speech started
            segment['is_speaking'] = True
            segment['speech_start'] = time.time()
            log.debug(f"Speech started for client {client_id}")
            return True
            
        elif not speech_detected and segment['is_speaking']:
            # Check if silence threshold reached
            if segment['silence_count'] >= self.silence_threshold:
                # Speech ended
                segment['is_speaking'] = False
                speech_duration = time.time() - segment['speech_start'] if segment['speech_start'] else 0
                log.debug(f"Speech ended for client {client_id}, duration: {speech_duration:.2f}s")
                return False
        
        return None  # No state change
    
    def get_speech_state(self, client_id: str) -> dict:
        """
        Get current speech state for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            dict: Current speech state information
        """
        if client_id not in self.speech_segments:
            return {
                'is_speaking': False,
                'speech_start': None,
                'silence_count': 0,
                'last_activity': None
            }
        
        return self.speech_segments[client_id].copy()
    
    def clear_client_state(self, client_id: str):
        """
        Clear speech state for a specific client.
        
        Args:
            client_id: Client identifier
        """
        if client_id in self.speech_segments:
            del self.speech_segments[client_id]
        if client_id in self.frame_buffers:
            del self.frame_buffers[client_id]
        
        log.debug(f"Cleared speech state for client {client_id}")
    
    def clear_all_states(self):
        """Clear all client speech states."""
        self.speech_segments.clear()
        self.frame_buffers.clear()
        log.info("Cleared all speech states")
    
    def get_active_speakers(self) -> List[str]:
        """
        Get list of clients currently speaking.
        
        Returns:
            List[str]: List of client IDs currently speaking
        """
        return [
            client_id for client_id, segment in self.speech_segments.items()
            if segment['is_speaking']
        ]
    
    def get_speech_statistics(self) -> dict:
        """
        Get speech detection statistics.
        
        Returns:
            dict: Statistics about speech detection
        """
        total_clients = len(self.speech_segments)
        active_speakers = len(self.get_active_speakers())
        
        return {
            'total_clients': total_clients,
            'active_speakers': active_speakers,
            'silence_threshold': self.silence_threshold,
            'frame_size': self.frame_size,
            'sample_rate': self.sample_rate
        }
