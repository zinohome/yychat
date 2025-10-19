"""
人格化系统适配器
复用现有人格系统，为实时语音提供人格化功能
"""

from typing import Dict, Any, Optional, List
from utils.log import log


class PersonalityAdapter:
    """人格化系统适配器"""
    
    def __init__(self):
        """初始化人格适配器"""
        try:
            from core.personality_manager import PersonalityManager
            self.personality_manager = PersonalityManager()
            log.info("人格适配器初始化成功")
        except Exception as e:
            log.error(f"人格适配器初始化失败: {e}")
            self.personality_manager = None
    
    def get_personality_for_realtime(self, personality_id: str) -> Dict[str, Any]:
        """
        获取实时语音专用人格配置
        
        Args:
            personality_id: 人格ID
            
        Returns:
            Dict[str, Any]: 实时语音人格配置
        """
        try:
            if not self.personality_manager:
                log.warning("人格系统未初始化，返回默认人格")
                return self._get_default_realtime_personality()
            
            # 复用现有人格系统
            personality = self.personality_manager.get_personality(personality_id)
            
            if not personality:
                log.warning(f"人格 {personality_id} 不存在，返回默认人格")
                return self._get_default_realtime_personality()
            
            # 转换为实时语音专用格式
            realtime_personality = self._convert_to_realtime_format(personality)
            
            log.debug(f"人格适配器获取人格成功: {personality_id}")
            return realtime_personality
            
        except Exception as e:
            log.error(f"获取人格失败: {e}")
            return self._get_default_realtime_personality()
    
    def _convert_to_realtime_format(self, personality) -> Dict[str, Any]:
        """
        转换为人格化格式
        
        Args:
            personality: 人格对象
            
        Returns:
            Dict[str, Any]: 实时语音格式的人格配置
        """
        try:
            # 获取系统提示
            instructions = getattr(personality, 'system_prompt', '') or ''
            
            # 获取语音设置
            voice_settings = getattr(personality, 'voice_settings', {}) or {}
            voice = voice_settings.get('voice', 'alloy')
            speed = voice_settings.get('speed', 1.0)
            
            # 获取行为模式
            behavior_patterns = getattr(personality, 'behavior_patterns', {}) or {}
            tone = behavior_patterns.get('tone', 'friendly')
            style = behavior_patterns.get('style', 'conversational')
            
            # 获取允许的工具
            allowed_tools = getattr(personality, 'allowed_tools', []) or []
            
            return {
                "instructions": instructions,
                "voice": voice,
                "speed": speed,
                "modalities": ["text", "audio"],
                "behavior": {
                    "tone": tone,
                    "style": style
                },
                "allowed_tools": allowed_tools
            }
            
        except Exception as e:
            log.error(f"转换人格格式失败: {e}")
            return self._get_default_realtime_personality()
    
    def _get_default_realtime_personality(self) -> Dict[str, Any]:
        """
        获取默认实时语音人格
        
        Returns:
            Dict[str, Any]: 默认人格配置
        """
        return {
            "instructions": "你是一个友好的AI助手，可以进行实时语音对话。请保持自然、友好的语调，并尽可能简洁地回答问题。",
            "voice": "alloy",
            "speed": 1.0,
            "modalities": ["text", "audio"],
            "behavior": {
                "tone": "friendly",
                "style": "conversational"
            },
            "allowed_tools": []
        }
    
    def get_available_personalities(self) -> List[Dict[str, Any]]:
        """
        获取可用的人格列表
        
        Returns:
            List[Dict[str, Any]]: 可用人格列表
        """
        try:
            if not self.personality_manager:
                return []
            
            # 这里可以添加获取所有可用人格的逻辑
            # 暂时返回空列表，后续可以扩展
            return []
            
        except Exception as e:
            log.error(f"获取可用人格列表失败: {e}")
            return []
    
    def is_available(self) -> bool:
        """
        检查人格系统是否可用
        
        Returns:
            bool: 是否可用
        """
        return self.personality_manager is not None


# 全局人格适配器实例
personality_adapter = PersonalityAdapter()
