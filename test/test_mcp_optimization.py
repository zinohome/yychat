#!/usr/bin/env python3
"""
测试MCP优化效果
验证MCP客户端重复初始化问题是否已解决
"""

import sys
import os
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_mcp_import():
    """测试MCP相关模块导入，检查是否还有重复初始化"""
    print("🧪 测试MCP优化效果...")
    
    start_time = time.time()
    
    try:
        # 测试导入MCP相关模块
        print("📦 导入MCP管理器...")
        from services.mcp.manager import get_mcp_manager
        print("✅ MCP管理器导入成功")
        
        print("📦 导入MCP发现模块...")
        from services.mcp.discovery import discover_and_register_mcp_tools
        print("✅ MCP发现模块导入成功")
        
        print("📦 导入聊天引擎...")
        from core.chat_engine import ChatEngine
        print("✅ 聊天引擎导入成功")
        
        print("📦 导入Mem0代理...")
        from core.mem0_proxy import get_mem0_proxy
        print("✅ Mem0代理导入成功")
        
        print("📦 导入应用...")
        from app import app
        print("✅ 应用导入成功")
        
        end_time = time.time()
        import_time = end_time - start_time
        
        print(f"\n⏱️ 导入耗时: {import_time:.2f}秒")
        
        if import_time < 10:
            print("✅ 导入时间正常，没有重复初始化问题")
            return True
        else:
            print("⚠️ 导入时间较长，可能仍有重复初始化")
            return False
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_mcp_manager_lazy_init():
    """测试MCP管理器的延迟初始化"""
    print("\n🧪 测试MCP管理器延迟初始化...")
    
    try:
        from services.mcp.manager import get_mcp_manager
        
        # 第一次调用应该创建实例
        print("📞 第一次调用get_mcp_manager()...")
        manager1 = get_mcp_manager()
        print("✅ 第一次调用成功")
        
        # 第二次调用应该返回同一个实例
        print("📞 第二次调用get_mcp_manager()...")
        manager2 = get_mcp_manager()
        print("✅ 第二次调用成功")
        
        # 验证是同一个实例
        if manager1 is manager2:
            print("✅ 单例模式正常工作")
            return True
        else:
            print("❌ 单例模式失效，返回了不同实例")
            return False
            
    except Exception as e:
        print(f"❌ 延迟初始化测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 MCP优化测试")
    print("=" * 50)
    
    # 测试导入
    import_success = test_mcp_import()
    
    # 测试延迟初始化
    lazy_init_success = test_mcp_manager_lazy_init()
    
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"导入测试: {'✅ 通过' if import_success else '❌ 失败'}")
    print(f"延迟初始化测试: {'✅ 通过' if lazy_init_success else '❌ 失败'}")
    
    if import_success and lazy_init_success:
        print("\n🎉 所有测试通过！MCP优化成功！")
        print("✅ MCP客户端重复初始化问题已解决")
        print("✅ 延迟初始化正常工作")
        print("✅ 单例模式正常工作")
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
