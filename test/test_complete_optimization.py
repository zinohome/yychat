#!/usr/bin/env python3
"""
测试完整优化效果
验证所有重复初始化问题是否已解决
"""

import sys
import os
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_complete_optimization():
    """测试完整优化效果"""
    print("🧪 测试完整优化效果...")
    
    # 清空输出缓冲区
    import io
    from contextlib import redirect_stdout
    
    output_buffer = io.StringIO()
    
    with redirect_stdout(output_buffer):
        # 导入所有可能触发初始化的模块
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
    
    # 统计各种初始化信息的出现次数
    env_load_count = output.count("成功加载.env文件")
    memory_init_count = output.count("使用本地模式初始化Memory")
    memory_success_count = output.count("成功创建本地Memory实例")
    engine_init_count = output.count("EngineManager初始化完成")
    audio_init_count = output.count("音频服务初始化成功")
    voice_init_count = output.count("语音个性化服务初始化成功")
    
    print(f"📊 统计结果:")
    print(f"  .env文件加载次数: {env_load_count}")
    print(f"  Memory初始化次数: {memory_init_count}")
    print(f"  Memory成功创建次数: {memory_success_count}")
    print(f"  EngineManager初始化次数: {engine_init_count}")
    print(f"  音频服务初始化次数: {audio_init_count}")
    print(f"  语音服务初始化次数: {voice_init_count}")
    
    # 检查是否都只有1次（Memory初始化应该是0，因为延迟初始化）
    all_single = all([
        env_load_count == 1,
        memory_init_count == 0,  # 延迟初始化，导入时不应该初始化
        memory_success_count == 0,  # 延迟初始化，导入时不应该初始化
        engine_init_count == 1,
        audio_init_count == 1,
        voice_init_count == 1
    ])
    
    if all_single:
        print("✅ 所有组件初始化正常，优化成功")
        print("  - .env文件只加载一次")
        print("  - Memory延迟初始化，导入时不初始化")
        print("  - 其他组件只初始化一次")
        return True
    else:
        print("❌ 仍有组件重复初始化，需要进一步优化")
        return False

def test_import_performance():
    """测试导入性能"""
    print("\n🧪 测试导入性能...")
    
    start_time = time.time()
    
    try:
        # 导入所有模块
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
        
        end_time = time.time()
        import_time = end_time - start_time
        
        print(f"⏱️ 导入耗时: {import_time:.2f}秒")
        
        if import_time < 8:
            print("✅ 导入时间正常，没有重复初始化问题")
            return True
        else:
            print("⚠️ 导入时间较长，可能仍有重复初始化")
            return False
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 完整优化测试")
    print("=" * 50)
    
    # 测试完整优化
    optimization_success = test_complete_optimization()
    
    # 测试导入性能
    performance_success = test_import_performance()
    
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"完整优化测试: {'✅ 通过' if optimization_success else '❌ 失败'}")
    print(f"导入性能测试: {'✅ 通过' if performance_success else '❌ 失败'}")
    
    if optimization_success and performance_success:
        print("\n🎉 所有测试通过！完整优化成功！")
        print("✅ 所有重复初始化问题已解决")
        print("✅ 导入性能正常")
        print("✅ 延迟初始化正常工作")
        return True
    else:
        print("\n❌ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 测试被中断")
        sys.exit(1)
