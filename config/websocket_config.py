"""
WebSocket配置模块
用于语音助手的WebSocket连接管理
"""

from typing import Dict, Any
from config.config import get_config

config = get_config()

class WebSocketConfig:
    """WebSocket相关配置参数"""
    
    # 连接管理配置
    MAX_CONNECTIONS = 100
    HEARTBEAT_INTERVAL = 30  # 心跳间隔（秒）
    CONNECTION_TIMEOUT = 300  # 连接超时（秒）
    MESSAGE_SIZE_LIMIT = 1024 * 1024  # 消息大小限制（1MB）
    
    # 重连配置
    MAX_RECONNECT_ATTEMPTS = 5
    RECONNECT_INTERVAL = 1000  # 重连间隔（毫秒）
    
    # 音频配置
    AUDIO_CHUNK_SIZE = 1024
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHANNELS = 1
    
    # 语音活动检测配置
    VAD_AGGRESSIVENESS = 2
    VAD_FRAME_DURATION = 30  # 毫秒
    
    # 性能配置
    ENABLE_PERFORMANCE_MONITOR = True
    PERFORMANCE_LOG_ENABLED = True
    
    # 缓存配置
    AUDIO_CACHE_SIZE = 100
    TTS_CACHE_SIZE = 50
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """获取配置字典"""
        return {
            "max_connections": cls.MAX_CONNECTIONS,
            "heartbeat_interval": cls.HEARTBEAT_INTERVAL,
            "connection_timeout": cls.CONNECTION_TIMEOUT,
            "message_size_limit": cls.MESSAGE_SIZE_LIMIT,
            "max_reconnect_attempts": cls.MAX_RECONNECT_ATTEMPTS,
            "reconnect_interval": cls.RECONNECT_INTERVAL,
            "audio_chunk_size": cls.AUDIO_CHUNK_SIZE,
            "audio_sample_rate": cls.AUDIO_SAMPLE_RATE,
            "audio_channels": cls.AUDIO_CHANNELS,
            "vad_aggressiveness": cls.VAD_AGGRESSIVENESS,
            "vad_frame_duration": cls.VAD_FRAME_DURATION,
            "enable_performance_monitor": cls.ENABLE_PERFORMANCE_MONITOR,
            "performance_log_enabled": cls.PERFORMANCE_LOG_ENABLED,
            "audio_cache_size": cls.AUDIO_CACHE_SIZE,
            "tts_cache_size": cls.TTS_CACHE_SIZE
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置参数"""
        try:
            # 验证数值范围
            assert cls.MAX_CONNECTIONS > 0, "MAX_CONNECTIONS must be positive"
            assert cls.HEARTBEAT_INTERVAL > 0, "HEARTBEAT_INTERVAL must be positive"
            assert cls.CONNECTION_TIMEOUT > 0, "CONNECTION_TIMEOUT must be positive"
            assert cls.MESSAGE_SIZE_LIMIT > 0, "MESSAGE_SIZE_LIMIT must be positive"
            assert cls.AUDIO_SAMPLE_RATE > 0, "AUDIO_SAMPLE_RATE must be positive"
            assert cls.AUDIO_CHANNELS > 0, "AUDIO_CHANNELS must be positive"
            assert 0 <= cls.VAD_AGGRESSIVENESS <= 3, "VAD_AGGRESSIVENESS must be between 0 and 3"
            
            return True
        except AssertionError as e:
            print(f"WebSocket配置验证失败: {e}")
            return False

# 创建全局配置实例
websocket_config = WebSocketConfig()

# 验证配置
if not websocket_config.validate_config():
    raise ValueError("WebSocket配置验证失败")
