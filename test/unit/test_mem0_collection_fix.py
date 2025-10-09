"""
Mem0Proxy collection错误修复测试
测试collection检查和创建逻辑
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.mem0_proxy import Mem0ChatEngine


class TestMem0CollectionFix:
    def test_ensure_collection_exists_success(self):
        """测试collection已存在的情况"""
        engine = Mem0ChatEngine()
        
        # Mock Mem0客户端
        mock_client = MagicMock()
        mock_client.search.return_value = []  # 搜索成功，返回空结果
        
        with patch.object(engine.mem0_client, 'get_client', return_value=mock_client):
            # 应该不抛出异常
            engine._ensure_collection_exists()
            mock_client.search.assert_called_once_with("test", user_id="__collection_test__")

    def test_ensure_collection_exists_creates_collection(self):
        """测试collection不存在时自动创建"""
        engine = Mem0ChatEngine()
        
        # Mock Mem0客户端
        mock_client = MagicMock()
        # 第一次搜索抛出collection不存在的异常
        mock_client.search.side_effect = Exception("Collection does not exists")
        
        with patch.object(engine.mem0_client, 'get_client', return_value=mock_client):
            # 应该不抛出异常，而是创建collection
            engine._ensure_collection_exists()
            
            # 验证调用了add和delete
            mock_client.add.assert_called_once_with("test", user_id="__collection_test__")
            mock_client.delete.assert_called_once_with("test", user_id="__collection_test__")

    def test_ensure_collection_exists_other_error(self):
        """测试其他类型的错误会重新抛出"""
        engine = Mem0ChatEngine()
        
        # Mock Mem0客户端
        mock_client = MagicMock()
        # 抛出其他类型的异常
        mock_client.search.side_effect = Exception("Network error")
        
        with patch.object(engine.mem0_client, 'get_client', return_value=mock_client):
            # 应该抛出异常
            with pytest.raises(Exception, match="Network error"):
                engine._ensure_collection_exists()

    def test_ensure_collection_exists_no_client(self):
        """测试Mem0客户端未初始化的情况"""
        engine = Mem0ChatEngine()
        
        with patch.object(engine.mem0_client, 'get_client', return_value=None):
            # 应该不抛出异常，只是记录警告
            engine._ensure_collection_exists()

    def test_ensure_collection_exists_delete_fails(self):
        """测试删除测试记忆失败的情况"""
        engine = Mem0ChatEngine()
        
        # Mock Mem0客户端
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("Collection does not exists")
        mock_client.delete.side_effect = Exception("Delete failed")
        
        with patch.object(engine.mem0_client, 'get_client', return_value=mock_client):
            # 应该不抛出异常，只是记录警告
            engine._ensure_collection_exists()
            
            # 验证调用了add和delete
            mock_client.add.assert_called_once_with("test", user_id="__collection_test__")
            mock_client.delete.assert_called_once_with("test", user_id="__collection_test__")
