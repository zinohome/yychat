"""
实时语音性能测试
测试延迟、并发和内存使用
"""

import pytest
import time
import threading
import psutil
import os
from fastapi.testclient import TestClient
from app import app


class TestRealtimePerformance:
    """实时语音性能测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.client = TestClient(app)
        self.api_key = "yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4"
        self.initial_memory = psutil.Process().memory_info().rss
    
    def test_latency_requirements(self):
        """测试延迟要求 < 2秒"""
        # 测试token生成延迟
        start_time = time.time()
        
        response = self.client.post(
            "/v1/realtime/token",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        end_time = time.time()
        latency = end_time - start_time
        
        assert response.status_code == 200
        assert latency < 2.0, f"Token生成延迟 {latency:.2f}s 超过要求"
        
        # 测试会话创建延迟
        start_time = time.time()
        
        response = self.client.post(
            "/v1/realtime/session",
            json={
                "conversation_id": "perf_test_conv",
                "personality_id": "test_personality"
            },
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        end_time = time.time()
        latency = end_time - start_time
        
        assert response.status_code == 200
        assert latency < 2.0, f"会话创建延迟 {latency:.2f}s 超过要求"
        
        # 测试人格获取延迟
        start_time = time.time()
        
        response = self.client.post(
            "/v1/realtime/personality",
            json={"personality_id": "test_personality"},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        end_time = time.time()
        latency = end_time - start_time
        
        assert response.status_code == 200
        assert latency < 2.0, f"人格获取延迟 {latency:.2f}s 超过要求"
    
    def test_concurrent_sessions(self):
        """测试并发会话处理"""
        import queue
        
        results = queue.Queue()
        num_concurrent = 10
        
        def create_session(session_id):
            try:
                start_time = time.time()
                
                response = self.client.post(
                    "/v1/realtime/session",
                    json={
                        "conversation_id": f"concurrent_test_{session_id}",
                        "personality_id": "test_personality"
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                end_time = time.time()
                latency = end_time - start_time
                
                results.put(("success", response.status_code, latency))
                
            except Exception as e:
                results.put(("error", str(e), 0))
        
        # 创建并发线程
        threads = []
        for i in range(num_concurrent):
            thread = threading.Thread(target=create_session, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 分析结果
        success_count = 0
        total_latency = 0
        max_latency = 0
        
        while not results.empty():
            result_type, status_code, latency = results.get()
            if result_type == "success" and status_code == 200:
                success_count += 1
                total_latency += latency
                max_latency = max(max_latency, latency)
        
        # 验证并发性能
        success_rate = success_count / num_concurrent
        avg_latency = total_latency / success_count if success_count > 0 else 0
        
        assert success_rate >= 0.8, f"并发成功率 {success_rate:.2%} 低于要求"
        assert avg_latency < 2.0, f"平均延迟 {avg_latency:.2f}s 超过要求"
        assert max_latency < 5.0, f"最大延迟 {max_latency:.2f}s 超过要求"
    
    def test_memory_usage(self):
        """测试内存使用增长 < 20%"""
        # 记录初始内存
        initial_memory = psutil.Process().memory_info().rss
        
        # 执行多个操作
        for i in range(50):
            # 创建会话
            self.client.post(
                "/v1/realtime/session",
                json={
                    "conversation_id": f"memory_test_{i}",
                    "personality_id": "test_personality"
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            # 获取人格
            self.client.post(
                "/v1/realtime/personality",
                json={"personality_id": "test_personality"},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            # 获取工具
            self.client.post(
                "/v1/realtime/tools",
                json={"personality_id": "test_personality"},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        
        # 记录最终内存
        final_memory = psutil.Process().memory_info().rss
        memory_increase = final_memory - initial_memory
        memory_increase_percent = (memory_increase / initial_memory) * 100
        
        # 内存增长应该小于20%
        assert memory_increase_percent < 20, f"内存增长 {memory_increase_percent:.2f}% 超过要求"
    
    def test_cpu_usage(self):
        """测试CPU使用率"""
        import psutil
        
        # 记录初始CPU使用率
        initial_cpu = psutil.cpu_percent(interval=1)
        
        # 执行密集操作
        start_time = time.time()
        
        for i in range(20):
            # 并发请求
            threads = []
            for j in range(5):
                thread = threading.Thread(target=self._make_api_request, args=(i, j))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 记录最终CPU使用率
        final_cpu = psutil.cpu_percent(interval=1)
        
        # CPU使用率应该在合理范围内
        assert final_cpu < 80, f"CPU使用率 {final_cpu}% 过高"
        assert duration < 30, f"操作耗时 {duration:.2f}s 过长"
    
    def _make_api_request(self, i, j):
        """执行API请求"""
        try:
            self.client.post(
                "/v1/realtime/personality",
                json={"personality_id": "test_personality"},
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        except Exception:
            pass
    
    def test_response_time_consistency(self):
        """测试响应时间一致性"""
        response_times = []
        
        # 执行多次请求
        for i in range(10):
            start_time = time.time()
            
            response = self.client.post(
                "/v1/realtime/token",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200
            response_times.append(response_time)
        
        # 计算统计信息
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        # 响应时间应该一致
        assert avg_response_time < 1.0, f"平均响应时间 {avg_response_time:.2f}s 过长"
        assert max_response_time < 2.0, f"最大响应时间 {max_response_time:.2f}s 过长"
        assert min_response_time > 0.01, f"最小响应时间 {min_response_time:.2f}s 异常"
        
        # 响应时间差异不应该太大
        time_variance = max_response_time - min_response_time
        assert time_variance < 1.0, f"响应时间差异 {time_variance:.2f}s 过大"
    
    def test_throughput(self):
        """测试吞吐量"""
        start_time = time.time()
        request_count = 0
        
        # 在10秒内尽可能多地发送请求
        while time.time() - start_time < 10:
            try:
                self.client.post(
                    "/v1/realtime/token",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                request_count += 1
            except Exception:
                pass
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = request_count / duration
        
        # 吞吐量应该达到合理水平
        assert throughput > 1, f"吞吐量 {throughput:.2f} 请求/秒 过低"
        assert request_count > 10, f"总请求数 {request_count} 过少"
    
    def test_error_recovery(self):
        """测试错误恢复性能"""
        # 测试无效请求的响应时间
        start_time = time.time()
        
        response = self.client.post(
            "/v1/realtime/personality",
            json={},  # 无效请求
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        end_time = time.time()
        error_response_time = end_time - start_time
        
        # 错误响应应该快速
        assert error_response_time < 1.0, f"错误响应时间 {error_response_time:.2f}s 过长"
        assert response.status_code == 422  # 验证错误
    
    def test_resource_cleanup(self):
        """测试资源清理"""
        # 记录初始资源使用
        initial_memory = psutil.Process().memory_info().rss
        initial_fds = len(os.listdir('/proc/self/fd')) if os.path.exists('/proc/self/fd') else 0
        
        # 执行大量操作
        for i in range(100):
            try:
                self.client.post(
                    "/v1/realtime/session",
                    json={
                        "conversation_id": f"cleanup_test_{i}",
                        "personality_id": "test_personality"
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
            except Exception:
                pass
        
        # 等待资源清理
        time.sleep(2)
        
        # 记录最终资源使用
        final_memory = psutil.Process().memory_info().rss
        final_fds = len(os.listdir('/proc/self/fd')) if os.path.exists('/proc/self/fd') else 0
        
        # 资源使用应该合理
        memory_increase = final_memory - initial_memory
        assert memory_increase < 50 * 1024 * 1024, f"内存增长 {memory_increase / 1024 / 1024:.2f}MB 过大"
        
        if initial_fds > 0:
            fd_increase = final_fds - initial_fds
            assert fd_increase < 10, f"文件描述符增长 {fd_increase} 过多"
    
    def test_scalability(self):
        """测试可扩展性"""
        # 测试不同负载下的性能
        load_levels = [1, 5, 10, 20]
        results = {}
        
        for load in load_levels:
            start_time = time.time()
            
            # 创建并发请求
            threads = []
            for i in range(load):
                thread = threading.Thread(target=self._make_api_request, args=(load, i))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            end_time = time.time()
            duration = end_time - start_time
            
            results[load] = duration
        
        # 性能不应该随负载线性下降
        for load in load_levels[1:]:
            prev_load = load_levels[load_levels.index(load) - 1]
            prev_duration = results[prev_load]
            current_duration = results[load]
            
            # 性能下降应该合理
            performance_ratio = current_duration / prev_duration
            assert performance_ratio < 3.0, f"负载 {load} 性能下降 {performance_ratio:.2f} 倍过大"
