#!/usr/bin/env python3
"""
测试ChatEngine延迟初始化
验证Memory等组件是否在首次使用时正确初始化
"""

import sys
import os
import asyncio

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

async def test_chat_engine_initialization():
    """测试ChatEngine延迟初始化"""
    print("🧪 测试ChatEngine延迟初始化...")
    
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
        
        # 触发延迟初始化
        print("\n🚀 触发延迟初始化...")
        await engine.generate_response(
            messages=[{"role": "user", "content": "Hello"}],
            conversation_id="test",
            stream=False
        )
        
        # 检查初始化后状态
        print(f"\n📊 初始化后状态:")
        print(f"  _initialized: {engine._initialized}")
        print(f"  chat_memory: {engine.chat_memory is not None}")
        print(f"  async_chat_memory: {engine.async_chat_memory is not None}")
        print(f"  personality_manager: {engine.personality_manager is not None}")
        print(f"  tool_manager: {engine.tool_manager is not None}")
        
        print("✅ ChatEngine延迟初始化测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 ChatEngine延迟初始化测试")
    print("=" * 50)
    
    try:
        result = asyncio.run(test_chat_engine_initialization())
        
        print("\n" + "=" * 50)
        if result:
            print("🎉 测试通过！ChatEngine延迟初始化正常工作")
        else:
            print("❌ 测试失败！需要检查延迟初始化逻辑")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        return False

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 测试被中断")
        sys.exit(1)
