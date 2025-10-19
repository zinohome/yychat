"""
实时语音配置管理
"""

import os
from typing import Optional
from utils.log import log


class RealtimeConfig:
    """实时语音配置类"""
    
    # OpenAI Realtime API 配置
    REALTIME_API_URL = "wss://api.openai.com/v1/realtime"
    VOICE_MODEL = "gpt-4o-realtime-preview-2024-10-01"
    
    # Token 配置
    TOKEN_EXPIRY = 3600  # 1小时
    
    # 音频配置
    AUDIO_SAMPLE_RATE = 24000
    AUDIO_CHANNELS = 1
    
    # 连接配置
    CONNECTION_TIMEOUT = 30  # 30秒
    RECONNECT_ATTEMPTS = 3
    
    def __init__(self):
        """初始化配置"""
        self._validate_config()
        log.info("实时语音配置初始化完成")
    
    def _validate_config(self):
        """验证配置"""
        required_env_vars = ["OPENAI_API_KEY"]
        
        for var in required_env_vars:
            if not os.getenv(var):
                log.warning(f"环境变量 {var} 未设置")
        
        # 验证模型名称
        if not self.VOICE_MODEL:
            raise ValueError("VOICE_MODEL 不能为空")
        
        # 验证过期时间
        if self.TOKEN_EXPIRY <= 0:
            raise ValueError("TOKEN_EXPIRY 必须大于0")
    
    def get_realtime_url(self) -> str:
        """获取实时API URL"""
        return f"{self.REALTIME_API_URL}?model={self.VOICE_MODEL}"
    
    def get_audio_config(self) -> dict:
        """获取音频配置"""
        return {
            "sampleRate": self.AUDIO_SAMPLE_RATE,
            "channelCount": self.AUDIO_CHANNELS,
            "echoCancellation": True,
            "noiseSuppression": True
        }
    
    def get_connection_config(self) -> dict:
        """获取连接配置"""
        return {
            "timeout": self.CONNECTION_TIMEOUT,
            "reconnect_attempts": self.RECONNECT_ATTEMPTS,
            "token_expiry": self.TOKEN_EXPIRY
        }


# 全局配置实例
realtime_config = RealtimeConfig()
