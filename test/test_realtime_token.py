"""
实时语音Token生成测试
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app import app


class TestRealtimeToken:
    """实时语音Token生成测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.client = TestClient(app)
        self.api_key = "yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4"  # 使用默认的API key
    
    def test_generate_token_success(self):
        """测试token生成成功"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-openai-key"}):
            response = self.client.post(
                "/v1/realtime/token",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "success"
            assert "data" in data
            
            token_data = data["data"]
            assert "token" in token_data
            assert "expires_at" in token_data
            assert "model" in token_data
            assert "url" in token_data
            assert "audio_config" in token_data
            assert "connection_config" in token_data
            
            # 验证token格式
            assert token_data["token"] == "test-openai-key"
            assert token_data["model"] == "gpt-4o-realtime-preview-2024-10-01"
            
            # 验证过期时间
            current_time = int(time.time())
            assert token_data["expires_at"] > current_time
            assert token_data["expires_at"] <= current_time + 3600 + 10  # 允许10秒误差
    
    def test_generate_token_missing_api_key(self):
        """测试缺少OpenAI API key"""
        with patch.dict("os.environ", {}, clear=True):
            response = self.client.post(
                "/v1/realtime/token",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "OpenAI API key未配置" in data["detail"]["error"]["message"]
    
    def test_generate_token_invalid_auth(self):
        """测试无效的API认证"""
        response = self.client.post(
            "/v1/realtime/token",
            headers={"Authorization": "Bearer invalid-key"}
        )
        
        assert response.status_code == 401
    
    def test_generate_token_missing_auth(self):
        """测试缺少认证头"""
        response = self.client.post("/v1/realtime/token")
        
        assert response.status_code == 403  # FastAPI返回403而不是401
    
    def test_token_expiry_time(self):
        """测试token过期时间正确性"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-openai-key"}):
            response = self.client.post(
                "/v1/realtime/token",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            token_data = data["data"]
            
            # 验证过期时间在合理范围内
            current_time = int(time.time())
            expected_expiry = current_time + 3600  # 1小时后
            
            # 允许5秒的误差
            assert abs(token_data["expires_at"] - expected_expiry) <= 5
    
    def test_audio_config_format(self):
        """测试音频配置格式"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-openai-key"}):
            response = self.client.post(
                "/v1/realtime/token",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            audio_config = data["data"]["audio_config"]
            
            expected_config = {
                "sampleRate": 24000,
                "channelCount": 1,
                "echoCancellation": True,
                "noiseSuppression": True
            }
            assert audio_config == expected_config
    
    def test_connection_config_format(self):
        """测试连接配置格式"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-openai-key"}):
            response = self.client.post(
                "/v1/realtime/token",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            connection_config = data["data"]["connection_config"]
            
            expected_config = {
                "timeout": 30,
                "reconnect_attempts": 3,
                "token_expiry": 3600
            }
            assert connection_config == expected_config
    
    def test_realtime_url_format(self):
        """测试实时API URL格式"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-openai-key"}):
            response = self.client.post(
                "/v1/realtime/token",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            url = data["data"]["url"]
            
            expected_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
            assert url == expected_url
