#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单配置检查脚本
"""

def main():
    print("🔍 配置项完整性检查")
    print("=" * 50)
    
    # 检查关键配置项是否存在
    key_configs = [
        'OPENAI_API_KEY', 'YYCHAT_API_KEY', 'TAVILY_API_KEY',
        'OPENAI_MODEL', 'OPENAI_BASE_URL', 'OPENAI_TEMPERATURE', 'OPENAI_MAX_TOKENS',
        'MEM0_API_KEY', 'MEM0_BASE_URL', 'MEMORY_RETRIEVAL_LIMIT', 'MEMORY_RETRIEVAL_TIMEOUT',
        'VECTOR_STORE_PROVIDER', 'CHROMA_PERSIST_DIRECTORY', 'CHROMA_COLLECTION_NAME',
        'SERVER_HOST', 'SERVER_PORT',
        'CHAT_ENGINE', 'DEFAULT_PERSONALITY', 'STREAM_DEFAULT', 'USE_TOOLS_DEFAULT',
        'REALTIME_VOICE_ENABLED', 'REALTIME_VOICE_MODEL', 'REALTIME_VOICE_TOKEN_EXPIRY',
        'AUDIO_MAX_SIZE_MB', 'TEXT_MAX_LENGTH', 'VOICE_SPEED_MIN', 'VOICE_SPEED_MAX',
        'DEFAULT_WHISPER_MODEL', 'DEFAULT_TTS_MODEL', 'DEFAULT_VOICE', 'DEFAULT_CHAT_MODEL',
        'CONNECTION_TIMEOUT', 'MAX_RETRY_ATTEMPTS', 'VAD_SILENCE_THRESHOLD',
        'AUDIO_BUFFER_SIZE', 'AUDIO_PROCESSOR_TIMEOUT', 'AUDIO_PROCESSOR_MAX_WORKERS',
        'WEBSOCKET_RECEIVE_TIMEOUT', 'WEBSOCKET_CONNECT_TIMEOUT', 'WEBSOCKET_CLOSE_TIMEOUT',
        'WEBSOCKET_PING_TIMEOUT', 'MAX_CONNECTION_ATTEMPTS',
        'REALTIME_CONNECTION_TIMEOUT', 'REALTIME_RECONNECT_ATTEMPTS',
        'REALTIME_IDLE_TIMEOUT_MS', 'REALTIME_VOICE_THRESHOLD',
        'TEST_TIMEOUT', 'TEST_MAX_ATTEMPTS', 'DEBUG_MODE', 'VERBOSE_LOGGING'
    ]
    
    with open('config/config.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    missing = []
    for config in key_configs:
        if f'{config} = os.getenv(' not in content:
            missing.append(config)
    
    if missing:
        print(f"❌ 发现 {len(missing)} 个缺失的配置项:")
        for item in missing:
            print(f"  - {item}")
        return 1
    else:
        print(f"✅ 所有 {len(key_configs)} 个关键配置项都存在！")
        return 0

if __name__ == "__main__":
    exit(main())
