"""
性能监控模块
用于收集和分析系统性能指标
"""
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional
import time
import statistics
from datetime import datetime
from utils.log import log


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    request_id: str = ""
    timestamp: float = 0.0
    
    # 各阶段耗时
    memory_retrieval_time: float = 0.0
    memory_cache_hit: bool = False
    personality_apply_time: float = 0.0
    tool_schema_build_time: float = 0.0
    openai_api_time: float = 0.0
    first_chunk_time: float = 0.0
    tool_execution_time: float = 0.0
    total_time: float = 0.0
    
    # 请求特征
    stream: bool = False
    use_tools: bool = False
    tool_called: bool = False
    personality_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    def to_log_string(self) -> str:
        """转换为日志字符串"""
        parts = []
        parts.append(f"总耗时={self.total_time:.3f}s")
        
        if self.memory_retrieval_time > 0:
            hit_str = "✓缓存命中" if self.memory_cache_hit else "✗缓存未命中"
            parts.append(f"Memory={self.memory_retrieval_time:.3f}s({hit_str})")
        
        if self.personality_apply_time > 0:
            parts.append(f"Personality={self.personality_apply_time:.3f}s")
        
        if self.tool_schema_build_time > 0:
            parts.append(f"ToolSchema={self.tool_schema_build_time:.3f}s")
        
        if self.openai_api_time > 0:
            parts.append(f"OpenAI={self.openai_api_time:.3f}s")
        
        if self.first_chunk_time > 0:
            parts.append(f"首字节={self.first_chunk_time:.3f}s")
        
        if self.tool_execution_time > 0:
            parts.append(f"工具执行={self.tool_execution_time:.3f}s")
        
        return " | ".join(parts)


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 1000):
        self._metrics_history: List[PerformanceMetrics] = []
        self._max_history = max_history
        self._cache_hit_count = 0
        self._cache_miss_count = 0
    
    def record(self, metrics: PerformanceMetrics, log_enabled: bool = True):
        """记录性能指标"""
        self._metrics_history.append(metrics)
        
        # 统计缓存命中率
        if metrics.memory_retrieval_time > 0:
            if metrics.memory_cache_hit:
                self._cache_hit_count += 1
            else:
                self._cache_miss_count += 1
        
        # 限制历史记录数量
        if len(self._metrics_history) > self._max_history:
            self._metrics_history.pop(0)
        
        # 可选的日志记录
        if log_enabled:
            log.info(f"[PERF] {metrics.to_log_string()}")
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self._metrics_history:
            return {
                "status": "no_data",
                "message": "暂无性能数据"
            }
        
        # 计算各项统计
        total_times = [m.total_time for m in self._metrics_history]
        memory_times = [m.memory_retrieval_time for m in self._metrics_history if m.memory_retrieval_time > 0]
        openai_times = [m.openai_api_time for m in self._metrics_history if m.openai_api_time > 0]
        first_chunk_times = [m.first_chunk_time for m in self._metrics_history if m.first_chunk_time > 0]
        
        # 缓存命中率
        total_cache_requests = self._cache_hit_count + self._cache_miss_count
        cache_hit_rate = (self._cache_hit_count / total_cache_requests * 100) if total_cache_requests > 0 else 0
        
        stats = {
            "status": "ok",
            "summary": {
                "total_requests": len(self._metrics_history),
                "time_range": {
                    "from": datetime.fromtimestamp(self._metrics_history[0].timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                    "to": datetime.fromtimestamp(self._metrics_history[-1].timestamp).strftime("%Y-%m-%d %H:%M:%S")
                }
            },
            "total_time": {
                "avg": f"{statistics.mean(total_times):.3f}s",
                "median": f"{statistics.median(total_times):.3f}s",
                "min": f"{min(total_times):.3f}s",
                "max": f"{max(total_times):.3f}s",
                "p95": f"{self._percentile(total_times, 0.95):.3f}s",
                "p99": f"{self._percentile(total_times, 0.99):.3f}s"
            },
            "cache": {
                "hit_count": self._cache_hit_count,
                "miss_count": self._cache_miss_count,
                "hit_rate": f"{cache_hit_rate:.1f}%"
            }
        }
        
        # 添加Memory统计
        if memory_times:
            stats["memory_retrieval"] = {
                "avg": f"{statistics.mean(memory_times):.3f}s",
                "median": f"{statistics.median(memory_times):.3f}s",
                "min": f"{min(memory_times):.3f}s",
                "max": f"{max(memory_times):.3f}s"
            }
        
        # 添加OpenAI API统计
        if openai_times:
            stats["openai_api"] = {
                "avg": f"{statistics.mean(openai_times):.3f}s",
                "median": f"{statistics.median(openai_times):.3f}s",
                "min": f"{min(openai_times):.3f}s",
                "max": f"{max(openai_times):.3f}s"
            }
        
        # 添加首字节统计
        if first_chunk_times:
            stats["first_chunk"] = {
                "avg": f"{statistics.mean(first_chunk_times):.3f}s",
                "median": f"{statistics.median(first_chunk_times):.3f}s"
            }
        
        return stats
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """计算百分位数"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]
    
    def get_recent_metrics(self, count: int = 10) -> List[Dict]:
        """获取最近的指标"""
        recent = self._metrics_history[-count:]
        return [m.to_dict() for m in recent]
    
    def clear(self):
        """清除历史数据"""
        self._metrics_history.clear()
        self._cache_hit_count = 0
        self._cache_miss_count = 0
        log.info("[PERF] 性能监控数据已清除")


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    return performance_monitor

