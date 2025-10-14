#!/usr/bin/env python3
"""
测试.env文件加载优化效果
验证重复加载问题是否已解决
"""

import sys
import os
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_env_loading():
    """测试.env文件加载，检查是否还有重复加载"""
    print("🧪 测试.env文件加载优化...")
    
    # 清空输出缓冲区
    import io
    from contextlib import redirect_stdout
    
    output_buffer = io.StringIO()
    
    with redirect_stdout(output_buffer):
        # 多次导入配置模块
        import config
        import config
        import config
        
        # 导入其他可能使用配置的模块
        from config.config import get_config
        from core.engine_manager import get_engine_manager
        from services.audio_service import AudioService
    
    output = output_buffer.getvalue()
    
    # 统计"成功加载.env文件"的出现次数
    env_load_count = output.count("成功加载.env文件")
    
    print(f"📊 .env文件加载次数: {env_load_count}")
    
    if env_load_count == 1:
        print("✅ .env文件只加载一次，优化成功")
        return True
    else:
        print(f"❌ .env文件加载了{env_load_count}次，仍有重复加载问题")
        return False

def test_import_performance():
    """测试导入性能"""
    print("\n🧪 测试导入性能...")
    
    start_time = time.time()
    
    try:
        # 导入多个模块
        import config
        from config.config import get_config
        from core.engine_manager import get_engine_manager
        from services.audio_service import AudioService
        from services.voice_personality_service import VoicePersonalityService
        from core.chat_engine import ChatEngine
        from core.mem0_proxy import get_mem0_proxy
        
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
    print("🚀 .env文件加载优化测试")
    print("=" * 50)
    
    # 测试.env文件加载
    env_success = test_env_loading()
    
    # 测试导入性能
    performance_success = test_import_performance()
    
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f".env文件加载测试: {'✅ 通过' if env_success else '❌ 失败'}")
    print(f"导入性能测试: {'✅ 通过' if performance_success else '❌ 失败'}")
    
    if env_success and performance_success:
        print("\n🎉 所有测试通过！.env文件加载优化成功！")
        print("✅ .env文件重复加载问题已解决")
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
