import re
from typing import List

class TTSSegmenter:
    """TTS智能分块器"""
    
    def __init__(self):
        # 中文标点符号
        self.chinese_punctuation = r'[。！？，、；：]'
        # 英文标点符号
        self.english_punctuation = r'[.!?,;:]'
        # 所有标点符号
        self.all_punctuation = r'[。！？，、；：.!?,;:]'
        # 强制分块阈值
        self.force_split_threshold = 100
    
    def segment_text(self, text: str) -> List[str]:
        """
        按标点符号智能分块文本
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 分块后的文本列表
        """
        if not text or not text.strip():
            return []
        
        # 按标点符号分割
        segments = re.split(f'({self.all_punctuation})', text)
        
        # 重新组合，保留标点符号
        result = []
        current_segment = ""
        
        for i, part in enumerate(segments):
            if not part.strip():
                continue
                
            current_segment += part
            
            # 如果包含标点符号，或者到达末尾
            if re.search(self.all_punctuation, part) or i == len(segments) - 1:
                if current_segment.strip():
                    result.append(current_segment.strip())
                    current_segment = ""
        
        return result
    
    def should_trigger_tts(self, text: str) -> bool:
        """
        判断是否应该触发TTS
        
        Args:
            text: 当前文本
            
        Returns:
            bool: 是否应该触发TTS
        """
        # 检查是否包含标点符号
        return bool(re.search(self.all_punctuation, text))
    
    def should_force_split(self, text: str) -> bool:
        """
        判断是否应该强制分块（无标点符号但达到长度阈值）
        
        Args:
            text: 当前文本
            
        Returns:
            bool: 是否应该强制分块
        """
        return len(text) >= self.force_split_threshold and not bool(re.search(self.all_punctuation, text))
    
    def segment_with_force_split(self, text: str) -> List[str]:
        """
        智能分块，包含强制分块逻辑
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 分块后的文本列表
        """
        if not text or not text.strip():
            return []
        
        # 先按标点符号分块
        segments = self.segment_text(text)
        
        # 检查是否需要强制分块
        result = []
        for segment in segments:
            if len(segment) >= self.force_split_threshold and not re.search(self.all_punctuation, segment):
                # 强制分块：按长度切分
                for i in range(0, len(segment), self.force_split_threshold):
                    chunk = segment[i:i + self.force_split_threshold]
                    if chunk.strip():
                        result.append(chunk.strip())
            else:
                result.append(segment)
        
        return result
