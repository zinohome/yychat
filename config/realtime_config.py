"""
实时语音配置管理
"""

import os
from typing import Optional
from utils.log import log
from config.config import Config


class RealtimeConfig:
    """实时语音配置类"""
    
    def __init__(self):
        """初始化配置"""
        # 使用本地配置
        self.OPENAI_API_KEY = Config.OPENAI_API_KEY
        self.OPENAI_BASE_URL = Config.OPENAI_BASE_URL
        
        # Realtime API 配置 - 使用自定义base URL
        if self.OPENAI_BASE_URL and self.OPENAI_BASE_URL != "https://api.openai.com/v1":
            # 将 https:// 替换为 wss://，并添加 /realtime 路径
            base_url = self.OPENAI_BASE_URL.replace("https://", "wss://")
            self.REALTIME_API_URL = f"{base_url}/realtime"
        else:
            # 默认使用官方OpenAI Realtime API
            self.REALTIME_API_URL = "wss://api.openai.com/v1/realtime"
        self.VOICE_MODEL = Config.REALTIME_VOICE_MODEL
        
        # Token 配置
        self.TOKEN_EXPIRY = Config.REALTIME_VOICE_TOKEN_EXPIRY
        
        # 音频配置
        self.AUDIO_SAMPLE_RATE = Config.REALTIME_VOICE_SAMPLE_RATE
        self.AUDIO_CHANNELS = Config.REALTIME_VOICE_CHANNELS
        
        # 连接配置
        self.CONNECTION_TIMEOUT = 30  # 30秒
        self.RECONNECT_ATTEMPTS = 3
        
        # 新增：语音实时对话文本显示配置
        self.VOICE_CALL_SEND_TRANSCRIPTION = os.getenv('VOICE_CALL_SEND_TRANSCRIPTION', 'true').lower() == 'true'
        self.VOICE_CALL_INCLUDE_ASSISTANT_TEXT = os.getenv('VOICE_CALL_INCLUDE_ASSISTANT_TEXT', 'true').lower() == 'true'
        
        self._validate_config()
        log.info(f"实时语音配置初始化完成 - Realtime API URL: {self.REALTIME_API_URL}")
    
    def _validate_config(self):
        """验证配置"""
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未设置")
        
        if not self.VOICE_MODEL:
            raise ValueError("VOICE_MODEL 不能为空")
        
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
