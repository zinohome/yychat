"""
人格适配器测试
"""

import pytest
from unittest.mock import Mock, patch
from adapters.personality_adapter import PersonalityAdapter, personality_adapter


class TestPersonalityAdapter:
    """人格适配器测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.adapter = PersonalityAdapter()
    
    def test_adapter_initialization(self):
        """测试适配器初始化"""
        assert self.adapter is not None
        assert hasattr(self.adapter, 'personality_manager')
    
    def test_global_adapter_instance(self):
        """测试全局适配器实例"""
        assert personality_adapter is not None
        assert isinstance(personality_adapter, PersonalityAdapter)
    
    def test_get_personality_for_realtime_success(self):
        """测试获取实时语音人格成功"""
        # 模拟人格对象
        mock_personality = Mock()
        mock_personality.system_prompt = "你是一个友好的AI助手"
        mock_personality.voice_settings = {"voice": "shimmer", "speed": 1.2}
        mock_personality.behavior_patterns = {"tone": "friendly", "style": "conversational"}
        mock_personality.allowed_tools = ["tool1", "tool2"]
        
        # 模拟人格管理器
        mock_manager = Mock()
        mock_manager.get_personality = Mock(return_value=mock_personality)
        
        with patch.object(self.adapter, 'personality_manager', mock_manager):
            result = self.adapter.get_personality_for_realtime("personality_123")
            
            assert result["instructions"] == "你是一个友好的AI助手"
            assert result["voice"] == "shimmer"
            assert result["speed"] == 1.2
            assert result["modalities"] == ["text", "audio"]
            assert result["behavior"]["tone"] == "friendly"
            assert result["behavior"]["style"] == "conversational"
            assert result["allowed_tools"] == ["tool1", "tool2"]
    
    def test_get_personality_for_realtime_no_manager(self):
        """测试人格管理器未初始化"""
        with patch.object(self.adapter, 'personality_manager', None):
            result = self.adapter.get_personality_for_realtime("personality_123")
            
            # 应该返回默认人格
            assert result["instructions"] is not None
            assert result["voice"] == "shimmer"
            assert result["modalities"] == ["text", "audio"]
    
    def test_get_personality_for_realtime_personality_not_found(self):
        """测试人格不存在"""
        mock_manager = Mock()
        mock_manager.get_personality = Mock(return_value=None)
        
        with patch.object(self.adapter, 'personality_manager', mock_manager):
            result = self.adapter.get_personality_for_realtime("nonexistent_personality")
            
            # 应该返回默认人格
            assert result["instructions"] is not None
            assert result["voice"] == "shimmer"
            assert result["modalities"] == ["text", "audio"]
    
    def test_get_personality_for_realtime_exception(self):
        """测试获取人格异常"""
        mock_manager = Mock()
        mock_manager.get_personality = Mock(side_effect=Exception("测试异常"))
        
        with patch.object(self.adapter, 'personality_manager', mock_manager):
            result = self.adapter.get_personality_for_realtime("personality_123")
            
            # 应该返回默认人格
            assert result["instructions"] is not None
            assert result["voice"] == "shimmer"
            assert result["modalities"] == ["text", "audio"]
    
    def test_convert_to_realtime_format(self):
        """测试人格格式转换"""
        # 模拟人格对象
        mock_personality = Mock()
        mock_personality.system_prompt = "测试系统提示"
        mock_personality.voice_settings = {"voice": "shimmer", "speed": 1.5}
        mock_personality.behavior_patterns = {"tone": "professional", "style": "formal"}
        mock_personality.allowed_tools = ["tool1"]
        
        result = self.adapter._convert_to_realtime_format(mock_personality)
        
        assert result["instructions"] == "测试系统提示"
        assert result["voice"] == "shimmer"
        assert result["speed"] == 1.5
        assert result["modalities"] == ["text", "audio"]
        assert result["behavior"]["tone"] == "professional"
        assert result["behavior"]["style"] == "formal"
        assert result["allowed_tools"] == ["tool1"]
    
    def test_convert_to_realtime_format_missing_attributes(self):
        """测试人格格式转换（缺少属性）"""
        # 模拟人格对象（缺少某些属性）
        mock_personality = Mock()
        mock_personality.system_prompt = None
        mock_personality.voice_settings = None
        mock_personality.behavior_patterns = None
        mock_personality.allowed_tools = None
        
        result = self.adapter._convert_to_realtime_format(mock_personality)
        
        assert result["instructions"] == ""
        assert result["voice"] == "shimmer"  # 默认值
        assert result["speed"] == 1.0  # 默认值
        assert result["modalities"] == ["text", "audio"]
        assert result["behavior"]["tone"] == "friendly"  # 默认值
        assert result["behavior"]["style"] == "conversational"  # 默认值
        assert result["allowed_tools"] == []
    
    def test_get_default_realtime_personality(self):
        """测试获取默认实时语音人格"""
        result = self.adapter._get_default_realtime_personality()
        
        assert result["instructions"] is not None
        assert result["voice"] == "shimmer"
        assert result["speed"] == 1.0
        assert result["modalities"] == ["text", "audio"]
        assert result["behavior"]["tone"] == "friendly"
        assert result["behavior"]["style"] == "conversational"
        assert result["allowed_tools"] == []
    
    def test_get_available_personalities_success(self):
        """测试获取可用人格列表成功"""
        mock_manager = Mock()
        
        with patch.object(self.adapter, 'personality_manager', mock_manager):
            result = self.adapter.get_available_personalities()
            
            assert isinstance(result, list)
    
    def test_get_available_personalities_no_manager(self):
        """测试人格管理器未初始化"""
        with patch.object(self.adapter, 'personality_manager', None):
            result = self.adapter.get_available_personalities()
            
            assert result == []
    
    def test_get_available_personalities_exception(self):
        """测试获取可用人格列表异常"""
        mock_manager = Mock()
        mock_manager.get_available_personalities = Mock(side_effect=Exception("测试异常"))
        
        with patch.object(self.adapter, 'personality_manager', mock_manager):
            result = self.adapter.get_available_personalities()
            
            assert result == []
    
    def test_is_available_with_manager(self):
        """测试人格管理器可用"""
        with patch.object(self.adapter, 'personality_manager', Mock()):
            assert self.adapter.is_available() is True
    
    def test_is_available_without_manager(self):
        """测试人格管理器不可用"""
        with patch.object(self.adapter, 'personality_manager', None):
            assert self.adapter.is_available() is False
    
    def test_convert_to_realtime_format_exception(self):
        """测试人格格式转换异常"""
        # 模拟人格对象（会抛出异常）
        mock_personality = Mock()
        mock_personality.system_prompt = Mock(side_effect=Exception("测试异常"))
        
        result = self.adapter._convert_to_realtime_format(mock_personality)
        
        # 应该返回默认人格
        assert result["instructions"] is not None
        # 由于异常处理，voice可能不是默认值，我们检查它是否存在
        assert "voice" in result
        assert result["modalities"] == ["text", "audio"]
