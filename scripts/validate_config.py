#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证脚本
检查所有配置项是否正确设置
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config import get_config
from utils.log import log


def validate_required_configs():
    """验证必需的配置项"""
    config = get_config()
    errors = []
    warnings = []
    
    print("🔍 验证必需配置项...")
    
    # 检查API密钥
    if not config.OPENAI_API_KEY:
        errors.append("❌ OPENAI_API_KEY 未设置")
    else:
        print("✅ OPENAI_API_KEY 已设置")
    
    if not config.YYCHAT_API_KEY:
        warnings.append("⚠️  YYCHAT_API_KEY 使用默认值，建议设置自定义密钥")
    else:
        print("✅ YYCHAT_API_KEY 已设置")
    
    return errors, warnings


def validate_audio_configs():
    """验证音频相关配置"""
    config = get_config()
    errors = []
    warnings = []
    
    print("\n🎵 验证音频配置...")
    
    # 检查音频大小限制
    if config.AUDIO_MAX_SIZE_MB <= 0:
        errors.append("❌ AUDIO_MAX_SIZE_MB 必须大于0")
    elif config.AUDIO_MAX_SIZE_MB > 100:
        warnings.append("⚠️  AUDIO_MAX_SIZE_MB 设置过大，可能影响性能")
    else:
        print(f"✅ 音频大小限制: {config.AUDIO_MAX_SIZE_MB}MB")
    
    # 检查文本长度限制
    if config.TEXT_MAX_LENGTH <= 0:
        errors.append("❌ TEXT_MAX_LENGTH 必须大于0")
    else:
        print(f"✅ 文本长度限制: {config.TEXT_MAX_LENGTH}字符")
    
    # 检查语速范围
    if config.VOICE_SPEED_MIN >= config.VOICE_SPEED_MAX:
        errors.append("❌ VOICE_SPEED_MIN 必须小于 VOICE_SPEED_MAX")
    else:
        print(f"✅ 语速范围: {config.VOICE_SPEED_MIN}-{config.VOICE_SPEED_MAX}")
    
    # 检查音频压缩质量
    if not (1 <= config.AUDIO_COMPRESSION_QUALITY <= 100):
        errors.append("❌ AUDIO_COMPRESSION_QUALITY 必须在1-100之间")
    else:
        print(f"✅ 音频压缩质量: {config.AUDIO_COMPRESSION_QUALITY}")
    
    return errors, warnings


def validate_model_configs():
    """验证模型配置"""
    config = get_config()
    errors = []
    warnings = []
    
    print("\n🤖 验证模型配置...")
    
    # 检查默认模型
    valid_whisper_models = ["whisper-1"]
    if config.DEFAULT_WHISPER_MODEL not in valid_whisper_models:
        warnings.append(f"⚠️  DEFAULT_WHISPER_MODEL 可能不是有效模型: {config.DEFAULT_WHISPER_MODEL}")
    else:
        print(f"✅ 默认Whisper模型: {config.DEFAULT_WHISPER_MODEL}")
    
    valid_tts_models = ["tts-1", "tts-1-hd"]
    if config.DEFAULT_TTS_MODEL not in valid_tts_models:
        warnings.append(f"⚠️  DEFAULT_TTS_MODEL 可能不是有效模型: {config.DEFAULT_TTS_MODEL}")
    else:
        print(f"✅ 默认TTS模型: {config.DEFAULT_TTS_MODEL}")
    
    valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    if config.DEFAULT_VOICE not in valid_voices:
        warnings.append(f"⚠️  DEFAULT_VOICE 可能不是有效语音: {config.DEFAULT_VOICE}")
    else:
        print(f"✅ 默认语音: {config.DEFAULT_VOICE}")
    
    return errors, warnings


def validate_timeout_configs():
    """验证超时配置"""
    config = get_config()
    errors = []
    warnings = []
    
    print("\n⏱️  验证超时配置...")
    
    # 检查连接超时
    if config.CONNECTION_TIMEOUT <= 0:
        errors.append("❌ CONNECTION_TIMEOUT 必须大于0")
    elif config.CONNECTION_TIMEOUT < 10:
        warnings.append("⚠️  CONNECTION_TIMEOUT 设置过短，可能导致连接失败")
    else:
        print(f"✅ 连接超时: {config.CONNECTION_TIMEOUT}秒")
    
    # 检查重试次数
    if config.MAX_RETRY_ATTEMPTS <= 0:
        errors.append("❌ MAX_RETRY_ATTEMPTS 必须大于0")
    elif config.MAX_RETRY_ATTEMPTS > 10:
        warnings.append("⚠️  MAX_RETRY_ATTEMPTS 设置过多，可能影响性能")
    else:
        print(f"✅ 最大重试次数: {config.MAX_RETRY_ATTEMPTS}")
    
    # 检查WebSocket超时
    if config.WEBSOCKET_RECEIVE_TIMEOUT <= 0:
        errors.append("❌ WEBSOCKET_RECEIVE_TIMEOUT 必须大于0")
    else:
        print(f"✅ WebSocket接收超时: {config.WEBSOCKET_RECEIVE_TIMEOUT}秒")
    
    return errors, warnings


def validate_performance_configs():
    """验证性能配置"""
    config = get_config()
    errors = []
    warnings = []
    
    print("\n⚡ 验证性能配置...")
    
    # 检查音频处理器配置
    if config.AUDIO_PROCESSOR_MAX_WORKERS <= 0:
        errors.append("❌ AUDIO_PROCESSOR_MAX_WORKERS 必须大于0")
    elif config.AUDIO_PROCESSOR_MAX_WORKERS > 16:
        warnings.append("⚠️  AUDIO_PROCESSOR_MAX_WORKERS 设置过多，可能影响性能")
    else:
        print(f"✅ 音频处理器工作线程数: {config.AUDIO_PROCESSOR_MAX_WORKERS}")
    
    # 检查音频缓冲区大小
    if config.AUDIO_BUFFER_SIZE <= 0:
        errors.append("❌ AUDIO_BUFFER_SIZE 必须大于0")
    else:
        print(f"✅ 音频缓冲区大小: {config.AUDIO_BUFFER_SIZE}")
    
    # 检查内存缓存配置
    if config.MEMORY_CACHE_MAXSIZE <= 0:
        errors.append("❌ MEMORY_CACHE_MAXSIZE 必须大于0")
    else:
        print(f"✅ 内存缓存最大条目数: {config.MEMORY_CACHE_MAXSIZE}")
    
    return errors, warnings


def validate_network_configs():
    """验证网络配置"""
    config = get_config()
    errors = []
    warnings = []
    
    print("\n🌐 验证网络配置...")
    
    # 检查服务器配置
    if not config.SERVER_HOST:
        errors.append("❌ SERVER_HOST 不能为空")
    else:
        print(f"✅ 服务器地址: {config.SERVER_HOST}")
    
    if not (1 <= config.SERVER_PORT <= 65535):
        errors.append("❌ SERVER_PORT 必须在1-65535之间")
    else:
        print(f"✅ 服务器端口: {config.SERVER_PORT}")
    
    # 检查Redis配置（如果启用）
    if config.USE_REDIS_CACHE:
        if not config.REDIS_HOST:
            errors.append("❌ 启用Redis缓存但REDIS_HOST未设置")
        else:
            print(f"✅ Redis主机: {config.REDIS_HOST}:{config.REDIS_PORT}")
    
    return errors, warnings


def main():
    """主函数"""
    print("🔧 YYChat 配置验证工具")
    print("=" * 50)
    
    all_errors = []
    all_warnings = []
    
    # 验证各个配置类别
    errors, warnings = validate_required_configs()
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    
    errors, warnings = validate_audio_configs()
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    
    errors, warnings = validate_model_configs()
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    
    errors, warnings = validate_timeout_configs()
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    
    errors, warnings = validate_performance_configs()
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    
    errors, warnings = validate_network_configs()
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    
    # 输出结果
    print("\n" + "=" * 50)
    print("📊 验证结果")
    print("=" * 50)
    
    if all_errors:
        print(f"\n❌ 发现 {len(all_errors)} 个错误:")
        for error in all_errors:
            print(f"  {error}")
    
    if all_warnings:
        print(f"\n⚠️  发现 {len(all_warnings)} 个警告:")
        for warning in all_warnings:
            print(f"  {warning}")
    
    if not all_errors and not all_warnings:
        print("\n✅ 所有配置验证通过！")
        return 0
    elif not all_errors:
        print(f"\n✅ 配置基本正确，但有 {len(all_warnings)} 个建议优化项")
        return 0
    else:
        print(f"\n❌ 配置验证失败，发现 {len(all_errors)} 个错误")
        return 1


if __name__ == "__main__":
    sys.exit(main())
