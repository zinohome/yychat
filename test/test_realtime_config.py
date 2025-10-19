"""
实时语音配置测试
"""

import pytest
import os
from unittest.mock import patch
from core.realtime_config import RealtimeConfig, realtime_config


class TestRealtimeConfig:
    """实时语音配置测试类"""
    
    def test_config_initialization(self):
        """测试配置初始化"""
        config = RealtimeConfig()
        
        # 验证基本配置
        assert config.REALTIME_API_URL == "wss://api.openai.com/v1/realtime"
        assert config.VOICE_MODEL == "gpt-4o-realtime-preview-2024-10-01"
        assert config.TOKEN_EXPIRY == 3600
        assert config.AUDIO_SAMPLE_RATE == 24000
        assert config.AUDIO_CHANNELS == 1
    
    def test_get_realtime_url(self):
        """测试获取实时API URL"""
        config = RealtimeConfig()
        url = config.get_realtime_url()
        
        expected_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        assert url == expected_url
    
    def test_get_audio_config(self):
        """测试获取音频配置"""
        config = RealtimeConfig()
        audio_config = config.get_audio_config()
        
        expected_config = {
            "sampleRate": 24000,
            "channelCount": 1,
            "echoCancellation": True,
            "noiseSuppression": True
        }
        assert audio_config == expected_config
    
    def test_get_connection_config(self):
        """测试获取连接配置"""
        config = RealtimeConfig()
        connection_config = config.get_connection_config()
        
        expected_config = {
            "timeout": 30,
            "reconnect_attempts": 3,
            "token_expiry": 3600
        }
        assert connection_config == expected_config
    
    def test_global_config_instance(self):
        """测试全局配置实例"""
        assert realtime_config is not None
        assert isinstance(realtime_config, RealtimeConfig)
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_config_validation_with_api_key(self):
        """测试配置验证（有API key）"""
        # 应该不抛出异常
        config = RealtimeConfig()
        assert config is not None
    
    @patch.dict(os.environ, {}, clear=True)
    def test_config_validation_without_api_key(self):
        """测试配置验证（无API key）"""
        # 应该不抛出异常，但会记录警告
        config = RealtimeConfig()
        assert config is not None
    
    def test_invalid_voice_model(self):
        """测试无效的语音模型"""
        with patch.object(RealtimeConfig, 'VOICE_MODEL', ''):
            with pytest.raises(ValueError, match="VOICE_MODEL 不能为空"):
                RealtimeConfig()
    
    def test_invalid_token_expiry(self):
        """测试无效的token过期时间"""
        with patch.object(RealtimeConfig, 'TOKEN_EXPIRY', 0):
            with pytest.raises(ValueError, match="TOKEN_EXPIRY 必须大于0"):
                RealtimeConfig()
    
    def test_negative_token_expiry(self):
        """测试负数的token过期时间"""
        with patch.object(RealtimeConfig, 'TOKEN_EXPIRY', -1):
            with pytest.raises(ValueError, match="TOKEN_EXPIRY 必须大于0"):
                RealtimeConfig()
