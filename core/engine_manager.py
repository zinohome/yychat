"""
引擎管理器
负责管理多个聊天引擎实例，支持动态切换
"""
import time
from typing import Dict, Any, Optional, List
from utils.log import log
from config.config import get_config

config = get_config()


class EngineManager:
    """
    引擎管理器
    
    职责：
    1. 管理多个引擎实例
    2. 支持动态切换引擎
    3. 提供引擎列表和信息查询
    4. 健康检查和监控
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """单例模式 - 改进版本，支持热重载"""
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化引擎管理器"""
        if EngineManager._initialized:
            return
            
        self.engines: Dict[str, Any] = {}  # 引擎实例字典
        self.current_engine_name: str = ""  # 当前使用的引擎名称
        EngineManager._initialized = True
        
        log.info("EngineManager初始化完成")
    
    def register_engine(self, name: str, engine_instance: Any) -> bool:
        """
        注册一个引擎实例
        
        Args:
            name: 引擎名称，如 "chat_engine"
            engine_instance: 引擎实例，必须继承BaseEngine
            
        Returns:
            是否注册成功
        """
        try:
            # 检查是否已存在
            if name in self.engines:
                log.warning(f"引擎 '{name}' 已存在，将被覆盖")
            
            # 注册引擎
            self.engines[name] = engine_instance
            log.info(f"✅ 引擎 '{name}' 注册成功")
            
            # 如果是第一个引擎，或者是配置中指定的引擎，设为当前引擎
            if not self.current_engine_name or name == config.CHAT_ENGINE:
                self.current_engine_name = name
                log.info(f"✅ 当前引擎设置为: {name}")
            
            return True
        except Exception as e:
            log.error(f"注册引擎 '{name}' 失败: {e}")
            return False
    
    def get_current_engine(self) -> Optional[Any]:
        """
        获取当前使用的引擎实例
        
        Returns:
            当前引擎实例，如果没有则返回None
        """
        if not self.current_engine_name:
            log.error("没有设置当前引擎")
            return None
        
        engine = self.engines.get(self.current_engine_name)
        if not engine:
            log.error(f"当前引擎 '{self.current_engine_name}' 不存在")
            return None
        
        return engine
    
    def get_engine(self, name: str) -> Optional[Any]:
        """
        获取指定名称的引擎实例
        
        Args:
            name: 引擎名称
            
        Returns:
            引擎实例，如果不存在则返回None
        """
        return self.engines.get(name)
    
    async def switch_engine(self, name: str) -> Dict[str, Any]:
        """
        切换当前使用的引擎
        
        Args:
            name: 目标引擎名称
            
        Returns:
            Dict包含切换结果:
            {
                "success": bool,
                "old_engine": str,
                "new_engine": str,
                "message": str
            }
        """
        old_engine = self.current_engine_name
        
        try:
            # 检查目标引擎是否存在
            if name not in self.engines:
                return {
                    "success": False,
                    "old_engine": old_engine,
                    "new_engine": None,
                    "message": f"引擎 '{name}' 不存在"
                }
            
            # 检查目标引擎健康状态
            target_engine = self.engines[name]
            health = await target_engine.health_check()
            
            if not health.get("healthy", False):
                log.warning(f"目标引擎 '{name}' 健康检查失败，但仍然切换")
            
            # 切换引擎
            self.current_engine_name = name
            log.info(f"✅ 引擎已从 '{old_engine}' 切换到 '{name}'")
            
            return {
                "success": True,
                "old_engine": old_engine,
                "new_engine": name,
                "message": f"成功切换到引擎: {name}",
                "health": health
            }
        except Exception as e:
            log.error(f"切换引擎失败: {e}")
            return {
                "success": False,
                "old_engine": old_engine,
                "new_engine": None,
                "message": f"切换失败: {str(e)}"
            }
    
    async def list_engines(self) -> List[Dict[str, Any]]:
        """
        列出所有已注册的引擎及其信息
        
        Returns:
            List[Dict]，每个Dict包含引擎信息
        """
        result = []
        
        for name, engine in self.engines.items():
            try:
                info = await engine.get_engine_info()
                info["is_current"] = (name == self.current_engine_name)
                result.append(info)
            except Exception as e:
                log.error(f"获取引擎 '{name}' 信息失败: {e}")
                result.append({
                    "name": name,
                    "status": "error",
                    "is_current": (name == self.current_engine_name),
                    "error": str(e)
                })
        
        return result
    
    async def health_check_all(self) -> Dict[str, Any]:
        """
        检查所有引擎的健康状态
        
        Returns:
            Dict包含所有引擎的健康状态
        """
        results = {}
        
        for name, engine in self.engines.items():
            try:
                health = await engine.health_check()
                results[name] = {
                    "healthy": health.get("healthy", False),
                    "is_current": (name == self.current_engine_name),
                    "details": health.get("details", {}),
                    "timestamp": health.get("timestamp", time.time())
                }
            except Exception as e:
                log.error(f"引擎 '{name}' 健康检查失败: {e}")
                results[name] = {
                    "healthy": False,
                    "is_current": (name == self.current_engine_name),
                    "error": str(e),
                    "timestamp": time.time()
                }
        
        return {
            "timestamp": time.time(),
            "current_engine": self.current_engine_name,
            "engines": results
        }
    
    def get_engine_count(self) -> int:
        """获取已注册引擎数量"""
        return len(self.engines)
    
    def get_engine_names(self) -> List[str]:
        """获取所有引擎名称"""
        return list(self.engines.keys())


# 全局引擎管理器实例
_engine_manager = EngineManager()


def get_engine_manager() -> EngineManager:
    """获取全局引擎管理器实例"""
    return _engine_manager


def get_current_engine() -> Optional[Any]:
    """获取当前引擎实例（快捷方法）"""
    return _engine_manager.get_current_engine()

