"""
utils.cache tests
Covers MemoryCache basic ops, get_cache singleton fallback, and hash_key uniqueness
"""
import pytest
from unittest.mock import patch

from utils.cache import MemoryCache, get_cache, reset_cache, hash_key


class TestMemoryCache:
    def test_memory_cache_basic(self):
        cache = MemoryCache(maxsize=10, ttl=30)
        cache.set("k1", "v1")
        assert cache.get("k1") == "v1"
        assert cache.exists("k1")
        cache.delete("k1")
        assert cache.get("k1") is None
        cache.set("k2", 123)
        cache.clear()
        assert not cache.exists("k2")

    def test_get_cache_singleton_memory(self):
        reset_cache()
        with patch("utils.cache.config") as mock_cfg:
            mock_cfg.USE_REDIS_CACHE = False
            mock_cfg.MEMORY_CACHE_MAXSIZE = 5
            mock_cfg.MEMORY_CACHE_TTL = 10
            c1 = get_cache()
            c2 = get_cache()
            assert c1 is c2
            assert isinstance(c1, MemoryCache)

    def test_get_cache_fallback_on_error(self):
        reset_cache()
        with patch("utils.cache.config") as mock_cfg, \
             patch("utils.cache.RedisCache", side_effect=Exception("redis down")):
            mock_cfg.USE_REDIS_CACHE = True
            # Should fallback to MemoryCache
            c = get_cache()
            assert isinstance(c, MemoryCache)

    def test_hash_key_uniqueness_and_order(self):
        k1 = hash_key("a", 1, x=2, y=3)
        k2 = hash_key("a", 1, y=3, x=2)  # kwargs order independent
        k3 = hash_key("a", 2, x=2, y=3)
        assert k1 == k2
        assert k1 != k3
