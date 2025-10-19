"""
记忆适配器测试
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from adapters.memory_adapter import MemoryAdapter, memory_adapter


class TestMemoryAdapter:
    """记忆适配器测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.adapter = MemoryAdapter()
    
    def test_adapter_initialization(self):
        """测试适配器初始化"""
        assert self.adapter is not None
        assert hasattr(self.adapter, 'memory')
    
    def test_global_adapter_instance(self):
        """测试全局适配器实例"""
        assert memory_adapter is not None
        assert isinstance(memory_adapter, MemoryAdapter)
    
    @pytest.mark.asyncio
    async def test_get_relevant_memory_success(self):
        """测试获取相关记忆成功"""
        # 模拟记忆系统
        mock_memory = Mock()
        mock_memory.get_relevant_memory = AsyncMock(return_value=["记忆1", "记忆2"])
        
        with patch.object(self.adapter, 'memory', mock_memory):
            result = await self.adapter.get_relevant_memory("conv_123", "测试查询")
            
            assert result == ["记忆1", "记忆2"]
            mock_memory.get_relevant_memory.assert_called_once_with("conv_123", "测试查询")
    
    @pytest.mark.asyncio
    async def test_get_relevant_memory_no_memory_system(self):
        """测试记忆系统未初始化"""
        with patch.object(self.adapter, 'memory', None):
            result = await self.adapter.get_relevant_memory("conv_123", "测试查询")
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_relevant_memory_exception(self):
        """测试获取记忆异常"""
        mock_memory = Mock()
        mock_memory.get_relevant_memory = AsyncMock(side_effect=Exception("测试异常"))
        
        with patch.object(self.adapter, 'memory', mock_memory):
            result = await self.adapter.get_relevant_memory("conv_123", "测试查询")
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_save_memory_success(self):
        """测试保存记忆成功"""
        mock_memory = Mock()
        mock_memory.save_memory = AsyncMock(return_value=True)
        
        with patch.object(self.adapter, 'memory', mock_memory):
            result = await self.adapter.save_memory("conv_123", "测试内容")
            
            assert result is True
            mock_memory.save_memory.assert_called_once_with("conv_123", "测试内容", None)
    
    @pytest.mark.asyncio
    async def test_save_memory_with_metadata(self):
        """测试保存记忆（带元数据）"""
        mock_memory = Mock()
        mock_memory.save_memory = AsyncMock(return_value=True)
        
        with patch.object(self.adapter, 'memory', mock_memory):
            metadata = {"type": "realtime_voice"}
            result = await self.adapter.save_memory("conv_123", "测试内容", metadata)
            
            assert result is True
            mock_memory.save_memory.assert_called_once_with("conv_123", "测试内容", metadata)
    
    @pytest.mark.asyncio
    async def test_save_memory_no_memory_system(self):
        """测试记忆系统未初始化"""
        with patch.object(self.adapter, 'memory', None):
            result = await self.adapter.save_memory("conv_123", "测试内容")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_save_memory_exception(self):
        """测试保存记忆异常"""
        mock_memory = Mock()
        mock_memory.save_memory = AsyncMock(side_effect=Exception("测试异常"))
        
        with patch.object(self.adapter, 'memory', mock_memory):
            result = await self.adapter.save_memory("conv_123", "测试内容")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_memory_stats_success(self):
        """测试获取记忆统计信息成功"""
        mock_memory = Mock()
        
        with patch.object(self.adapter, 'memory', mock_memory):
            result = await self.adapter.get_memory_stats("conv_123")
            
            assert isinstance(result, dict)
            assert "total_memories" in result
            assert "last_updated" in result
    
    @pytest.mark.asyncio
    async def test_get_memory_stats_no_memory_system(self):
        """测试记忆系统未初始化"""
        with patch.object(self.adapter, 'memory', None):
            result = await self.adapter.get_memory_stats("conv_123")
            
            assert result == {"total_memories": 0, "last_updated": None}
    
    def test_is_available_with_memory_system(self):
        """测试记忆系统可用"""
        with patch.object(self.adapter, 'memory', Mock()):
            assert self.adapter.is_available() is True
    
    def test_is_available_without_memory_system(self):
        """测试记忆系统不可用"""
        with patch.object(self.adapter, 'memory', None):
            assert self.adapter.is_available() is False
    
    @pytest.mark.asyncio
    async def test_memory_conversion(self):
        """测试记忆格式转换"""
        mock_memory = Mock()
        mock_memory.get_relevant_memory = AsyncMock(return_value=["记忆1", "记忆2"])
        
        with patch.object(self.adapter, 'memory', mock_memory):
            result = await self.adapter.get_relevant_memory("conv_123", "测试查询")
            
            # 验证返回的是字符串列表
            assert all(isinstance(memory, str) for memory in result)
    
    @pytest.mark.asyncio
    async def test_memory_conversion_single_memory(self):
        """测试单个记忆格式转换"""
        mock_memory = Mock()
        mock_memory.get_relevant_memory = AsyncMock(return_value="单个记忆")
        
        with patch.object(self.adapter, 'memory', mock_memory):
            result = await self.adapter.get_relevant_memory("conv_123", "测试查询")
            
            assert result == ["单个记忆"]
    
    @pytest.mark.asyncio
    async def test_memory_conversion_empty_memory(self):
        """测试空记忆格式转换"""
        mock_memory = Mock()
        mock_memory.get_relevant_memory = AsyncMock(return_value=None)
        
        with patch.object(self.adapter, 'memory', mock_memory):
            result = await self.adapter.get_relevant_memory("conv_123", "测试查询")
            
            assert result == []
