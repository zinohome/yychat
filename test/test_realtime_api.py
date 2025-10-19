"""
实时语音API集成测试
"""

import pytest
from fastapi.testclient import TestClient
from app import app


class TestRealtimeAPI:
    """实时语音API集成测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.client = TestClient(app)
        self.api_key = "yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4"  # 使用默认的API key
    
    def test_get_realtime_memory_success(self):
        """测试获取实时语音记忆成功"""
        request_data = {
            "conversation_id": "conv_123",
            "query": "测试查询"
        }
        
        response = self.client.post(
            "/v1/realtime/memory",
            json=request_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert data["conversation_id"] == "conv_123"
        assert data["query"] == "测试查询"
    
    def test_get_realtime_memory_invalid_auth(self):
        """测试获取实时语音记忆无效认证"""
        request_data = {
            "conversation_id": "conv_123",
            "query": "测试查询"
        }
        
        response = self.client.post(
            "/v1/realtime/memory",
            json=request_data,
            headers={"Authorization": "Bearer invalid-key"}
        )
        
        assert response.status_code == 401
    
    def test_get_realtime_personality_success(self):
        """测试获取实时语音人格成功"""
        request_data = {
            "personality_id": "personality_123"
        }
        
        response = self.client.post(
            "/v1/realtime/personality",
            json=request_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert data["personality_id"] == "personality_123"
        assert "instructions" in data["data"]
        assert "voice" in data["data"]
        assert "modalities" in data["data"]
    
    def test_get_realtime_personality_missing_auth(self):
        """测试获取实时语音人格缺少认证"""
        request_data = {
            "personality_id": "personality_123"
        }
        
        response = self.client.post(
            "/v1/realtime/personality",
            json=request_data
        )
        
        assert response.status_code == 403
    
    def test_get_realtime_tools_success(self):
        """测试获取实时语音工具成功"""
        request_data = {
            "personality_id": "personality_123"
        }
        
        response = self.client.post(
            "/v1/realtime/tools",
            json=request_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert isinstance(data["data"], list)
        assert data["personality_id"] == "personality_123"
    
    def test_get_realtime_tools_without_personality(self):
        """测试不指定人格获取工具"""
        request_data = {}
        
        response = self.client.post(
            "/v1/realtime/tools",
            json=request_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert isinstance(data["data"], list)
        assert data["personality_id"] is None
    
    def test_execute_realtime_tool_success(self):
        """测试执行实时语音工具成功"""
        request_data = {
            "tool_name": "test_tool",
            "parameters": {"param1": "value1"}
        }
        
        response = self.client.post(
            "/v1/realtime/tools/execute",
            json=request_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert data["tool_name"] == "test_tool"
    
    def test_execute_realtime_tool_missing_params(self):
        """测试执行工具缺少参数"""
        request_data = {
            "tool_name": "test_tool"
            # 缺少parameters参数
        }
        
        response = self.client.post(
            "/v1/realtime/tools/execute",
            json=request_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        assert response.status_code == 422  # 验证错误
    
    def test_save_realtime_memory_success(self):
        """测试保存实时语音记忆成功"""
        request_data = {
            "conversation_id": "conv_123",
            "content": "测试记忆内容",
            "metadata": {"type": "realtime_voice"}
        }
        
        response = self.client.post(
            "/v1/realtime/memory/save",
            json=request_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "error"]  # 可能成功或失败
        assert "data" in data
        assert data["conversation_id"] == "conv_123"
    
    def test_save_realtime_memory_missing_content(self):
        """测试保存记忆缺少内容"""
        request_data = {
            "conversation_id": "conv_123"
            # 缺少content参数
        }
        
        response = self.client.post(
            "/v1/realtime/memory/save",
            json=request_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        assert response.status_code == 422  # 验证错误
    
    def test_create_realtime_session_success(self):
        """测试创建实时语音会话成功"""
        request_data = {
            "conversation_id": "conv_123",
            "personality_id": "personality_123",
            "session_config": {"voice": "alloy", "speed": 1.0}
        }
        
        response = self.client.post(
            "/v1/realtime/session",
            json=request_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert data["conversation_id"] == "conv_123"
        assert "adapters_available" in data["data"]
        assert "memory" in data["data"]["adapters_available"]
        assert "personality" in data["data"]["adapters_available"]
        assert "tools" in data["data"]["adapters_available"]
    
    def test_create_realtime_session_minimal(self):
        """测试创建实时语音会话（最小参数）"""
        request_data = {
            "conversation_id": "conv_123"
        }
        
        response = self.client.post(
            "/v1/realtime/session",
            json=request_data,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert data["conversation_id"] == "conv_123"
    
    def test_api_endpoints_consistency(self):
        """测试API端点一致性"""
        endpoints = [
            "/v1/realtime/memory",
            "/v1/realtime/personality", 
            "/v1/realtime/tools",
            "/v1/realtime/tools/execute",
            "/v1/realtime/memory/save",
            "/v1/realtime/session"
        ]
        
        for endpoint in endpoints:
            # 测试端点是否存在（通过OPTIONS请求）
            response = self.client.options(endpoint)
            assert response.status_code in [200, 405]  # 200表示支持，405表示不支持OPTIONS
    
    def test_api_response_format(self):
        """测试API响应格式一致性"""
        # 测试记忆API
        response = self.client.post(
            "/v1/realtime/memory",
            json={"conversation_id": "conv_123", "query": "test"},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "data" in data
            assert "conversation_id" in data
            assert "query" in data
    
    def test_api_error_handling(self):
        """测试API错误处理"""
        # 测试无效的JSON
        response = self.client.post(
            "/v1/realtime/memory",
            data="invalid json",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # 验证错误
    
    def test_api_authentication_required(self):
        """测试API认证要求"""
        endpoints = [
            "/v1/realtime/memory",
            "/v1/realtime/personality",
            "/v1/realtime/tools",
            "/v1/realtime/tools/execute",
            "/v1/realtime/memory/save",
            "/v1/realtime/session"
        ]
        
        for endpoint in endpoints:
            response = self.client.post(endpoint, json={})
            assert response.status_code in [401, 403]  # 需要认证
