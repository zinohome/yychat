"""
utils.performance tests
Tests the performance monitoring functionality
"""
import pytest
import time
from unittest.mock import patch, MagicMock

from utils.performance import (
    PerformanceMetrics, 
    PerformanceMonitor, 
    performance_monitor,
    get_performance_monitor
)


class TestPerformanceMetrics:
    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics instance"""
        metrics = PerformanceMetrics()
        assert metrics.request_id == ""
        assert metrics.timestamp == 0.0
        assert metrics.memory_retrieval_time == 0.0
        assert metrics.memory_cache_hit is False
        assert metrics.stream is False
        assert metrics.use_tools is False
        assert metrics.tool_called is False
        assert metrics.personality_id is None

    def test_performance_metrics_with_values(self):
        """Test PerformanceMetrics with specific values"""
        metrics = PerformanceMetrics(
            request_id="test_123",
            timestamp=1234567890.0,
            memory_retrieval_time=0.1,
            memory_cache_hit=True,
            personality_apply_time=0.05,
            tool_schema_build_time=0.02,
            openai_api_time=1.5,
            first_chunk_time=0.8,
            tool_execution_time=0.3,
            total_time=2.0,
            stream=True,
            use_tools=True,
            tool_called=True,
            personality_id="friendly"
        )
        
        assert metrics.request_id == "test_123"
        assert metrics.timestamp == 1234567890.0
        assert metrics.memory_retrieval_time == 0.1
        assert metrics.memory_cache_hit is True
        assert metrics.personality_apply_time == 0.05
        assert metrics.tool_schema_build_time == 0.02
        assert metrics.openai_api_time == 1.5
        assert metrics.first_chunk_time == 0.8
        assert metrics.tool_execution_time == 0.3
        assert metrics.total_time == 2.0
        assert metrics.stream is True
        assert metrics.use_tools is True
        assert metrics.tool_called is True
        assert metrics.personality_id == "friendly"

    def test_to_dict(self):
        """Test converting PerformanceMetrics to dictionary"""
        metrics = PerformanceMetrics(
            request_id="test_123",
            timestamp=1234567890.0,
            total_time=1.5
        )
        
        result = metrics.to_dict()
        assert isinstance(result, dict)
        assert result["request_id"] == "test_123"
        assert result["timestamp"] == 1234567890.0
        assert result["total_time"] == 1.5

    def test_to_log_string_basic(self):
        """Test converting PerformanceMetrics to log string"""
        metrics = PerformanceMetrics(total_time=1.5)
        result = metrics.to_log_string()
        assert "总耗时=1.500s" in result

    def test_to_log_string_with_memory(self):
        """Test log string with memory metrics"""
        metrics = PerformanceMetrics(
            total_time=1.5,
            memory_retrieval_time=0.1,
            memory_cache_hit=True
        )
        result = metrics.to_log_string()
        assert "总耗时=1.500s" in result
        assert "Memory=0.100s(✓缓存命中)" in result

    def test_to_log_string_with_memory_miss(self):
        """Test log string with memory cache miss"""
        metrics = PerformanceMetrics(
            total_time=1.5,
            memory_retrieval_time=0.1,
            memory_cache_hit=False
        )
        result = metrics.to_log_string()
        assert "Memory=0.100s(✗缓存未命中)" in result

    def test_to_log_string_with_all_metrics(self):
        """Test log string with all metrics"""
        metrics = PerformanceMetrics(
            total_time=2.0,
            memory_retrieval_time=0.1,
            memory_cache_hit=True,
            personality_apply_time=0.05,
            tool_schema_build_time=0.02,
            openai_api_time=1.5,
            first_chunk_time=0.8,
            tool_execution_time=0.3
        )
        result = metrics.to_log_string()
        assert "总耗时=2.000s" in result
        assert "Memory=0.100s(✓缓存命中)" in result
        assert "Personality=0.050s" in result
        assert "ToolSchema=0.020s" in result
        assert "OpenAI=1.500s" in result
        assert "首字节=0.800s" in result
        assert "工具执行=0.300s" in result


class TestPerformanceMonitor:
    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization"""
        monitor = PerformanceMonitor()
        assert monitor._max_history == 1000
        assert len(monitor._metrics_history) == 0
        assert monitor._cache_hit_count == 0
        assert monitor._cache_miss_count == 0

    def test_performance_monitor_custom_max_history(self):
        """Test PerformanceMonitor with custom max_history"""
        monitor = PerformanceMonitor(max_history=100)
        assert monitor._max_history == 100

    def test_record_metrics(self):
        """Test recording performance metrics"""
        monitor = PerformanceMonitor()
        metrics = PerformanceMetrics(
            request_id="test_123",
            timestamp=time.time(),
            total_time=1.5
        )
        
        with patch('utils.performance.log') as mock_log:
            monitor.record(metrics)
            assert len(monitor._metrics_history) == 1
            assert monitor._metrics_history[0] == metrics
            mock_log.info.assert_called_once()

    def test_record_metrics_without_logging(self):
        """Test recording metrics without logging"""
        monitor = PerformanceMonitor()
        metrics = PerformanceMetrics(
            request_id="test_123",
            timestamp=time.time(),
            total_time=1.5
        )
        
        with patch('utils.performance.log') as mock_log:
            monitor.record(metrics, log_enabled=False)
            assert len(monitor._metrics_history) == 1
            mock_log.info.assert_not_called()

    def test_record_metrics_with_cache_hit(self):
        """Test recording metrics with cache hit"""
        monitor = PerformanceMonitor()
        metrics = PerformanceMetrics(
            request_id="test_123",
            timestamp=time.time(),
            memory_retrieval_time=0.1,
            memory_cache_hit=True
        )
        
        monitor.record(metrics, log_enabled=False)
        assert monitor._cache_hit_count == 1
        assert monitor._cache_miss_count == 0

    def test_record_metrics_with_cache_miss(self):
        """Test recording metrics with cache miss"""
        monitor = PerformanceMonitor()
        metrics = PerformanceMetrics(
            request_id="test_123",
            timestamp=time.time(),
            memory_retrieval_time=0.1,
            memory_cache_hit=False
        )
        
        monitor.record(metrics, log_enabled=False)
        assert monitor._cache_hit_count == 0
        assert monitor._cache_miss_count == 1

    def test_record_metrics_no_memory_retrieval(self):
        """Test recording metrics without memory retrieval"""
        monitor = PerformanceMonitor()
        metrics = PerformanceMetrics(
            request_id="test_123",
            timestamp=time.time(),
            memory_retrieval_time=0.0
        )
        
        monitor.record(metrics, log_enabled=False)
        assert monitor._cache_hit_count == 0
        assert monitor._cache_miss_count == 0

    def test_max_history_limit(self):
        """Test max history limit"""
        monitor = PerformanceMonitor(max_history=3)
        
        # Add 5 metrics
        for i in range(5):
            metrics = PerformanceMetrics(
                request_id=f"test_{i}",
                timestamp=time.time(),
                total_time=1.0
            )
            monitor.record(metrics, log_enabled=False)
        
        # Should only keep the last 3
        assert len(monitor._metrics_history) == 3
        assert monitor._metrics_history[0].request_id == "test_2"
        assert monitor._metrics_history[1].request_id == "test_3"
        assert monitor._metrics_history[2].request_id == "test_4"

    def test_get_statistics_no_data(self):
        """Test get_statistics with no data"""
        monitor = PerformanceMonitor()
        stats = monitor.get_statistics()
        
        assert stats["status"] == "no_data"
        assert stats["message"] == "暂无性能数据"

    def test_get_statistics_with_data(self):
        """Test get_statistics with data"""
        monitor = PerformanceMonitor()
        
        # Add some test data
        base_time = time.time()
        for i in range(5):
            metrics = PerformanceMetrics(
                request_id=f"test_{i}",
                timestamp=base_time + i,
                total_time=1.0 + i * 0.1,
                memory_retrieval_time=0.1 if i % 2 == 0 else 0.0,
                memory_cache_hit=i % 2 == 0,
                openai_api_time=0.8 + i * 0.05,
                first_chunk_time=0.5 + i * 0.02
            )
            monitor.record(metrics, log_enabled=False)
        
        stats = monitor.get_statistics()
        
        assert stats["status"] == "ok"
        assert stats["summary"]["total_requests"] == 5
        assert "total_time" in stats
        assert "cache" in stats
        assert "memory_retrieval" in stats
        assert "openai_api" in stats
        assert "first_chunk" in stats

    def test_percentile_calculation(self):
        """Test percentile calculation"""
        monitor = PerformanceMonitor()
        
        # Test with known data
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        p95 = monitor._percentile(data, 0.95)
        p99 = monitor._percentile(data, 0.99)
        
        assert p95 == 5.0  # 95th percentile of [1,2,3,4,5] is 5
        assert p99 == 5.0  # 99th percentile of [1,2,3,4,5] is 5

    def test_get_recent_metrics(self):
        """Test getting recent metrics"""
        monitor = PerformanceMonitor()
        
        # Add 5 metrics
        for i in range(5):
            metrics = PerformanceMetrics(
                request_id=f"test_{i}",
                timestamp=time.time(),
                total_time=1.0
            )
            monitor.record(metrics, log_enabled=False)
        
        # Get last 3
        recent = monitor.get_recent_metrics(3)
        assert len(recent) == 3
        assert recent[0]["request_id"] == "test_2"
        assert recent[1]["request_id"] == "test_3"
        assert recent[2]["request_id"] == "test_4"

    def test_get_recent_metrics_more_than_available(self):
        """Test getting more recent metrics than available"""
        monitor = PerformanceMonitor()
        
        # Add 2 metrics
        for i in range(2):
            metrics = PerformanceMetrics(
                request_id=f"test_{i}",
                timestamp=time.time(),
                total_time=1.0
            )
            monitor.record(metrics, log_enabled=False)
        
        # Request 5 (more than available)
        recent = monitor.get_recent_metrics(5)
        assert len(recent) == 2

    def test_clear(self):
        """Test clearing performance data"""
        monitor = PerformanceMonitor()
        
        # Add some data
        metrics = PerformanceMetrics(
            request_id="test_123",
            timestamp=time.time(),
            total_time=1.5,
            memory_retrieval_time=0.1,
            memory_cache_hit=True
        )
        monitor.record(metrics, log_enabled=False)
        
        # Clear
        with patch('utils.performance.log') as mock_log:
            monitor.clear()
            assert len(monitor._metrics_history) == 0
            assert monitor._cache_hit_count == 0
            assert monitor._cache_miss_count == 0
            mock_log.info.assert_called_once_with("[PERF] 性能监控数据已清除")


class TestGlobalPerformanceMonitor:
    def test_global_performance_monitor(self):
        """Test global performance monitor instance"""
        assert performance_monitor is not None
        assert isinstance(performance_monitor, PerformanceMonitor)

    def test_get_performance_monitor(self):
        """Test get_performance_monitor function"""
        monitor = get_performance_monitor()
        assert monitor is not None
        assert isinstance(monitor, PerformanceMonitor)
        assert monitor is performance_monitor  # Should be the same instance

    def test_global_monitor_singleton(self):
        """Test that global monitor is a singleton"""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        assert monitor1 is monitor2
        assert monitor1 is performance_monitor
