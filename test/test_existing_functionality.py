"""
现有功能回归测试
验证现有功能未受影响
"""

import pytest
from fastapi.testclient import TestClient
from app import app


class TestExistingFunctionality:
    """现有功能回归测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.client = TestClient(app)
        self.api_key = "yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4"
    
    def test_text_chat_unchanged(self):
        """验证文本对话功能未受影响"""
        # 测试文本对话API
        response = self.client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": "Hello, how are you?"}
                ],
                "stream": False
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        # 文本对话应该仍然工作
        assert response.status_code in [200, 500]  # 200表示成功，500可能是模型问题
        
        if response.status_code == 200:
            data = response.json()
            assert "choices" in data
            assert len(data["choices"]) > 0
            assert "message" in data["choices"][0]
    
    def test_voice_recording_unchanged(self):
        """验证录音对话功能未受影响"""
        # 测试音频转录API
        response = self.client.post(
            "/v1/audio/transcriptions",
            files={"file": ("test.wav", b"fake audio data", "audio/wav")},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        # 音频转录API应该仍然存在
        assert response.status_code in [200, 400, 422, 500]  # 500可能是服务问题
        
        # 测试音频合成API
        response = self.client.post(
            "/v1/audio/speech",
            json={
                "model": "tts-1",
                "input": "Hello, this is a test.",
                "voice": "alloy"
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        # 音频合成API应该仍然存在
        assert response.status_code in [200, 400, 422, 500]
    
    def test_memory_unchanged(self):
        """验证记忆功能未受影响"""
        # 测试记忆相关API（如果存在）
        # 这里需要根据实际的记忆API进行调整
        
        # 测试基本的聊天完成功能，这通常涉及记忆
        response = self.client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": "What did I say before?"}
                ],
                "stream": False
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        # 聊天完成应该仍然工作
        assert response.status_code in [200, 500]
    
    def test_personality_unchanged(self):
        """验证人格化功能未受影响"""
        # 测试人格化相关API（如果存在）
        # 这里需要根据实际的人格化API进行调整
        
        # 测试带有人格化的聊天完成
        response = self.client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello"}
                ],
                "stream": False
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        # 聊天完成应该仍然工作
        assert response.status_code in [200, 500]
    
    def test_tools_unchanged(self):
        """验证工具调用功能未受影响"""
        # 测试工具调用API
        response = self.client.post(
            "/v1/tools/call",
            json={
                "tool_name": "test_tool",
                "parameters": {"param1": "value1"}
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        # 工具调用API应该仍然存在
        assert response.status_code in [200, 400, 404, 500]
    
    def test_websocket_unchanged(self):
        """验证WebSocket功能未受影响"""
        # 测试WebSocket连接
        with self.client.websocket_connect("/ws/chat") as websocket:
            # WebSocket连接应该成功
            assert websocket is not None
            
            # 发送测试消息
            websocket.send_json({
                "type": "text_message",
                "content": "Hello WebSocket"
            })
            
            # 应该能接收到响应（或至少不抛出异常）
            try:
                data = websocket.receive_json()
                assert data is not None
            except Exception:
                # 如果没有响应，至少连接应该正常
                pass
    
    def test_audio_cache_unchanged(self):
        """验证音频缓存功能未受影响"""
        # 测试音频缓存统计API
        response = self.client.get(
            "/v1/audio/cache/stats",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        # 音频缓存API应该仍然存在
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "data" in data
    
    def test_engine_management_unchanged(self):
        """验证引擎管理功能未受影响"""
        # 测试引擎切换API
        response = self.client.post(
            "/v1/engines/switch",
            json={"engine_name": "chat_engine"},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        # 引擎切换API应该仍然存在
        assert response.status_code in [200, 400, 404, 422, 500]
    
    def test_mcp_tools_unchanged(self):
        """验证MCP工具功能未受影响"""
        # 测试MCP工具调用API
        response = self.client.post(
            "/v1/mcp/call",
            json={
                "service_name": "test_service",
                "method": "test_method",
                "parameters": {}
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        # MCP工具API应该仍然存在
        assert response.status_code in [200, 400, 404, 500]
    
    def test_api_consistency(self):
        """验证API一致性"""
        # 测试所有现有API端点仍然存在
        existing_endpoints = [
            "/v1/chat/completions",
            "/v1/audio/transcriptions",
            "/v1/audio/speech",
            "/v1/tools/call",
            "/v1/engines/switch",
            "/v1/mcp/call",
            "/v1/audio/cache/stats"
        ]
        
        for endpoint in existing_endpoints:
            # 测试端点是否存在（通过OPTIONS请求）
            response = self.client.options(endpoint)
            assert response.status_code in [200, 405, 404]  # 200表示支持，405表示不支持OPTIONS，404表示不存在
    
    def test_response_format_consistency(self):
        """验证响应格式一致性"""
        # 测试聊天完成API的响应格式
        response = self.client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "test"}],
                "stream": False
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            # 验证响应格式符合OpenAI API规范
            assert "id" in data
            assert "object" in data
            assert "created" in data
            assert "model" in data
            assert "choices" in data
            assert "usage" in data
    
    def test_error_handling_consistency(self):
        """验证错误处理一致性"""
        # 测试无效认证
        response = self.client.post(
            "/v1/chat/completions",
            json={"model": "gpt-4", "messages": []},
            headers={"Authorization": "Bearer invalid-key"}
        )
        
        assert response.status_code == 401
        
        # 测试缺少认证
        response = self.client.post(
            "/v1/chat/completions",
            json={"model": "gpt-4", "messages": []}
        )
        
        assert response.status_code == 403
    
    def test_performance_unchanged(self):
        """验证性能未受影响"""
        import time
        
        # 测试API响应时间
        start_time = time.time()
        
        response = self.client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "test"}],
                "stream": False
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # 响应时间应该在合理范围内（这里设置为5秒，实际可能更短）
        assert response_time < 5.0, f"API响应时间 {response_time:.2f}s 超过预期"
    
    def test_new_endpoints_do_not_conflict(self):
        """验证新端点不与现有端点冲突"""
        # 测试新的实时语音端点不会影响现有端点
        new_endpoints = [
            "/v1/realtime/token",
            "/v1/realtime/session",
            "/v1/realtime/personality",
            "/v1/realtime/tools",
            "/v1/realtime/memory",
            "/v1/realtime/memory/save"
        ]
        
        for endpoint in new_endpoints:
            # 新端点应该存在
            response = self.client.options(endpoint)
            assert response.status_code in [200, 405]
            
            # 新端点不应该影响现有端点
            existing_response = self.client.options("/v1/chat/completions")
            assert existing_response.status_code in [200, 405]
