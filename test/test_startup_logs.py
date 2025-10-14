#!/usr/bin/env python3
"""
测试启动日志
验证启动过程中是否有重复的Memory初始化
"""

import sys
import os
import io
from contextlib import redirect_stdout

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_startup_logs():
    """测试启动日志"""
    print("🧪 测试启动日志...")
    
    output_buffer = io.StringIO()
    
    with redirect_stdout(output_buffer):
        # 模拟启动过程
        import config
        from config.config import get_config
        from core.engine_manager import get_engine_manager
        from core.chat_engine import ChatEngine
        from core.mem0_proxy import get_mem0_proxy
        from services.audio_service import AudioService
        from services.voice_personality_service import VoicePersonalityService
        from services.mcp.manager import get_mcp_manager
        from services.mcp.discovery import discover_and_register_mcp_tools
        from core.message_router import message_router
        from handlers.text_message_handler import TextMessageHandler
        from core.realtime_handler import RealtimeMessageHandler
    
    output = output_buffer.getvalue()
    
    # 统计各种初始化信息
    env_load_count = output.count("成功加载.env文件")
    memory_init_count = output.count("使用本地模式初始化Memory")
    memory_success_count = output.count("成功创建本地Memory实例")
    async_memory_count = output.count("使用本地模式初始化AsyncMemory")
    engine_init_count = output.count("EngineManager初始化完成")
    audio_init_count = output.count("音频服务初始化成功")
    voice_init_count = output.count("语音个性化服务初始化成功")
    
    print(f"📊 启动日志统计:")
    print(f"  .env文件加载次数: {env_load_count}")
    print(f"  Memory初始化次数: {memory_init_count}")
    print(f"  Memory成功创建次数: {memory_success_count}")
    print(f"  AsyncMemory初始化次数: {async_memory_count}")
    print(f"  EngineManager初始化次数: {engine_init_count}")
    print(f"  音频服务初始化次数: {audio_init_count}")
    print(f"  语音服务初始化次数: {voice_init_count}")
    
    # 检查是否有重复
    has_duplicates = any([
        env_load_count > 1,
        memory_init_count > 1,
        memory_success_count > 1,
        async_memory_count > 1,
        engine_init_count > 1,
        audio_init_count > 1,
        voice_init_count > 1
    ])
    
    if has_duplicates:
        print("❌ 发现重复初始化")
        return False
    else:
        print("✅ 没有重复初始化")
        return True

def main():
    """主测试函数"""
    print("🚀 启动日志测试")
    print("=" * 50)
    
    result = test_startup_logs()
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 启动日志正常，没有重复初始化")
    else:
        print("❌ 启动日志异常，存在重复初始化")
    
    return result

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 测试被中断")
        sys.exit(1)
