#!/usr/bin/env python3
"""
测试启动时初始化
验证ChatEngine是否在启动时正确初始化所有组件
"""

import sys
import os
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_startup_initialization():
    """测试启动时初始化"""
    print("🧪 测试启动时初始化...")
    
    start_time = time.time()
    
    try:
        from core.chat_engine import ChatEngine
        
        print("✅ ChatEngine导入成功")
        
        # 创建ChatEngine实例
        engine = ChatEngine()
        print("✅ ChatEngine实例创建成功")
        
        # 检查初始状态
        print(f"📊 初始状态:")
        print(f"  _initialized: {engine._initialized}")
        print(f"  chat_memory: {engine.chat_memory}")
        print(f"  async_chat_memory: {engine.async_chat_memory}")
        print(f"  personality_manager: {engine.personality_manager}")
        print(f"  tool_manager: {engine.tool_manager}")
        
        # 强制初始化
        print("\n🚀 强制初始化组件...")
        init_start = time.time()
        engine._ensure_initialized()
        init_end = time.time()
        init_time = init_end - init_start
        
        print(f"⏱️ 初始化耗时: {init_time:.2f}秒")
        
        # 检查初始化后状态
        print(f"\n📊 初始化后状态:")
        print(f"  _initialized: {engine._initialized}")
        print(f"  chat_memory: {engine.chat_memory is not None}")
        print(f"  async_chat_memory: {engine.async_chat_memory is not None}")
        print(f"  personality_manager: {engine.personality_manager is not None}")
        print(f"  tool_manager: {engine.tool_manager is not None}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n⏱️ 总耗时: {total_time:.2f}秒")
        
        if engine._initialized and init_time < 2:
            print("✅ 启动时初始化测试成功")
            return True
        else:
            print("❌ 启动时初始化测试失败")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 启动时初始化测试")
    print("=" * 50)
    
    result = test_startup_initialization()
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 启动时初始化测试成功")
        print("✅ ChatEngine组件在启动时正确初始化")
    else:
        print("❌ 启动时初始化测试失败")
    
    return result

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 测试被中断")
        sys.exit(1)
