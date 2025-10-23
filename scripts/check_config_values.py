#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置值检查脚本
检查关键配置项的默认值是否正确
"""

import re

def check_key_configs():
    """检查关键配置项的默认值"""
    key_configs = {
        'OPENAI_MODEL': 'gpt-4.1',
        'OPENAI_BASE_URL': 'https://api.openai.com/v1',
        'OPENAI_TEMPERATURE': '0.75',
        'OPENAI_MAX_TOKENS': '16384',
        'SERVER_HOST': '0.0.0.0',
        'SERVER_PORT': '8000',
        'CHAT_ENGINE': 'chat_engine',
        'DEFAULT_PERSONALITY': 'health_assistant',
        'REALTIME_VOICE_ENABLED': 'true',
        'AUDIO_MAX_SIZE_MB': '25',
        'TEXT_MAX_LENGTH': '4096',
        'DEFAULT_WHISPER_MODEL': 'whisper-1',
        'DEFAULT_TTS_MODEL': 'tts-1',
        'DEFAULT_VOICE': 'shimmer',
        'DEFAULT_CHAT_MODEL': 'gpt-4o-mini',
        'CONNECTION_TIMEOUT': '30',
        'MAX_RETRY_ATTEMPTS': '3',
        'AUDIO_BUFFER_SIZE': '100',
        'AUDIO_PROCESSOR_MAX_WORKERS': '4',
        'WEBSOCKET_RECEIVE_TIMEOUT': '5.0',
        'WEBSOCKET_CONNECT_TIMEOUT': '10.0',
        'WEBSOCKET_CLOSE_TIMEOUT': '5.0',
        'WEBSOCKET_PING_TIMEOUT': '10.0',
        'MAX_CONNECTION_ATTEMPTS': '5',
        'REALTIME_CONNECTION_TIMEOUT': '30',
        'REALTIME_RECONNECT_ATTEMPTS': '3',
        'REALTIME_IDLE_TIMEOUT_MS': '30000',
        'REALTIME_VOICE_THRESHOLD': '0.2',
        'TEST_TIMEOUT': '30',
        'TEST_MAX_ATTEMPTS': '5',
        'DEBUG_MODE': 'false',
        'VERBOSE_LOGGING': 'false'
    }
    
    print("🔍 关键配置项默认值检查")
    print("=" * 50)
    
    with open('config/config.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    errors = []
    for config_name, expected_value in key_configs.items():
        # 查找配置项的定义
        pattern = rf'{config_name}\s*=\s*os\.getenv\("{config_name}",\s*"([^"]+)"'
        match = re.search(pattern, content)
        
        # 如果没找到，尝试查找其他格式
        if not match:
            pattern = rf'{config_name}\s*=\s*os\.getenv\("{config_name}",\s*([^)]+)\)'
            match = re.search(pattern, content)
        
        if match:
            actual_value = match.group(1)
            if actual_value != expected_value:
                errors.append(f"❌ {config_name}: 期望 '{expected_value}', 实际 '{actual_value}'")
            else:
                print(f"✅ {config_name}: {actual_value}")
        else:
            errors.append(f"❌ {config_name}: 未找到配置项")
    
    if errors:
        print(f"\n❌ 发现 {len(errors)} 个配置值错误:")
        for error in errors:
            print(f"  {error}")
        return 1
    else:
        print(f"\n✅ 所有关键配置项默认值正确！")
        return 0

if __name__ == "__main__":
    exit(check_key_configs())
