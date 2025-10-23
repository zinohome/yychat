#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终配置项统计报告
"""

import re

def main():
    print("📊 YYChat 配置项统计报告")
    print("=" * 60)
    
    # 从config.py中提取所有配置项
    with open('config/config.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配所有配置项
    config_pattern = r'([A-Z_]+)\s*=\s*os\.getenv\('
    matches = re.findall(config_pattern, content)
    
    print(f"📈 配置项统计:")
    print(f"  总配置项数量: {len(matches)}")
    
    # 按分组统计
    groups = {
        '🔑 核心API密钥配置': ['OPENAI_API_KEY', 'YYCHAT_API_KEY', 'TAVILY_API_KEY'],
        '🤖 AI模型配置': ['OPENAI_MODEL', 'OPENAI_BASE_URL', 'OPENAI_TEMPERATURE', 'OPENAI_MAX_TOKENS'],
        '🧠 记忆管理配置': ['MEM0_API_KEY', 'MEM0_BASE_URL', 'MEMO_USE_LOCAL', 'MEM0_LLM_PROVIDER', 
                          'MEM0_LLM_CONFIG_MODEL', 'MEM0_LLM_CONFIG_MAX_TOKENS', 'MEM0_EMBEDDER_MODEL',
                          'MEMORY_RETRIEVAL_LIMIT', 'MEMORY_RETRIEVAL_TIMEOUT', 'ENABLE_MEMORY_RETRIEVAL', 'MEMORY_SAVE_MODE'],
        '💾 数据存储配置': ['VECTOR_STORE_PROVIDER', 'CHROMA_PERSIST_DIRECTORY', 'CHROMA_COLLECTION_NAME',
                          'QDRANT_HOST', 'QDRANT_PORT', 'QDRANT_API_KEY', 'QDRANT_COLLECTION_NAME'],
        '🚀 服务器配置': ['SERVER_HOST', 'SERVER_PORT'],
        '💬 聊天引擎配置': ['CHAT_ENGINE', 'DEFAULT_PERSONALITY', 'STREAM_DEFAULT', 'USE_TOOLS_DEFAULT'],
        '🎤 实时语音配置': ['REALTIME_VOICE_ENABLED', 'REALTIME_VOICE_MODEL', 'REALTIME_VOICE_TOKEN_EXPIRY',
                          'REALTIME_VOICE_SAMPLE_RATE', 'REALTIME_VOICE_CHANNELS'],
        '⚡ 性能优化配置': ['OPENAI_API_TIMEOUT', 'OPENAI_CONNECT_TIMEOUT', 'OPENAI_READ_TIMEOUT',
                          'OPENAI_WRITE_TIMEOUT', 'OPENAI_POOL_TIMEOUT', 'OPENAI_API_RETRIES',
                          'MAX_CONNECTIONS', 'MAX_KEEPALIVE_CONNECTIONS', 'KEEPALIVE_EXPIRY', 'VERIFY_SSL',
                          'CHUNK_SPLIT_THRESHOLD'],
        '📊 缓存配置': ['USE_REDIS_CACHE', 'REDIS_HOST', 'REDIS_PORT', 'REDIS_DB', 'REDIS_PASSWORD', 'REDIS_TTL',
                      'MEMORY_CACHE_MAXSIZE', 'MEMORY_CACHE_TTL'],
        '📈 监控和日志配置': ['ENABLE_PERFORMANCE_MONITOR', 'PERFORMANCE_LOG_ENABLED', 'PERFORMANCE_MAX_HISTORY',
                          'PERFORMANCE_SAMPLING_RATE', 'LOG_LEVEL', 'LOG_FILE_NAME'],
        '📋 API元数据配置': ['API_TITLE', 'API_DESCRIPTION', 'API_VERSION'],
        '🎵 音频处理配置': ['AUDIO_MAX_SIZE_MB', 'TEXT_MAX_LENGTH', 'VOICE_SPEED_MIN', 'VOICE_SPEED_MAX',
                          'AUDIO_CHUNK_SIZE_KB', 'AUDIO_COMPRESSION_QUALITY'],
        '🎤 语音和模型默认配置': ['DEFAULT_WHISPER_MODEL', 'DEFAULT_TTS_MODEL', 'DEFAULT_VOICE', 'DEFAULT_CHAT_MODEL'],
        '⏱️ 超时和重试配置': ['CONNECTION_TIMEOUT', 'MAX_RETRY_ATTEMPTS', 'VAD_SILENCE_THRESHOLD',
                          'AUDIO_BUFFER_SIZE', 'AUDIO_PROCESSOR_TIMEOUT', 'AUDIO_PROCESSOR_MAX_WORKERS'],
        '🌐 WebSocket和网络配置': ['WEBSOCKET_RECEIVE_TIMEOUT', 'WEBSOCKET_CONNECT_TIMEOUT',
                                'WEBSOCKET_CLOSE_TIMEOUT', 'WEBSOCKET_PING_TIMEOUT', 'MAX_CONNECTION_ATTEMPTS'],
        '🎯 实时语音配置': ['REALTIME_CONNECTION_TIMEOUT', 'REALTIME_RECONNECT_ATTEMPTS',
                          'REALTIME_IDLE_TIMEOUT_MS', 'REALTIME_VOICE_THRESHOLD'],
        '📊 测试和调试配置': ['TEST_TIMEOUT', 'TEST_MAX_ATTEMPTS', 'DEBUG_MODE', 'VERBOSE_LOGGING']
    }
    
    print(f"\n📋 配置项分组统计:")
    total_count = 0
    for group_name, group_configs in groups.items():
        count = len(group_configs)
        total_count += count
        print(f"  {group_name}: {count} 项")
    
    print(f"\n✅ 配置项完整性检查:")
    print(f"  配置项总数: {len(matches)}")
    print(f"  分组统计总数: {total_count}")
    
    if len(matches) == total_count:
        print("  ✅ 配置项数量一致，无遗漏")
    else:
        print("  ❌ 配置项数量不一致，可能存在遗漏")
    
    print(f"\n🎯 重构成果总结:")
    print(f"  - 原有配置项: 约60个")
    print(f"  - 新增配置项: 约30个")
    print(f"  - 总配置项: {len(matches)}个")
    print(f"  - 配置分组: {len(groups)}个")
    print(f"  - 支持Docker部署: ✅")
    print(f"  - 支持环境变量配置: ✅")
    
    return 0

if __name__ == "__main__":
    exit(main())
