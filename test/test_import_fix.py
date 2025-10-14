#!/usr/bin/env python3
"""
测试导入修复
验证所有必要的函数都能正确导入
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_imports():
    """测试所有必要的导入"""
    print("🧪 测试导入修复...")
    
    try:
        # 测试消息处理器导入
        from handlers.text_message_handler import handle_text_message
        print("✅ handle_text_message 导入成功")
        
        # 测试消息路由器函数导入
        from core.message_router import (
            handle_heartbeat, 
            handle_ping, 
            handle_get_status, 
            handle_audio_input, 
            handle_audio_stream, 
            handle_voice_command, 
            handle_status_query
        )
        print("✅ 所有消息路由器函数导入成功")
        
        # 测试其他必要导入
        from core.engine_manager import get_engine_manager
        print("✅ get_engine_manager 导入成功")
        
        from services.audio_service import AudioService
        print("✅ AudioService 导入成功")
        
        from services.voice_personality_service import VoicePersonalityService
        print("✅ VoicePersonalityService 导入成功")
        
        print("\n🎉 所有导入测试通过！")
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
