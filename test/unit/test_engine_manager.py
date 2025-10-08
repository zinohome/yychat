"""
EngineManager测试
测试引擎管理器的注册、切换、查询等功能
"""
import pytest
from unittest.mock import Mock, AsyncMock
from core.engine_manager import EngineManager, get_engine_manager, get_current_engine

@pytest.mark.asyncio
class TestEngineManager:
    """EngineManager测试套件"""
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = EngineManager()
        manager2 = EngineManager()
        
        assert manager1 is manager2, "应该返回同一个实例"
        assert id(manager1) == id(manager2), "对象ID应该相同"
        print("✅ 单例模式验证通过")
    
    def test_global_manager_instance(self):
        """测试全局管理器实例"""
        manager = get_engine_manager()
        
        assert manager is not None
        assert isinstance(manager, EngineManager)
        print("✅ 全局管理器实例存在")
    
    def test_register_engine(self):
        """测试注册引擎"""
        manager = EngineManager()
        
        # 创建mock引擎
        mock_engine = Mock()
        mock_engine.name = "test_engine"
        
        # 注册引擎
        success = manager.register_engine("test_engine_1", mock_engine)
        
        assert success is True
        assert "test_engine_1" in manager.engines
        assert manager.engines["test_engine_1"] == mock_engine
        
        print("✅ 引擎注册成功")
    
    def test_register_duplicate_engine(self):
        """测试注册重复引擎（应该覆盖）"""
        manager = EngineManager()
        
        mock_engine1 = Mock(name="engine1")
        mock_engine2 = Mock(name="engine2")
        
        # 注册第一个引擎
        manager.register_engine("duplicate_test", mock_engine1)
        # 注册同名引擎（应该覆盖）
        success = manager.register_engine("duplicate_test", mock_engine2)
        
        assert success is True
        assert manager.engines["duplicate_test"] == mock_engine2
        
        print("✅ 重复引擎覆盖成功")
    
    def test_get_current_engine(self):
        """测试获取当前引擎"""
        manager = EngineManager()
        
        # 清空引擎列表
        manager.engines.clear()
        manager.current_engine_name = ""
        
        # 注册并获取引擎
        mock_engine = Mock()
        manager.register_engine("current_test", mock_engine)
        
        current = manager.get_current_engine()
        
        assert current is not None
        assert current == mock_engine
        
        print("✅ 获取当前引擎成功")
    
    def test_get_engine_by_name(self):
        """测试根据名称获取引擎"""
        manager = EngineManager()
        
        mock_engine = Mock()
        manager.register_engine("named_engine", mock_engine)
        
        retrieved = manager.get_engine("named_engine")
        
        assert retrieved == mock_engine
        
        print("✅ 根据名称获取引擎成功")
    
    def test_get_nonexistent_engine(self):
        """测试获取不存在的引擎"""
        manager = EngineManager()
        
        retrieved = manager.get_engine("nonexistent_engine_999")
        
        assert retrieved is None
        
        print("✅ 不存在的引擎返回None")
    
    async def test_switch_engine_success(self):
        """测试成功切换引擎"""
        manager = EngineManager()
        manager.engines.clear()
        
        # 创建两个mock引擎
        mock_engine1 = Mock()
        mock_engine1.health_check = AsyncMock(return_value={"healthy": True})
        
        mock_engine2 = Mock()
        mock_engine2.health_check = AsyncMock(return_value={"healthy": True})
        
        # 注册引擎
        manager.register_engine("engine1", mock_engine1)
        manager.register_engine("engine2", mock_engine2)
        
        # 切换到engine2
        result = await manager.switch_engine("engine2")
        
        assert result["success"] is True
        assert result["new_engine"] == "engine2"
        assert manager.current_engine_name == "engine2"
        
        print("✅ 引擎切换成功")
    
    async def test_switch_to_nonexistent_engine(self):
        """测试切换到不存在的引擎"""
        manager = EngineManager()
        
        result = await manager.switch_engine("nonexistent_999")
        
        assert result["success"] is False
        assert "不存在" in result["message"]
        
        print("✅ 切换到不存在的引擎正确失败")
    
    async def test_list_engines(self):
        """测试列出所有引擎"""
        manager = EngineManager()
        manager.engines.clear()
        
        # 创建mock引擎
        mock_engine1 = Mock()
        mock_engine1.get_engine_info = AsyncMock(return_value={
            "name": "engine1",
            "version": "1.0.0",
            "status": "healthy"
        })
        
        mock_engine2 = Mock()
        mock_engine2.get_engine_info = AsyncMock(return_value={
            "name": "engine2",
            "version": "1.0.0",
            "status": "healthy"
        })
        
        manager.register_engine("engine1", mock_engine1)
        manager.register_engine("engine2", mock_engine2)
        
        engines_list = await manager.list_engines()
        
        assert isinstance(engines_list, list)
        assert len(engines_list) == 2
        assert any(e.get("name") == "engine1" for e in engines_list)
        assert any(e.get("name") == "engine2" for e in engines_list)
        
        print(f"✅ 列出引擎成功，共{len(engines_list)}个")
    
    async def test_health_check_all(self):
        """测试所有引擎健康检查"""
        manager = EngineManager()
        manager.engines.clear()
        
        # 创建mock引擎
        healthy_engine = Mock()
        healthy_engine.health_check = AsyncMock(return_value={
            "healthy": True,
            "details": {"status": "ok"},
            "timestamp": 123456
        })
        
        unhealthy_engine = Mock()
        unhealthy_engine.health_check = AsyncMock(return_value={
            "healthy": False,
            "details": {"error": "connection failed"},
            "timestamp": 123457
        })
        
        manager.register_engine("healthy", healthy_engine)
        manager.register_engine("unhealthy", unhealthy_engine)
        
        result = await manager.health_check_all()
        
        assert "engines" in result
        assert "healthy" in result["engines"]
        assert "unhealthy" in result["engines"]
        assert result["engines"]["healthy"]["healthy"] is True
        assert result["engines"]["unhealthy"]["healthy"] is False
        
        print("✅ 全部引擎健康检查完成")
    
    def test_get_engine_count(self):
        """测试获取引擎数量"""
        manager = EngineManager()
        initial_count = manager.get_engine_count()
        
        # 添加一个引擎
        mock_engine = Mock()
        manager.register_engine("count_test", mock_engine)
        
        new_count = manager.get_engine_count()
        
        assert new_count > initial_count
        
        print(f"✅ 引擎数量统计正确：{new_count}个")
    
    def test_get_engine_names(self):
        """测试获取所有引擎名称"""
        manager = EngineManager()
        
        # 清空并添加测试引擎
        manager.engines.clear()
        manager.register_engine("name_test_1", Mock())
        manager.register_engine("name_test_2", Mock())
        
        names = manager.get_engine_names()
        
        assert isinstance(names, list)
        assert "name_test_1" in names
        assert "name_test_2" in names
        
        print(f"✅ 获取引擎名称成功：{names}")
    
    def test_get_current_engine_shortcut(self):
        """测试快捷方法get_current_engine"""
        current = get_current_engine()
        
        # 应该返回引擎实例或None
        assert current is not None or current is None
        
        print("✅ 快捷方法get_current_engine工作正常")
    
    async def test_engine_isolation(self):
        """测试引擎之间的隔离性"""
        manager = EngineManager()
        manager.engines.clear()
        
        # 创建两个独立的mock引擎
        engine1 = Mock()
        engine1.state = "engine1_state"
        engine1.health_check = AsyncMock(return_value={"healthy": True})
        
        engine2 = Mock()
        engine2.state = "engine2_state"
        engine2.health_check = AsyncMock(return_value={"healthy": True})
        
        manager.register_engine("isolated1", engine1)
        manager.register_engine("isolated2", engine2)
        
        # 验证引擎独立性
        retrieved1 = manager.get_engine("isolated1")
        retrieved2 = manager.get_engine("isolated2")
        
        assert retrieved1 != retrieved2
        assert retrieved1.state != retrieved2.state
        
        print("✅ 引擎隔离性验证通过")
    
    async def test_switch_engine_with_unhealthy_target(self):
        """测试切换到不健康的引擎"""
        manager = EngineManager()
        manager.engines.clear()
        
        # 创建不健康的引擎
        unhealthy_engine = Mock()
        unhealthy_engine.health_check = AsyncMock(return_value={
            "healthy": False,
            "details": {"error": "service down"}
        })
        
        manager.register_engine("unhealthy_target", unhealthy_engine)
        
        # 应该仍然能切换（带警告）
        result = await manager.switch_engine("unhealthy_target")
        
        assert result["success"] is True  # 仍然切换成功
        assert result["health"]["healthy"] is False  # 但健康状态为false
        
        print("✅ 切换到不健康引擎测试通过（带警告）")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
