"""
Voice Performance Monitor for real-time voice chat.

This module provides comprehensive performance monitoring and metrics
collection for voice processing, connection management, and system resources.
"""

import time
import psutil
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque
from utils.log import log


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    timestamp: float
    value: float
    metric_type: str
    client_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_sent_mb: float
    network_recv_mb: float
    timestamp: float


class VoicePerformanceMonitor:
    """
    Monitors voice chat performance and system resources.
    
    Provides comprehensive performance tracking for audio processing,
    connection management, and system resource utilization.
    """
    
    def __init__(self, max_samples: int = 1000, collection_interval: float = 1.0):
        """
        Initialize the performance monitor.
        
        Args:
            max_samples: Maximum number of samples to keep in memory
            collection_interval: Metrics collection interval in seconds
        """
        self.max_samples = max_samples
        self.collection_interval = collection_interval
        
        # Metrics storage
        self.metrics: Dict[str, deque] = {
            'audio_processing_time': deque(maxlen=max_samples),
            'tts_generation_time': deque(maxlen=max_samples),
            'stt_processing_time': deque(maxlen=max_samples),
            'connection_count': deque(maxlen=max_samples),
            'message_throughput': deque(maxlen=max_samples),
            'error_rate': deque(maxlen=max_samples),
            'system_cpu': deque(maxlen=max_samples),
            'system_memory': deque(maxlen=max_samples),
            'system_network': deque(maxlen=max_samples)
        }
        
        # System metrics
        self.system_metrics: List[SystemMetrics] = []
        self.network_start = None
        self.network_sent_start = 0
        self.network_recv_start = 0
        
        # Collection task
        self.collection_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Statistics
        self.stats = {
            'total_metrics_collected': 0,
            'collection_start_time': 0,
            'last_collection_time': 0,
            'collection_errors': 0
        }
        
        # Initialize network baseline
        self._initialize_network_baseline()
        
        log.info(f"VoicePerformanceMonitor initialized: max_samples={max_samples}, "
                f"collection_interval={collection_interval}s")
    
    def _initialize_network_baseline(self):
        """Initialize network usage baseline"""
        try:
            net_io = psutil.net_io_counters()
            self.network_sent_start = net_io.bytes_sent
            self.network_recv_start = net_io.bytes_recv
            self.network_start = time.time()
        except Exception as e:
            log.warning(f"Failed to initialize network baseline: {e}")
    
    async def start(self):
        """Start performance monitoring"""
        if self.is_running:
            log.warning("Performance monitor already running")
            return
        
        self.is_running = True
        self.stats['collection_start_time'] = time.time()
        self.collection_task = asyncio.create_task(self._collection_loop())
        
        log.info("Performance monitor started")
    
    async def stop(self):
        """Stop performance monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        
        log.info("Performance monitor stopped")
    
    async def _collection_loop(self):
        """Background metrics collection loop"""
        while self.is_running:
            try:
                await asyncio.sleep(self.collection_interval)
                await self._collect_system_metrics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Metrics collection error: {e}")
                self.stats['collection_errors'] += 1
    
    async def _collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # Network usage
            net_io = psutil.net_io_counters()
            current_time = time.time()
            
            if self.network_start:
                time_diff = current_time - self.network_start
                if time_diff > 0:
                    network_sent_mb = (net_io.bytes_sent - self.network_sent_start) / (1024 * 1024)
                    network_recv_mb = (net_io.bytes_recv - self.network_recv_start) / (1024 * 1024)
                else:
                    network_sent_mb = 0
                    network_recv_mb = 0
            else:
                network_sent_mb = 0
                network_recv_mb = 0
            
            # Create system metrics
            system_metric = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                disk_usage_percent=disk_usage_percent,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                timestamp=current_time
            )
            
            # Store metrics
            self.system_metrics.append(system_metric)
            if len(self.system_metrics) > self.max_samples:
                self.system_metrics.pop(0)
            
            # Store in metrics deque
            self.metrics['system_cpu'].append(cpu_percent)
            self.metrics['system_memory'].append(memory_percent)
            self.metrics['system_network'].append(network_sent_mb + network_recv_mb)
            
            # Update statistics
            self.stats['total_metrics_collected'] += 1
            self.stats['last_collection_time'] = current_time
            
        except Exception as e:
            log.error(f"Failed to collect system metrics: {e}")
            self.stats['collection_errors'] += 1
    
    def record_audio_processing_time(self, processing_time: float, client_id: str = None):
        """Record audio processing time"""
        metric = PerformanceMetric(
            timestamp=time.time(),
            value=processing_time,
            metric_type='audio_processing',
            client_id=client_id
        )
        self.metrics['audio_processing_time'].append(processing_time)
        self._log_metric(metric)
    
    def record_tts_generation_time(self, generation_time: float, client_id: str = None):
        """Record TTS generation time"""
        metric = PerformanceMetric(
            timestamp=time.time(),
            value=generation_time,
            metric_type='tts_generation',
            client_id=client_id
        )
        self.metrics['tts_generation_time'].append(generation_time)
        self._log_metric(metric)
    
    def record_stt_processing_time(self, processing_time: float, client_id: str = None):
        """Record STT processing time"""
        metric = PerformanceMetric(
            timestamp=time.time(),
            value=processing_time,
            metric_type='stt_processing',
            client_id=client_id
        )
        self.metrics['stt_processing_time'].append(processing_time)
        self._log_metric(metric)
    
    def record_connection_count(self, connection_count: int):
        """Record connection count"""
        self.metrics['connection_count'].append(connection_count)
    
    def record_message_throughput(self, messages_per_second: float):
        """Record message throughput"""
        self.metrics['message_throughput'].append(messages_per_second)
    
    def record_error_rate(self, error_rate: float):
        """Record error rate"""
        self.metrics['error_rate'].append(error_rate)
    
    def _log_metric(self, metric: PerformanceMetric):
        """Log performance metric"""
        log.debug(f"Performance metric: {metric.metric_type}={metric.value:.3f}s, "
                  f"client={metric.client_id}, timestamp={metric.timestamp}")
    
    def get_performance_summary(self) -> dict:
        """
        Get comprehensive performance summary.
        
        Returns:
            dict: Performance summary with statistics
        """
        summary = {
            'collection_stats': {
                'is_running': self.is_running,
                'total_metrics': self.stats['total_metrics_collected'],
                'collection_errors': self.stats['collection_errors'],
                'uptime': time.time() - self.stats['collection_start_time'] if self.stats['collection_start_time'] else 0
            },
            'audio_metrics': self._get_metric_summary('audio_processing_time'),
            'tts_metrics': self._get_metric_summary('tts_generation_time'),
            'stt_metrics': self._get_metric_summary('stt_processing_time'),
            'connection_metrics': self._get_metric_summary('connection_count'),
            'throughput_metrics': self._get_metric_summary('message_throughput'),
            'error_metrics': self._get_metric_summary('error_rate'),
            'system_metrics': self._get_system_metrics_summary()
        }
        
        return summary
    
    def _get_metric_summary(self, metric_name: str) -> dict:
        """Get summary for a specific metric"""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {'count': 0, 'average': 0, 'min': 0, 'max': 0, 'latest': 0}
        
        values = list(self.metrics[metric_name])
        return {
            'count': len(values),
            'average': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'latest': values[-1] if values else 0
        }
    
    def _get_system_metrics_summary(self) -> dict:
        """Get system metrics summary"""
        if not self.system_metrics:
            return {'cpu': 0, 'memory': 0, 'disk': 0, 'network': 0}
        
        latest = self.system_metrics[-1]
        return {
            'cpu_percent': latest.cpu_percent,
            'memory_percent': latest.memory_percent,
            'memory_used_mb': latest.memory_used_mb,
            'disk_usage_percent': latest.disk_usage_percent,
            'network_sent_mb': latest.network_sent_mb,
            'network_recv_mb': latest.network_recv_mb,
            'timestamp': latest.timestamp
        }
    
    def get_metric_history(self, metric_name: str, limit: int = 100) -> List[float]:
        """
        Get metric history.
        
        Args:
            metric_name: Name of the metric
            limit: Maximum number of values to return
            
        Returns:
            List[float]: Metric values
        """
        if metric_name not in self.metrics:
            return []
        
        values = list(self.metrics[metric_name])
        return values[-limit:] if limit > 0 else values
    
    def get_system_metrics_history(self, limit: int = 100) -> List[dict]:
        """
        Get system metrics history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List[dict]: System metrics history
        """
        if not self.system_metrics:
            return []
        
        metrics = self.system_metrics[-limit:] if limit > 0 else self.system_metrics
        return [
            {
                'cpu_percent': m.cpu_percent,
                'memory_percent': m.memory_percent,
                'memory_used_mb': m.memory_used_mb,
                'disk_usage_percent': m.disk_usage_percent,
                'network_sent_mb': m.network_sent_mb,
                'network_recv_mb': m.network_recv_mb,
                'timestamp': m.timestamp
            }
            for m in metrics
        ]
    
    def clear_metrics(self):
        """Clear all metrics"""
        for metric_deque in self.metrics.values():
            metric_deque.clear()
        
        self.system_metrics.clear()
        self.stats = {
            'total_metrics_collected': 0,
            'collection_start_time': 0,
            'last_collection_time': 0,
            'collection_errors': 0
        }
        
        log.info("Performance metrics cleared")
    
    def get_alerts(self) -> List[dict]:
        """
        Get performance alerts based on thresholds.
        
        Returns:
            List[dict]: List of performance alerts
        """
        alerts = []
        current_time = time.time()
        
        # CPU alert
        if self.metrics['system_cpu']:
            latest_cpu = self.metrics['system_cpu'][-1]
            if latest_cpu > 80:
                alerts.append({
                    'type': 'high_cpu',
                    'message': f'High CPU usage: {latest_cpu:.1f}%',
                    'severity': 'warning',
                    'timestamp': current_time
                })
        
        # Memory alert
        if self.metrics['system_memory']:
            latest_memory = self.metrics['system_memory'][-1]
            if latest_memory > 90:
                alerts.append({
                    'type': 'high_memory',
                    'message': f'High memory usage: {latest_memory:.1f}%',
                    'severity': 'critical',
                    'timestamp': current_time
                })
        
        # Audio processing time alert
        if self.metrics['audio_processing_time']:
            latest_audio = self.metrics['audio_processing_time'][-1]
            if latest_audio > 5.0:  # 5 seconds
                alerts.append({
                    'type': 'slow_audio_processing',
                    'message': f'Slow audio processing: {latest_audio:.2f}s',
                    'severity': 'warning',
                    'timestamp': current_time
                })
        
        return alerts
