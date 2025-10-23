"""
音频服务模块
提供语音转文本(STT)和文本转语音(TTS)功能
"""

import base64
import io
import time
from typing import Optional, Dict, Any
from openai import OpenAI
from utils.log import log
from config.config import get_config
from utils.audio_utils import AudioUtils

config = get_config()


class AudioService:
    """音频服务类"""
    
    def __init__(self):
        """初始化音频服务"""
        try:
            self.openai_client = OpenAI(
                api_key=config.OPENAI_API_KEY,
                base_url=config.OPENAI_BASE_URL
            )
            # 延迟初始化AudioCache，避免循环引用
            self.audio_cache = None
            log.info("音频服务初始化成功")
        except Exception as e:
            log.error(f"音频服务初始化失败: {e}")
            raise
    
    async def transcribe_audio(self, audio_data: bytes, model: str = "whisper-1") -> str:
        """
        语音转文本
        
        Args:
            audio_data: 音频数据
            model: 使用的模型，默认whisper-1
            
        Returns:
            str: 转录的文本
        """
        try:
            # 验证音频数据
            if not audio_data or len(audio_data) == 0:
                raise ValueError("音频数据不能为空")
            
            # 检查音频大小限制 (25MB for OpenAI)
            max_size = 25 * 1024 * 1024  # 25MB
            if len(audio_data) > max_size:
                # 尝试压缩音频
                log.info(f"音频文件过大 ({len(audio_data) / (1024*1024):.1f}MB)，尝试压缩")
                audio_data = AudioUtils.compress_audio(audio_data, quality=70)
                
                # 再次检查大小
                if len(audio_data) > max_size:
                    raise ValueError(f"音频文件过大，最大支持 {max_size / (1024*1024):.1f}MB")
            
            # 音频预处理
            log.info("开始音频预处理...")
            
            # 1. 标准化音频格式
            audio_data = AudioUtils.normalize_audio(audio_data)
            
            # 2. 转换为WAV格式 (Whisper推荐)
            audio_data = AudioUtils.convert_audio_format(audio_data, "wav")
            
            log.info("音频预处理完成")
            
            # 创建音频文件对象
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"
            
            # 调用OpenAI Whisper API
            start_time = time.time()
            response = self.openai_client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="text"
            )
            processing_time = time.time() - start_time
            
            # 获取转录结果
            if isinstance(response, str):
                transcribed_text = response.strip()
            else:
                transcribed_text = response.text.strip()
            
            log.info(f"语音转文本完成，耗时: {processing_time:.2f}s，文本长度: {len(transcribed_text)}")
            return transcribed_text
            
        except Exception as e:
            log.error(f"语音转文本失败: {e}")
            # 提供更友好的错误信息
            if "Invalid file format" in str(e):
                raise Exception(f"不支持的音频格式。支持的格式: flac, m4a, mp3, mp4, mpeg, mpga, oga, ogg, wav, webm")
            elif "Error code: 400" in str(e):
                raise Exception(f"音频文件格式错误: {e}")
            else:
                raise Exception(f"语音转文本处理失败: {e}")
    
    async def synthesize_speech(self, text: str, voice: str = "shimmer", 
                              model: str = "tts-1", speed: float = 1.0) -> bytes:
        """
        文本转语音
        
        Args:
            text: 要转换的文本
            voice: 语音类型 (alloy, echo, fable, onyx, nova, shimmer)
            model: 使用的模型 (tts-1, tts-1-hd)
            speed: 语速 (0.25-4.0)
            
        Returns:
            bytes: 音频数据
        """
        try:
            # 验证输入参数
            if not text or not text.strip():
                raise ValueError("文本内容不能为空")
            
            if len(text) > 4096:  # OpenAI TTS限制
                raise ValueError("文本长度不能超过4096个字符")
            
            if speed < 0.25 or speed > 4.0:
                raise ValueError("语速必须在0.25-4.0之间")
            
            # 检查缓存
            if self.audio_cache is None:
                self.audio_cache = AudioCache()
            cache_key = f"{text}_{voice}_{model}_{speed}"
            cached_audio = await self.audio_cache.get(cache_key)
            if cached_audio:
                log.debug(f"使用缓存的TTS结果: {cache_key}")
                return cached_audio
            
            # 调用OpenAI TTS API
            start_time = time.time()
            response = self.openai_client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed
            )
            processing_time = time.time() - start_time
            
            # 获取音频数据
            audio_data = response.content
            
            # 缓存结果
            if self.audio_cache is None:
                self.audio_cache = AudioCache()
            await self.audio_cache.set(cache_key, audio_data)
            
            log.info(f"文本转语音完成，耗时: {processing_time:.2f}s，音频大小: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            log.error(f"文本转语音失败: {e}")
            raise

    async def synthesize_speech_stream(self, text: str, voice: str = "shimmer",
                                       model: str = "tts-1", speed: float = 1.0,
                                       chunk_size: int = 32 * 1024):
        """
        文本转语音（分片流式）
        说明：当前SDK未提供真正的流式TTS输出，此实现先整体合成再按字节切片，
        以满足前端按分片播放与带宽平滑的需求；后续如SDK支持流式接口，可在此处替换为真正的流式生成。

        Yields:
            bytes: 音频数据分片
        """
        # 直接复用参数校验逻辑
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")
        if len(text) > 4096:
            raise ValueError("文本长度不能超过4096个字符")
        if speed < 0.25 or speed > 4.0:
            raise ValueError("语速必须在0.25-4.0之间")

        try:
            # 先整体合成
            audio_bytes = await self.synthesize_speech(text=text, voice=voice, model=model, speed=speed)
            total_len = len(audio_bytes)
            if total_len == 0:
                log.warning("synthesize_speech_stream: 生成的音频长度为0")
                return

            # 切片输出
            offset = 0
            while offset < total_len:
                end = min(offset + chunk_size, total_len)
                yield audio_bytes[offset:end]
                offset = end
        except Exception as e:
            log.error(f"文本转语音(流式)失败: {e}")
            raise

    def text_to_speech(self, text: str, voice: str = "shimmer", 
                        model: str = "tts-1", speed: float = 1.0) -> bytes:
        """
        同步封装：文本转语音（返回原始音频bytes）
        与 OpenAI 官方 TTS 指南保持一致，便于在非异步环境复用。
        """
        # 参数校验与缓存逻辑与异步实现保持一致（此处走直连不使用异步缓存）
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")
        if len(text) > 4096:
            raise ValueError("文本长度不能超过4096个字符")
        if speed < 0.25 or speed > 4.0:
            raise ValueError("语速必须在0.25-4.0之间")

        try:
            start_time = time.time()
            response = self.openai_client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed
            )
            processing_time = time.time() - start_time
            audio_data = response.content
            log.info(f"文本转语音(同步)完成，耗时: {processing_time:.2f}s，音频大小: {len(audio_data)} bytes")
            return audio_data
        except Exception as e:
            log.error(f"文本转语音(同步)失败: {e}")
            raise

    async def text_to_speech_async(self, text: str, voice: str = "shimmer", 
                                   model: str = "tts-1", speed: float = 1.0) -> bytes:
        """
        异步封装：调用内部 synthesize_speech，返回原始音频bytes。
        """
        return await self.synthesize_speech(text=text, voice=voice, model=model, speed=speed)
    
    async def transcribe_audio_base64(self, audio_base64: str, model: str = "whisper-1") -> str:
        """
        从Base64编码的音频数据转文本
        
        Args:
            audio_base64: Base64编码的音频数据
            model: 使用的模型
            
        Returns:
            str: 转录的文本
        """
        try:
            # 解码Base64数据
            audio_data = base64.b64decode(audio_base64)
            return await self.transcribe_audio(audio_data, model)
        except Exception as e:
            log.error(f"Base64音频转文本失败: {e}")
            raise
    
    async def synthesize_speech_base64(self, text: str, voice: str = "shimmer", 
                                     model: str = "tts-1", speed: float = 1.0) -> str:
        """
        文本转语音并返回Base64编码
        
        Args:
            text: 要转换的文本
            voice: 语音类型
            model: 使用的模型
            speed: 语速
            
        Returns:
            str: Base64编码的音频数据
        """
        try:
            audio_data = await self.synthesize_speech(text, voice, model, speed)
            return base64.b64encode(audio_data).decode('utf-8')
        except Exception as e:
            log.error(f"文本转Base64音频失败: {e}")
            raise
    
    def get_available_voices(self) -> Dict[str, str]:
        """
        获取可用的语音类型
        
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
    
    def get_available_models(self) -> Dict[str, str]:
        """
        获取可用的模型
        
        Returns:
            Dict[str, str]: 模型和描述
        """
        return {
            "whisper-1": "语音转文本模型",
            "tts-1": "文本转语音模型（标准）",
            "tts-1-hd": "文本转语音模型（高清）"
        }


class AudioCache:
    """音频缓存类"""
    
    def __init__(self, max_size: int = 100):
        """
        初始化音频缓存
        
        Args:
            max_size: 最大缓存条目数
        """
        self.cache: Dict[str, bytes] = {}
        self.max_size = max_size
        self.access_times: Dict[str, float] = {}
    
    async def get(self, key: str) -> Optional[bytes]:
        """
        获取缓存的音频数据
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[bytes]: 音频数据，如果不存在返回None
        """
        if key in self.cache:
            self.access_times[key] = time.time()
            log.debug(f"音频缓存命中: {key}")
            return self.cache[key]
        return None
    
    async def set(self, key: str, audio_data: bytes):
        """
        设置缓存音频数据
        
        Args:
            key: 缓存键
            audio_data: 音频数据
        """
        # 如果缓存已满，删除最旧的条目
        if len(self.cache) >= self.max_size:
            await self._evict_oldest()
        
        self.cache[key] = audio_data
        self.access_times[key] = time.time()
        log.debug(f"音频缓存设置: {key}, 大小: {len(audio_data)} bytes")
    
    async def _evict_oldest(self):
        """删除最旧的缓存条目"""
        if not self.access_times:
            return
        
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]
        log.debug(f"删除最旧缓存条目: {oldest_key}")
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()
        log.info("音频缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_size = sum(len(data) for data in self.cache.values())
        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "total_bytes": total_size,
            "total_mb": round(total_size / (1024 * 1024), 2)
        }


# 创建全局音频服务实例
audio_service = AudioService()
