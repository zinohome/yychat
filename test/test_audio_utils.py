#!/usr/bin/env python3
"""
音频工具测试脚本
测试音频预处理功能
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.audio_utils import AudioUtils


class TestAudioUtils(unittest.TestCase):
    """音频工具测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建测试用的WAV文件头
        self.wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
        self.wav_data = self.wav_header + b'\x00' * 1000  # 添加一些音频数据
        
        # 创建测试用的MP3文件头
        self.mp3_header = b'\xff\xfb\x90\x00'
        self.mp3_data = self.mp3_header + b'\x00' * 1000
    
    def test_validate_audio_format_wav(self):
        """测试WAV格式验证"""
        result = AudioUtils.validate_audio_format(self.wav_data)
        self.assertTrue(result, "WAV格式验证应该通过")
    
    def test_validate_audio_format_invalid(self):
        """测试无效格式验证"""
        invalid_data = b'invalid audio data'
        result = AudioUtils.validate_audio_format(invalid_data)
        self.assertFalse(result, "无效格式验证应该失败")
    
    def test_validate_audio_format_empty(self):
        """测试空数据验证"""
        result = AudioUtils.validate_audio_format(b'')
        self.assertFalse(result, "空数据验证应该失败")
    
    def test_get_audio_info_wav(self):
        """测试获取WAV音频信息"""
        info = AudioUtils.get_audio_info(self.wav_data)
        if info:  # 如果pydub可用
            self.assertIn('channels', info)
            self.assertIn('frame_rate', info)
            self.assertIn('sample_width', info)
            self.assertIn('duration', info)
    
    def test_get_audio_info_invalid(self):
        """测试获取无效音频信息"""
        info = AudioUtils.get_audio_info(b'invalid data')
        self.assertIsNone(info, "无效音频应该返回None")
    
    def test_detect_audio_format_wav(self):
        """测试检测WAV格式"""
        format_type = AudioUtils._detect_audio_format(self.wav_data)
        self.assertEqual(format_type, "wav", "应该检测为WAV格式")
    
    def test_detect_audio_format_mp3(self):
        """测试检测MP3格式"""
        format_type = AudioUtils._detect_audio_format(self.mp3_data)
        self.assertEqual(format_type, "mp3", "应该检测为MP3格式")
    
    def test_detect_audio_format_unknown(self):
        """测试检测未知格式"""
        unknown_data = b'unknown format data'
        format_type = AudioUtils._detect_audio_format(unknown_data)
        self.assertIsNone(format_type, "未知格式应该返回None")
    
    @patch('utils.audio_utils.PYDUB_AVAILABLE', True)
    @patch('utils.audio_utils.AudioSegment')
    def test_convert_audio_format_with_pydub(self, mock_audio_segment):
        """测试使用pydub进行格式转换"""
        # 模拟AudioSegment
        mock_segment = MagicMock()
        mock_segment.set_frame_rate.return_value = mock_segment
        mock_segment.set_channels.return_value = mock_segment
        mock_segment.set_sample_width.return_value = mock_segment
        mock_audio_segment.from_file.return_value = mock_segment
        
        # 模拟export方法
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b'converted audio data'
        
        with patch('io.BytesIO') as mock_bytesio:
            mock_bytesio.return_value.__enter__.return_value = mock_buffer
            
            result = AudioUtils.convert_audio_format(self.wav_data, "mp3")
            
            # 验证调用
            mock_audio_segment.from_file.assert_called_once()
            mock_segment.set_frame_rate.assert_called_with(16000)
            mock_segment.set_channels.assert_called_with(1)
            mock_segment.set_sample_width.assert_called_with(2)
            mock_segment.export.assert_called_once()
            
            self.assertEqual(result, b'converted audio data')
    
    @patch('utils.audio_utils.PYDUB_AVAILABLE', False)
    def test_convert_audio_format_without_pydub(self):
        """测试没有pydub时的格式转换"""
        result = AudioUtils.convert_audio_format(self.wav_data, "mp3")
        self.assertEqual(result, self.wav_data, "没有pydub时应该返回原始数据")
    
    def test_convert_audio_format_empty_data(self):
        """测试空数据的格式转换"""
        with self.assertRaises(ValueError):
            AudioUtils.convert_audio_format(b'', "wav")
    
    @patch('utils.audio_utils.PYDUB_AVAILABLE', True)
    @patch('utils.audio_utils.AudioSegment')
    def test_compress_audio_with_pydub(self, mock_audio_segment):
        """测试使用pydub进行音频压缩"""
        # 模拟AudioSegment
        mock_segment = MagicMock()
        mock_segment.set_frame_rate.return_value = mock_segment
        mock_segment.set_channels.return_value = mock_segment
        mock_segment.set_sample_width.return_value = mock_segment
        mock_audio_segment.from_file.return_value = mock_segment
        
        # 模拟export方法
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b'compressed audio data'
        
        with patch('io.BytesIO') as mock_bytesio:
            mock_bytesio.return_value.__enter__.return_value = mock_buffer
            
            result = AudioUtils.compress_audio(self.wav_data, quality=70)
            
            # 验证调用
            mock_audio_segment.from_file.assert_called_once()
            mock_segment.set_frame_rate.assert_called_with(16000)
            mock_segment.set_channels.assert_called_with(1)
            mock_segment.set_sample_width.assert_called_with(2)
            mock_segment.export.assert_called_once()
            
            self.assertEqual(result, b'compressed audio data')
    
    @patch('utils.audio_utils.PYDUB_AVAILABLE', True)
    @patch('utils.audio_utils.AudioSegment')
    def test_normalize_audio_with_pydub(self, mock_audio_segment):
        """测试使用pydub进行音频标准化"""
        # 模拟AudioSegment
        mock_segment = MagicMock()
        mock_segment.frame_rate = 44100
        mock_segment.channels = 2
        mock_segment.sample_width = 4
        mock_segment.set_frame_rate.return_value = mock_segment
        mock_segment.set_channels.return_value = mock_segment
        mock_segment.set_sample_width.return_value = mock_segment
        mock_segment.normalize.return_value = mock_segment
        mock_audio_segment.from_file.return_value = mock_segment
        
        # 模拟export方法
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b'normalized audio data'
        
        with patch('io.BytesIO') as mock_bytesio:
            mock_bytesio.return_value.__enter__.return_value = mock_buffer
            
            result = AudioUtils.normalize_audio(self.wav_data)
            
            # 验证调用
            mock_audio_segment.from_file.assert_called_once()
            mock_segment.set_frame_rate.assert_called_with(16000)
            mock_segment.set_channels.assert_called_with(1)
            mock_segment.set_sample_width.assert_called_with(2)
            mock_segment.normalize.assert_called_once()
            mock_segment.export.assert_called_once()
            
            self.assertEqual(result, b'normalized audio data')
    
    def test_compress_audio_empty_data(self):
        """测试空数据的音频压缩"""
        with self.assertRaises(ValueError):
            AudioUtils.compress_audio(b'', quality=80)
    
    def test_normalize_audio_empty_data(self):
        """测试空数据的音频标准化"""
        with self.assertRaises(ValueError):
            AudioUtils.normalize_audio(b'')


class TestVoicePersonalityService(unittest.TestCase):
    """语音个性化服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        from services.voice_personality_service import VoicePersonalityService
        self.service = VoicePersonalityService()
    
    def test_get_voice_for_personality_friendly(self):
        """测试获取友好人格的语音"""
        voice = self.service.get_voice_for_personality("friendly")
        self.assertEqual(voice, "shimmer", "友好人格应该使用shimmer语音")
    
    def test_get_voice_for_personality_professional(self):
        """测试获取专业人格的语音"""
        voice = self.service.get_voice_for_personality("professional")
        self.assertEqual(voice, "shimmer", "专业人格应该使用shimmer语音")
    
    def test_get_voice_for_personality_health_assistant(self):
        """测试获取健康助手人格的语音"""
        voice = self.service.get_voice_for_personality("health_assistant")
        self.assertEqual(voice, "shimmer", "健康助手人格应该使用shimmer语音")
    
    def test_get_voice_for_personality_unknown(self):
        """测试获取未知人格的语音"""
        voice = self.service.get_voice_for_personality("unknown_personality")
        self.assertEqual(voice, "shimmer", "未知人格应该使用默认语音")
    
    def test_get_voice_for_personality_none(self):
        """测试获取None人格的语音"""
        voice = self.service.get_voice_for_personality(None)
        self.assertEqual(voice, "shimmer", "None人格应该使用默认语音")
    
    def test_get_available_voices(self):
        """测试获取可用语音列表"""
        voices = self.service.get_available_voices()
        self.assertIsInstance(voices, dict, "应该返回字典")
        self.assertIn("shimmer", voices, "应该包含shimmer语音")
        self.assertIn("alloy", voices, "应该包含alloy语音")
        self.assertIn("nova", voices, "应该包含nova语音")
        self.assertIn("onyx", voices, "应该包含onyx语音")
    
    @patch('services.voice_personality_service.PersonalityManager')
    def test_set_voice_for_personality_success(self, mock_personality_manager):
        """测试成功设置人格语音"""
        # 模拟PersonalityManager
        mock_manager = MagicMock()
        mock_manager.get_all_personalities.return_value = {"friendly": {}, "professional": {}}
        mock_personality_manager.return_value = mock_manager
        
        # 创建新的服务实例
        from services.voice_personality_service import VoicePersonalityService
        service = VoicePersonalityService()
        service.personality_manager = mock_manager
        
        # 测试设置语音
        result = service.set_voice_for_personality("friendly", "shimmer")
        self.assertTrue(result, "设置语音应该成功")
    
    def test_set_voice_for_personality_invalid_voice(self):
        """测试设置无效语音"""
        result = self.service.set_voice_for_personality("friendly", "invalid_voice")
        self.assertFalse(result, "设置无效语音应该失败")
    
    def test_set_voice_for_personality_invalid_personality(self):
        """测试设置无效人格的语音"""
        result = self.service.set_voice_for_personality("invalid_personality", "shimmer")
        self.assertFalse(result, "设置无效人格的语音应该失败")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
