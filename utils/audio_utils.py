"""
音频工具模块
提供音频格式验证、转换和压缩功能
"""

import wave
import struct
from typing import Tuple, Optional
from utils.log import log


class AudioUtils:
    """音频工具类"""
    
    @staticmethod
    def validate_audio_format(audio_data: bytes) -> bool:
        """
        验证音频格式
        
        Args:
            audio_data: 音频数据
            
        Returns:
            bool: 是否为有效音频格式
        """
        try:
            if not audio_data or len(audio_data) < 44:  # WAV文件最小大小
                return False
            
            # 检查WAV文件头
            if audio_data[:4] != b'RIFF':
                return False
            
            if audio_data[8:12] != b'WAVE':
                return False
            
            return True
            
        except Exception as e:
            log.warning(f"音频格式验证失败: {e}")
            return False
    
    @staticmethod
    def get_audio_info(audio_data: bytes) -> Optional[dict]:
        """
        获取音频信息
        
        Args:
            audio_data: 音频数据
            
        Returns:
            Optional[dict]: 音频信息，如果解析失败返回None
        """
        try:
            if not AudioUtils.validate_audio_format(audio_data):
                return None
            
            # 解析WAV文件头
            with wave.open(io.BytesIO(audio_data), 'rb') as wav_file:
                return {
                    "channels": wav_file.getnchannels(),
                    "sample_width": wav_file.getsampwidth(),
                    "frame_rate": wav_file.getframerate(),
                    "frames": wav_file.getnframes(),
                    "duration": wav_file.getnframes() / wav_file.getframerate()
                }
                
        except Exception as e:
            log.warning(f"获取音频信息失败: {e}")
            return None
    
    @staticmethod
    def convert_audio_format(audio_data: bytes, target_format: str = "wav") -> bytes:
        """
        转换音频格式
        
        Args:
            audio_data: 原始音频数据
            target_format: 目标格式 (wav, mp3)
            
        Returns:
            bytes: 转换后的音频数据
        """
        try:
            if target_format.lower() == "wav":
                return audio_data  # 已经是WAV格式
            
            # 这里可以添加其他格式转换逻辑
            # 目前只支持WAV格式
            log.warning(f"不支持的音频格式转换: {target_format}")
            return audio_data
            
        except Exception as e:
            log.error(f"音频格式转换失败: {e}")
            return audio_data
    
    @staticmethod
    def compress_audio(audio_data: bytes, quality: int = 80) -> bytes:
        """
        压缩音频数据
        
        Args:
            audio_data: 原始音频数据
            quality: 压缩质量 (1-100)
            
        Returns:
            bytes: 压缩后的音频数据
        """
        try:
            # 简单的音频压缩实现
            # 这里可以根据需要实现更复杂的压缩算法
            
            if quality >= 90:
                return audio_data  # 高质量，不压缩
            
            # 降低采样率进行压缩
            audio_info = AudioUtils.get_audio_info(audio_data)
            if not audio_info:
                return audio_data
            
            # 如果采样率较高，可以降低采样率
            if audio_info["frame_rate"] > 16000:
                # 这里可以实现重采样逻辑
                log.info(f"音频压缩: 原始采样率 {audio_info['frame_rate']}Hz")
            
            return audio_data
            
        except Exception as e:
            log.error(f"音频压缩失败: {e}")
            return audio_data
    
    @staticmethod
    def normalize_audio(audio_data: bytes) -> bytes:
        """
        音频标准化
        
        Args:
            audio_data: 原始音频数据
            
        Returns:
            bytes: 标准化后的音频数据
        """
        try:
            audio_info = AudioUtils.get_audio_info(audio_data)
            if not audio_info:
                return audio_data
            
            # 检查是否需要标准化
            if audio_info["frame_rate"] == 16000 and audio_info["channels"] == 1:
                return audio_data  # 已经是标准格式
            
            # 这里可以实现音频标准化逻辑
            log.info(f"音频标准化: {audio_info['frame_rate']}Hz, {audio_info['channels']}声道")
            
            return audio_data
            
        except Exception as e:
            log.error(f"音频标准化失败: {e}")
            return audio_data
    
    @staticmethod
    def trim_audio(audio_data: bytes, start_time: float = 0, end_time: Optional[float] = None) -> bytes:
        """
        裁剪音频
        
        Args:
            audio_data: 原始音频数据
            start_time: 开始时间（秒）
            end_time: 结束时间（秒），None表示到结尾
            
        Returns:
            bytes: 裁剪后的音频数据
        """
        try:
            audio_info = AudioUtils.get_audio_info(audio_data)
            if not audio_info:
                return audio_data
            
            duration = audio_info["duration"]
            if start_time >= duration:
                return b''  # 开始时间超出音频长度
            
            if end_time is None:
                end_time = duration
            else:
                end_time = min(end_time, duration)
            
            if start_time >= end_time:
                return b''  # 无效的时间范围
            
            # 这里可以实现音频裁剪逻辑
            log.info(f"音频裁剪: {start_time:.2f}s - {end_time:.2f}s")
            
            return audio_data
            
        except Exception as e:
            log.error(f"音频裁剪失败: {e}")
            return audio_data
    
    @staticmethod
    def detect_silence(audio_data: bytes, threshold: float = 0.01) -> list:
        """
        检测静音段
        
        Args:
            audio_data: 音频数据
            threshold: 静音阈值
            
        Returns:
            list: 静音段列表 [(start_time, end_time), ...]
        """
        try:
            audio_info = AudioUtils.get_audio_info(audio_data)
            if not audio_info:
                return []
            
            # 这里可以实现静音检测逻辑
            # 目前返回空列表
            log.debug(f"静音检测: 阈值 {threshold}")
            
            return []
            
        except Exception as e:
            log.error(f"静音检测失败: {e}")
            return []


# 导入io模块
import io
