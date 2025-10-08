"""
Redis缓存测试脚本
用于验证缓存系统是否正常工作
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cache import get_cache
from config.config import get_config
import time

config = get_config()


def test_cache():
    """测试缓存功能"""
    print("=" * 60)
    print("  Redis缓存系统测试")
    print("=" * 60)
    print("")
    
    # 显示配置
    print(f"配置信息:")
    print(f"  - USE_REDIS_CACHE: {config.USE_REDIS_CACHE}")
    if config.USE_REDIS_CACHE:
        print(f"  - REDIS_HOST: {config.REDIS_HOST}")
        print(f"  - REDIS_PORT: {config.REDIS_PORT}")
        print(f"  - REDIS_DB: {config.REDIS_DB}")
    else:
        print(f"  - MEMORY_CACHE_MAXSIZE: {config.MEMORY_CACHE_MAXSIZE}")
        print(f"  - MEMORY_CACHE_TTL: {config.MEMORY_CACHE_TTL}")
    print("")
    
    # 获取缓存实例
    try:
        cache = get_cache()
        print(f"✅ 缓存后端: {cache.get_name()}")
        print("")
    except Exception as e:
        print(f"❌ 初始化缓存失败: {e}")
        return False
    
    # 测试1: Set/Get
    print("测试1: Set/Get")
    try:
        test_data = {
            "message": "Hello World",
            "timestamp": time.time(),
            "nested": {"key": "value"}
        }
        cache.set("test_key_1", test_data, ttl=60)
        retrieved = cache.get("test_key_1")
        
        if retrieved == test_data:
            print("  ✅ Set/Get 测试通过")
        else:
            print(f"  ❌ Set/Get 测试失败: {retrieved}")
            return False
    except Exception as e:
        print(f"  ❌ Set/Get 测试异常: {e}")
        return False
    print("")
    
    # 测试2: Exists
    print("测试2: Exists")
    try:
        exists_before = cache.exists("test_key_1")
        cache.delete("test_key_1")
        exists_after = cache.exists("test_key_1")
        
        if exists_before and not exists_after:
            print("  ✅ Exists 测试通过")
        else:
            print(f"  ❌ Exists 测试失败: before={exists_before}, after={exists_after}")
            return False
    except Exception as e:
        print(f"  ❌ Exists 测试异常: {e}")
        return False
    print("")
    
    # 测试3: Delete
    print("测试3: Delete")
    try:
        cache.set("test_key_2", "test_value")
        cache.delete("test_key_2")
        value = cache.get("test_key_2")
        
        if value is None:
            print("  ✅ Delete 测试通过")
        else:
            print(f"  ❌ Delete 测试失败: value={value}")
            return False
    except Exception as e:
        print(f"  ❌ Delete 测试异常: {e}")
        return False
    print("")
    
    # 测试4: Multiple Set/Get
    print("测试4: Multiple Set/Get")
    try:
        for i in range(5):
            cache.set(f"test_key_{i}", f"value_{i}")
        
        success = True
        for i in range(5):
            value = cache.get(f"test_key_{i}")
            if value != f"value_{i}":
                print(f"  ❌ 第{i}个key失败: expected=value_{i}, got={value}")
                success = False
                break
        
        if success:
            print("  ✅ Multiple Set/Get 测试通过")
        
        # 清理
        for i in range(5):
            cache.delete(f"test_key_{i}")
            
        if not success:
            return False
    except Exception as e:
        print(f"  ❌ Multiple Set/Get 测试异常: {e}")
        return False
    print("")
    
    # 测试5: TTL (仅Redis)
    if config.USE_REDIS_CACHE:
        print("测试5: TTL 过期")
        try:
            cache.set("test_ttl", "expire_soon", ttl=2)
            value_before = cache.get("test_ttl")
            print(f"  等待3秒...")
            time.sleep(3)
            value_after = cache.get("test_ttl")
            
            if value_before == "expire_soon" and value_after is None:
                print("  ✅ TTL 测试通过")
            else:
                print(f"  ❌ TTL 测试失败: before={value_before}, after={value_after}")
                return False
        except Exception as e:
            print(f"  ❌ TTL 测试异常: {e}")
            return False
        print("")
    
    # 测试6: Redis Health Check (仅Redis)
    if config.USE_REDIS_CACHE and hasattr(cache, 'ping'):
        print("测试6: Redis Health Check")
        try:
            is_healthy = cache.ping()
            if is_healthy:
                print("  ✅ Redis健康检查通过")
            else:
                print("  ❌ Redis健康检查失败")
                return False
        except Exception as e:
            print(f"  ❌ Redis健康检查异常: {e}")
            return False
        print("")
    
    print("=" * 60)
    print("  ✅ 所有测试通过！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_cache()
    sys.exit(0 if success else 1)

