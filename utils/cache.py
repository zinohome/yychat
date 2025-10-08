"""
统一缓存抽象层
支持内存缓存和Redis缓存，便于切换和扩展
"""
import pickle
import hashlib
from abc import ABC, abstractmethod
from typing import Any, Optional
from cachetools import TTLCache
from utils.log import log
from config.config import get_config

config = get_config()


class CacheBackend(ABC):
    """缓存后端抽象基类"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        pass
    
    @abstractmethod
    def delete(self, key: str):
        """删除缓存"""
        pass
    
    @abstractmethod
    def clear(self):
        """清空所有缓存"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查key是否存在"""
        pass
    
    def get_name(self) -> str:
        """获取缓存后端名称"""
        return self.__class__.__name__


class MemoryCache(CacheBackend):
    """
    内存缓存实现（基于cachetools.TTLCache）
    
    优点：
    - 速度快
    - 无需外部依赖
    
    缺点：
    - 服务重启丢失
    - 单实例，不共享
    """
    
    def __init__(self, maxsize: int = 1000, ttl: int = 1800):
        """
        Args:
            maxsize: 最大缓存条目数
            ttl: 默认过期时间（秒）
        """
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.default_ttl = ttl
        log.info(f"✅ MemoryCache初始化完成 (maxsize={maxsize}, ttl={ttl}s)")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            return self.cache.get(key)
        except Exception as e:
            log.error(f"MemoryCache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值（TTLCache不支持单独设置ttl，使用全局ttl）"""
        try:
            self.cache[key] = value
        except Exception as e:
            log.error(f"MemoryCache set error for key {key}: {e}")
    
    def delete(self, key: str):
        """删除缓存"""
        try:
            if key in self.cache:
                del self.cache[key]
        except Exception as e:
            log.error(f"MemoryCache delete error for key {key}: {e}")
    
    def clear(self):
        """清空所有缓存"""
        try:
            self.cache.clear()
            log.info("MemoryCache cleared")
        except Exception as e:
            log.error(f"MemoryCache clear error: {e}")
    
    def exists(self, key: str) -> bool:
        """检查key是否存在"""
        return key in self.cache


class RedisCache(CacheBackend):
    """
    Redis缓存实现
    
    优点：
    - 持久化存储
    - 支持分布式部署
    - 多实例共享
    
    缺点：
    - 需要Redis服务
    - 网络开销
    """
    
    def __init__(self):
        """初始化Redis客户端"""
        try:
            import redis
            
            self.client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                password=config.REDIS_PASSWORD if config.REDIS_PASSWORD else None,
                decode_responses=False,  # 使用bytes模式，便于pickle
                socket_timeout=5,
                socket_connect_timeout=5,
                health_check_interval=30
            )
            
            # 测试连接
            self.client.ping()
            
            log.info(f"✅ RedisCache初始化完成 ({config.REDIS_HOST}:{config.REDIS_PORT})")
        except Exception as e:
            log.error(f"❌ RedisCache初始化失败: {e}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            data = self.client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            log.error(f"RedisCache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        try:
            data = pickle.dumps(value)
            if ttl:
                self.client.setex(key, ttl, data)
            else:
                self.client.set(key, data)
        except Exception as e:
            log.error(f"RedisCache set error for key {key}: {e}")
    
    def delete(self, key: str):
        """删除缓存"""
        try:
            self.client.delete(key)
        except Exception as e:
            log.error(f"RedisCache delete error for key {key}: {e}")
    
    def clear(self):
        """清空所有缓存（慎用！会清空整个DB）"""
        try:
            self.client.flushdb()
            log.warning("⚠️ RedisCache cleared (flushdb)")
        except Exception as e:
            log.error(f"RedisCache clear error: {e}")
    
    def exists(self, key: str) -> bool:
        """检查key是否存在"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            log.error(f"RedisCache exists error for key {key}: {e}")
            return False
    
    def ping(self) -> bool:
        """健康检查"""
        try:
            return self.client.ping()
        except Exception as e:
            log.error(f"RedisCache ping error: {e}")
            return False


# 全局缓存实例
_cache_instance: Optional[CacheBackend] = None


def get_cache() -> CacheBackend:
    """
    获取全局缓存实例（单例）
    
    根据配置返回Memory或Redis缓存
    """
    global _cache_instance
    
    if _cache_instance is not None:
        return _cache_instance
    
    try:
        if config.USE_REDIS_CACHE:
            log.info("🔄 初始化Redis缓存...")
            _cache_instance = RedisCache()
        else:
            log.info("🔄 初始化内存缓存...")
            _cache_instance = MemoryCache(
                maxsize=config.MEMORY_CACHE_MAXSIZE,
                ttl=config.MEMORY_CACHE_TTL
            )
        
        return _cache_instance
    except Exception as e:
        log.error(f"初始化缓存失败: {e}")
        # 降级到内存缓存
        log.warning("⚠️ 降级到内存缓存")
        _cache_instance = MemoryCache()
        return _cache_instance


def reset_cache():
    """重置缓存实例（主要用于测试）"""
    global _cache_instance
    _cache_instance = None


def hash_key(*args, **kwargs) -> str:
    """
    生成缓存key的hash值
    
    Example:
        key = hash_key("memory", conversation_id="123", query="hello")
    """
    key_str = ":".join(str(arg) for arg in args)
    if kwargs:
        key_str += ":" + ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    
    return hashlib.md5(key_str.encode('utf-8')).hexdigest()

