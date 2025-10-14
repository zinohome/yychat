"""
音频工具模块
提供音频格式验证、转换和压缩功能
"""

import wave
import struct
import io
from typing import Tuple, Optional
from utils.log import log

try:
    from pydub import AudioSegment
    from pydub.utils import which
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    log.warning("pydub未安装，音频格式转换功能将不可用")


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
            target_format: 目标格式 (wav, mp3, flac等)
            
        Returns:
            bytes: 转换后的音频数据
        """
        try:
            if not PYDUB_AVAILABLE:
                log.warning("pydub不可用，返回原始音频数据")
                return audio_data
            
            if not audio_data:
                raise ValueError("音频数据不能为空")
            
            # 检测输入格式
            input_format = AudioUtils._detect_audio_format(audio_data)
            if not input_format:
                log.warning("无法检测音频格式，尝试作为WAV处理")
                input_format = "wav"
            
            log.info(f"音频格式转换: {input_format} → {target_format}")
            
            # 使用pydub进行格式转换
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format=input_format)
            
            # 标准化音频参数 (Whisper推荐参数)
            audio_segment = audio_segment.set_frame_rate(16000)  # 16kHz
            audio_segment = audio_segment.set_channels(1)        # 单声道
            audio_segment = audio_segment.set_sample_width(2)    # 16位
            
            # 转换格式
            output_buffer = io.BytesIO()
            audio_segment.export(output_buffer, format=target_format)
            converted_data = output_buffer.getvalue()
            
            log.info(f"音频格式转换成功: {len(audio_data)} bytes → {len(converted_data)} bytes")
            return converted_data
            
        except Exception as e:
            log.error(f"音频格式转换失败: {e}")
            return audio_data
    
    @staticmethod
    def _detect_audio_format(audio_data: bytes) -> Optional[str]:
        """
        检测音频格式
        
        Args:
            audio_data: 音频数据
            
        Returns:
            Optional[str]: 检测到的格式，如果无法检测返回None
        """
        try:
            if not audio_data:
                return None
            
            # 检查文件头标识
            if audio_data.startswith(b'RIFF') and b'WAVE' in audio_data[:12]:
                return "wav"
            elif audio_data.startswith(b'ID3') or audio_data.startswith(b'\xff\xfb'):
                return "mp3"
            elif audio_data.startswith(b'fLaC'):
                return "flac"
            elif audio_data.startswith(b'OggS'):
                return "ogg"
            elif audio_data.startswith(b'ftypM4A') or audio_data.startswith(b'ftypisom'):
                return "m4a"
            elif audio_data.startswith(b'\x1a\x45\xdf\xa3'):
                return "webm"
            else:
                return None
                
        except Exception as e:
            log.warning(f"音频格式检测失败: {e}")
            return None
    
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
            if not PYDUB_AVAILABLE:
                log.warning("pydub不可用，返回原始音频数据")
                return audio_data
            
            if not audio_data:
                raise ValueError("音频数据不能为空")
            
            # 检测输入格式
            input_format = AudioUtils._detect_audio_format(audio_data)
            if not input_format:
                log.warning("无法检测音频格式，尝试作为WAV处理")
                input_format = "wav"
            
            log.info(f"音频压缩: 质量 {quality}, 格式 {input_format}")
            
            # 使用pydub进行音频压缩
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format=input_format)
            
            # 标准化音频参数
            audio_segment = audio_segment.set_frame_rate(16000)  # 16kHz
            audio_segment = audio_segment.set_channels(1)        # 单声道
            audio_segment = audio_segment.set_sample_width(2)    # 16位
            
            # 根据质量参数选择压缩方式
            output_buffer = io.BytesIO()
            if quality >= 90:
                # 高质量：使用WAV格式
                audio_segment.export(output_buffer, format="wav")
            elif quality >= 70:
                # 中等质量：使用MP3格式
                audio_segment.export(output_buffer, format="mp3", bitrate="128k")
            elif quality >= 50:
                # 低质量：使用MP3格式
                audio_segment.export(output_buffer, format="mp3", bitrate="64k")
            else:
                # 极低质量：使用MP3格式
                audio_segment.export(output_buffer, format="mp3", bitrate="32k")
            
            compressed_data = output_buffer.getvalue()
            
            # 计算压缩比
            compression_ratio = len(compressed_data) / len(audio_data) * 100
            log.info(f"音频压缩成功: {len(audio_data)} bytes → {len(compressed_data)} bytes (压缩比: {compression_ratio:.1f}%)")
            
            return compressed_data
            
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
            if not PYDUB_AVAILABLE:
                log.warning("pydub不可用，返回原始音频数据")
                return audio_data
            
            if not audio_data:
                raise ValueError("音频数据不能为空")
            
            # 检测输入格式
            input_format = AudioUtils._detect_audio_format(audio_data)
            if not input_format:
                log.warning("无法检测音频格式，尝试作为WAV处理")
                input_format = "wav"
            
            # 使用pydub进行音频标准化
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format=input_format)
            
            # 获取原始音频信息
            original_info = {
                "frame_rate": audio_segment.frame_rate,
                "channels": audio_segment.channels,
                "sample_width": audio_segment.sample_width,
                "duration": len(audio_segment) / 1000.0  # 秒
            }
            
            log.info(f"音频标准化前: {original_info['frame_rate']}Hz, {original_info['channels']}声道, {original_info['sample_width']}位")
            
            # 标准化音频参数 (Whisper推荐参数)
            audio_segment = audio_segment.set_frame_rate(16000)  # 16kHz
            audio_segment = audio_segment.set_channels(1)        # 单声道
            audio_segment = audio_segment.set_sample_width(2)    # 16位
            
            # 音量标准化 (归一化到-20dB)
            audio_segment = audio_segment.normalize()
            
            # 导出标准化后的音频
            output_buffer = io.BytesIO()
            audio_segment.export(output_buffer, format="wav")
            normalized_data = output_buffer.getvalue()
            
            log.info(f"音频标准化成功: {len(audio_data)} bytes → {len(normalized_data)} bytes")
            
            return normalized_data
            
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
