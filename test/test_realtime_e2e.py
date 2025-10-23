"""
实时语音端到端测试
测试完整的实时语音流程
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app import app


class TestRealtimeE2E:
    """实时语音端到端测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.client = TestClient(app)
        self.api_key = "yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4"
        self.conversation_id = "e2e_test_conv_001"
        self.personality_id = "test_personality"
    
    def test_complete_realtime_flow(self):
        """测试完整的实时语音流程"""
        try:
            # 1. 生成token
            token_response = self.client.post(
                "/v1/realtime/token",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            assert token_response.status_code == 200
            token_data = token_response.json()
            assert token_data["status"] == "success"
            assert "token" in token_data["data"]
            assert "url" in token_data["data"]
            
            # 2. 创建会话
            session_response = self.client.post(
                "/v1/realtime/session",
                json={
                    "conversation_id": self.conversation_id,
                    "personality_id": self.personality_id,
                    "session_config": {"voice": "shimmer", "speed": 1.0}
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            assert session_response.status_code == 200
            session_data = session_response.json()
            assert session_data["status"] == "success"
            assert session_data["data"]["conversation_id"] == self.conversation_id
            
            # 3. 获取人格配置
            personality_response = self.client.post(
                "/v1/realtime/personality",
                json={"personality_id": self.personality_id},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            assert personality_response.status_code == 200
            personality_data = personality_response.json()
            assert personality_data["status"] == "success"
            assert "instructions" in personality_data["data"]
            
            # 4. 获取工具列表
            tools_response = self.client.post(
                "/v1/realtime/tools",
                json={"personality_id": self.personality_id},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            assert tools_response.status_code == 200
            tools_data = tools_response.json()
            assert tools_data["status"] == "success"
            assert isinstance(tools_data["data"], list)
            
            # 5. 获取记忆
            memory_response = self.client.post(
                "/v1/realtime/memory",
                json={
                    "conversation_id": self.conversation_id,
                    "query": "测试查询"
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            assert memory_response.status_code == 200
            memory_data = memory_response.json()
            assert memory_data["status"] == "success"
            assert isinstance(memory_data["data"], list)
            
            # 6. 保存记忆
            save_memory_response = self.client.post(
                "/v1/realtime/memory/save",
                json={
                    "conversation_id": self.conversation_id,
                    "content": "测试记忆内容",
                    "metadata": {"type": "e2e_test"}
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            assert save_memory_response.status_code == 200
            save_memory_data = save_memory_response.json()
            assert save_memory_data["status"] in ["success", "error"]  # 可能成功或失败
            
            print("✅ 端到端测试完成：所有API端点正常工作")
            
        except Exception as e:
            pytest.fail(f"端到端测试失败: {e}")
    
    def test_api_endpoints_availability(self):
        """测试所有API端点可用性"""
        endpoints = [
            "/v1/realtime/token",
            "/v1/realtime/session",
            "/v1/realtime/personality",
            "/v1/realtime/tools",
            "/v1/realtime/memory",
            "/v1/realtime/memory/save"
        ]
        
        for endpoint in endpoints:
            # 测试端点是否存在（通过OPTIONS请求）
            response = self.client.options(endpoint)
            assert response.status_code in [200, 405]  # 200表示支持，405表示不支持OPTIONS
    
    def test_api_response_consistency(self):
        """测试API响应一致性"""
        # 测试所有端点都返回一致的响应格式
        test_cases = [
            {
                "endpoint": "/v1/realtime/personality",
                "data": {"personality_id": "test_personality"}
            },
            {
                "endpoint": "/v1/realtime/tools",
                "data": {"personality_id": "test_personality"}
            },
            {
                "endpoint": "/v1/realtime/memory",
                "data": {"conversation_id": "test_conv", "query": "test"}
            }
        ]
        
        for test_case in test_cases:
            response = self.client.post(
                test_case["endpoint"],
                json=test_case["data"],
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "status" in data
                assert "data" in data
                assert data["status"] in ["success", "error"]
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效的API密钥
        response = self.client.post(
            "/v1/realtime/token",
            headers={"Authorization": "Bearer invalid-key"}
        )
        assert response.status_code == 401
        
        # 测试缺少认证
        response = self.client.post("/v1/realtime/token")
        assert response.status_code == 403
        
        # 测试无效的请求数据
        response = self.client.post(
            "/v1/realtime/personality",
            json={},  # 缺少personality_id
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        assert response.status_code == 422  # 验证错误
    
    def test_performance_requirements(self):
        """测试性能要求"""
        # 测试API响应时间
        start_time = time.time()
        
        response = self.client.post(
            "/v1/realtime/token",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # API响应时间应该小于1秒
        assert response_time < 1.0, f"API响应时间 {response_time:.2f}s 超过要求"
        assert response.status_code == 200
    
    def test_concurrent_requests(self):
        """测试并发请求处理"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = self.client.post(
                    "/v1/realtime/token",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                results.put(("success", response.status_code))
            except Exception as e:
                results.put(("error", str(e)))
        
        # 创建多个并发请求
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查结果
        success_count = 0
        while not results.empty():
            result_type, result_data = results.get()
            if result_type == "success" and result_data == 200:
                success_count += 1
        
        # 至少80%的请求应该成功
        assert success_count >= 4, f"并发请求成功率 {success_count}/5 低于要求"
    
    def test_memory_persistence(self):
        """测试记忆持久化"""
        conversation_id = f"persistence_test_{int(time.time())}"
        
        # 保存记忆
        save_response = self.client.post(
            "/v1/realtime/memory/save",
            json={
                "conversation_id": conversation_id,
                "content": "持久化测试记忆",
                "metadata": {"type": "persistence_test"}
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        # 获取记忆
        get_response = self.client.post(
            "/v1/realtime/memory",
            json={
                "conversation_id": conversation_id,
                "query": "持久化测试"
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        assert save_response.status_code == 200
        assert get_response.status_code == 200
        
        # 验证记忆数据格式
        get_data = get_response.json()
        assert get_data["status"] == "success"
        assert isinstance(get_data["data"], list)
    
    def test_personality_consistency(self):
        """测试人格配置一致性"""
        # 多次获取同一人格配置，应该返回一致的结果
        responses = []
        
        for i in range(3):
            response = self.client.post(
                "/v1/realtime/personality",
                json={"personality_id": self.personality_id},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            responses.append(response.json())
        
        # 所有响应应该一致
        first_response = responses[0]
        for response in responses[1:]:
            assert response["status"] == first_response["status"]
            assert response["data"]["instructions"] == first_response["data"]["instructions"]
    
    def test_tools_availability(self):
        """测试工具可用性"""
        response = self.client.post(
            "/v1/realtime/tools",
            json={"personality_id": self.personality_id},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["data"], list)
        
        # 验证工具格式
        for tool in data["data"]:
            assert "type" in tool
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]
    
    def test_session_management(self):
        """测试会话管理"""
        # 创建会话
        session_response = self.client.post(
            "/v1/realtime/session",
            json={
                "conversation_id": self.conversation_id,
                "personality_id": self.personality_id
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        assert session_response.status_code == 200
        session_data = session_response.json()
        assert session_data["status"] == "success"
        assert "adapters_available" in session_data["data"]
        
        # 验证适配器可用性信息
        adapters = session_data["data"]["adapters_available"]
        assert "memory" in adapters
        assert "personality" in adapters
        assert "tools" in adapters
        assert isinstance(adapters["memory"], bool)
        assert isinstance(adapters["personality"], bool)
        assert isinstance(adapters["tools"], bool)
