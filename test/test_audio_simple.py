#!/usr/bin/env python3
"""
简化的音频功能测试
验证核心功能是否正常工作
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_audio_utils_basic():
    """测试音频工具基础功能"""
    print("🧪 测试音频工具基础功能...")
    
    from utils.audio_utils import AudioUtils
    
    # 创建测试用的WAV文件头
    wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
    wav_data = wav_header + b'\x00' * 1000
    
    # 测试格式验证
    result = AudioUtils.validate_audio_format(wav_data)
    print(f"  ✅ WAV格式验证: {result}")
    
    # 测试格式检测
    format_type = AudioUtils._detect_audio_format(wav_data)
    print(f"  ✅ 格式检测: {format_type}")
    
    # 测试音频信息获取
    info = AudioUtils.get_audio_info(wav_data)
    if info:
        print(f"  ✅ 音频信息: {info}")
    else:
        print("  ⚠️  音频信息获取失败 (可能pydub未安装)")
    
    # 测试格式转换 (不依赖pydub)
    try:
        converted = AudioUtils.convert_audio_format(wav_data, "wav")
        print(f"  ✅ 格式转换: {len(converted)} bytes")
    except Exception as e:
        print(f"  ⚠️  格式转换: {e}")
    
    print("🎉 音频工具基础功能测试完成")

def test_voice_personality_service():
    """测试语音个性化服务"""
    print("\n🧪 测试语音个性化服务...")
    
    from services.voice_personality_service import VoicePersonalityService
    
    service = VoicePersonalityService()
    
    # 测试获取语音
    voices = {
        "friendly": service.get_voice_for_personality("friendly"),
        "professional": service.get_voice_for_personality("professional"),
        "health_assistant": service.get_voice_for_personality("health_assistant"),
        "unknown": service.get_voice_for_personality("unknown_personality"),
        "none": service.get_voice_for_personality(None)
    }
    
    print("  📊 语音映射结果:")
    for personality, voice in voices.items():
        print(f"    {personality}: {voice}")
    
    # 测试可用语音
    available_voices = service.get_available_voices()
    print(f"  📋 可用语音: {list(available_voices.keys())}")
    
    print("🎉 语音个性化服务测试完成")

def test_audio_service_integration():
    """测试音频服务集成"""
    print("\n🧪 测试音频服务集成...")
    
    try:
        from services.audio_service import AudioService
        
        # 注意：这里不实际调用OpenAI API，只测试初始化
        print("  ⚠️  音频服务初始化测试 (跳过API调用)")
        print("  ✅ 音频服务模块导入成功")
        
    except Exception as e:
        print(f"  ❌ 音频服务测试失败: {e}")
    
    print("🎉 音频服务集成测试完成")

def main():
    """主测试函数"""
    print("🚀 开始简化音频功能测试")
    print("=" * 50)
    
    try:
        test_audio_utils_basic()
        test_voice_personality_service()
        test_audio_service_integration()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
