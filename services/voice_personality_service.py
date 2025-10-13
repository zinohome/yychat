"""
语音个性化服务
根据人格设置选择合适的语音类型
"""

from typing import Dict, Optional
from utils.log import log
from core.personality_manager import PersonalityManager


class VoicePersonalityService:
    """语音个性化服务"""
    
    def __init__(self):
        """初始化语音个性化服务"""
        self.personality_manager = PersonalityManager()
        self.voice_mapping = self._init_voice_mapping()
        log.info("语音个性化服务初始化成功")
    
    def _init_voice_mapping(self) -> Dict[str, str]:
        """
        初始化人格到语音的映射
        
        Returns:
            Dict[str, str]: 人格ID到语音类型的映射
        """
        return {
            "friendly": "nova",        # 年轻、活泼的声音
            "professional": "onyx",    # 深沉、权威的声音
            "health_assistant": "alloy", # 中性、平衡的声音
            "default": "alloy"         # 默认语音
        }
    
    def get_voice_for_personality(self, personality_id: Optional[str]) -> str:
        """
        根据人格获取语音类型
        
        Args:
            personality_id: 人格ID
            
        Returns:
            str: 语音类型
        """
        try:
            if not personality_id:
                return self.voice_mapping["default"]
            
            # 检查人格是否存在
            personalities = self.personality_manager.get_personalities()
            if personality_id not in personalities:
                log.warning(f"未知的人格ID: {personality_id}，使用默认语音")
                return self.voice_mapping["default"]
            
            # 获取对应的语音类型
            voice = self.voice_mapping.get(personality_id, self.voice_mapping["default"])
            log.debug(f"人格 {personality_id} 使用语音: {voice}")
            return voice
            
        except Exception as e:
            log.error(f"获取语音类型失败: {e}")
            return self.voice_mapping["default"]
    
    def get_voice_description(self, voice: str) -> str:
        """
        获取语音描述
        
        Args:
            voice: 语音类型
            
        Returns:
            str: 语音描述
        """
        descriptions = {
            "alloy": "中性、平衡的声音",
            "echo": "清晰、专业的声音",
            "fable": "温暖、友好的声音",
            "onyx": "深沉、权威的声音",
            "nova": "年轻、活泼的声音",
            "shimmer": "柔和、优雅的声音"
        }
        return descriptions.get(voice, "未知语音类型")
    
    def get_personality_voice_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        获取人格语音映射信息
        
        Returns:
            Dict[str, Dict[str, str]]: 人格语音映射信息
        """
        try:
            personalities = self.personality_manager.get_personalities()
            mapping = {}
            
            for personality_id in personalities:
                voice = self.get_voice_for_personality(personality_id)
                personality_info = personalities[personality_id]
                
                mapping[personality_id] = {
                    "name": personality_info.get("name", personality_id),
                    "description": personality_info.get("description", ""),
                    "voice": voice,
                    "voice_description": self.get_voice_description(voice)
                }
            
            return mapping
            
        except Exception as e:
            log.error(f"获取人格语音映射失败: {e}")
            return {}
    
    def set_voice_for_personality(self, personality_id: str, voice: str) -> bool:
        """
        为人格设置语音类型
        
        Args:
            personality_id: 人格ID
            voice: 语音类型
            
        Returns:
            bool: 设置是否成功
        """
        try:
            # 验证语音类型
            valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            if voice not in valid_voices:
                log.error(f"无效的语音类型: {voice}")
                return False
            
            # 验证人格ID
            personalities = self.personality_manager.get_all_personalities()
            if personality_id not in personalities:
                log.error(f"未知的人格ID: {personality_id}")
                return False
            
            # 更新映射
            self.voice_mapping[personality_id] = voice
            log.info(f"为人格 {personality_id} 设置语音: {voice}")
            return True
            
        except Exception as e:
            log.error(f"设置人格语音失败: {e}")
            return False
    
    def get_available_voices(self) -> Dict[str, str]:
        """
        获取所有可用的语音类型
        
        Returns:
            Dict[str, str]: 语音类型和描述
        """
        return {
            "alloy": "中性、平衡的声音",
            "echo": "清晰、专业的声音",
            "fable": "温暖、友好的声音",
            "onyx": "深沉、权威的声音",
            "nova": "年轻、活泼的声音",
            "shimmer": "柔和、优雅的声音"
        }
    
    def get_voice_recommendations(self) -> Dict[str, list]:
        """
        获取语音推荐
        
        Returns:
            Dict[str, list]: 不同场景的语音推荐
        """
        return {
            "商务场景": ["onyx", "echo"],
            "客服场景": ["alloy", "nova"],
            "教育场景": ["fable", "shimmer"],
            "娱乐场景": ["nova", "fable"],
            "医疗场景": ["alloy", "echo"]
        }


# 创建全局语音个性化服务实例
voice_personality_service = VoicePersonalityService()
