#!/usr/bin/env python3
"""
快速检查 Mem0 配置是否正确
"""

import os
import sys

# 将项目根目录添加到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.config import get_config


def check_config():
    """检查配置"""
    config = get_config()
    
    print("\n" + "="*60)
    print("Mem0 配置检查")
    print("="*60 + "\n")
    
    is_local = config.MEMO_USE_LOCAL
    mode = "本地模式 (Local)" if is_local else "API模式 (Cloud)"
    
    print(f"📌 当前模式: {mode}")
    print()
    
    issues = []
    warnings = []
    
    if is_local:
        # 检查本地模式配置
        print("🔍 检查本地模式配置...")
        
        # LLM 配置
        if config.MEM0_LLM_PROVIDER:
            print(f"  ✓ LLM Provider: {config.MEM0_LLM_PROVIDER}")
        else:
            issues.append("MEM0_LLM_PROVIDER 未配置")
        
        if config.MEM0_LLM_CONFIG_MODEL:
            print(f"  ✓ LLM Model: {config.MEM0_LLM_CONFIG_MODEL}")
        else:
            warnings.append("MEM0_LLM_CONFIG_MODEL 未配置，将使用默认值")
        
        # ChromaDB 配置
        chroma_path = config.CHROMA_PERSIST_DIRECTORY
        print(f"  ✓ ChromaDB 路径: {chroma_path}")
        
        # 检查路径是否存在或可创建
        try:
            os.makedirs(chroma_path, exist_ok=True)
            print(f"  ✓ ChromaDB 路径可访问")
        except Exception as e:
            issues.append(f"ChromaDB 路径不可访问: {e}")
        
        print(f"  ✓ Collection 名称: {config.CHROMA_COLLECTION_NAME}")
        
        # 检查依赖
        print("\n🔍 检查依赖包...")
        try:
            import mem0
            print(f"  ✓ mem0ai 已安装")
        except ImportError:
            issues.append("mem0ai 未安装，请运行: pip install mem0ai")
        
        try:
            import chromadb
            print(f"  ✓ chromadb 已安装")
        except ImportError:
            issues.append("chromadb 未安装，请运行: pip install chromadb")
    
    else:
        # 检查 API 模式配置
        print("🔍 检查 API 模式配置...")
        
        if config.MEM0_API_KEY:
            key_preview = config.MEM0_API_KEY[:10] + "..." if len(config.MEM0_API_KEY) > 10 else config.MEM0_API_KEY
            print(f"  ✓ API Key 已配置: {key_preview}")
        else:
            issues.append("MEM0_API_KEY 未配置，API 模式需要此配置")
        
        # 检查依赖
        print("\n🔍 检查依赖包...")
        try:
            import mem0
            print(f"  ✓ mem0ai 已安装")
        except ImportError:
            issues.append("mem0ai 未安装，请运行: pip install mem0ai")
        
        try:
            from mem0 import MemoryClient
            print(f"  ✓ MemoryClient 可用")
        except ImportError:
            warnings.append("MemoryClient 不可用，可能需要更新 mem0ai 版本")
    
    # 通用配置检查
    print("\n🔍 检查通用配置...")
    print(f"  ✓ 检索限制: {config.MEMORY_RETRIEVAL_LIMIT}")
    print(f"  ✓ 检索超时: {config.MEMORY_RETRIEVAL_TIMEOUT}秒")
    print(f"  ✓ 保存模式: {config.MEMORY_SAVE_MODE}")
    
    # 总结
    print("\n" + "="*60)
    print("检查结果")
    print("="*60)
    
    if not issues and not warnings:
        print("✅ 配置检查通过！所有配置项都正确。")
        print("\n💡 提示:")
        print(f"   当前使用 {mode}")
        if is_local:
            print("   数据将存储在本地 ChromaDB")
            print(f"   路径: {config.CHROMA_PERSIST_DIRECTORY}")
        else:
            print("   数据将存储在 Mem0 云端")
        
        print("\n🚀 可以运行测试脚本验证:")
        print("   python test_memory_mode.py")
        return 0
    
    else:
        if warnings:
            print("\n⚠️ 警告:")
            for warning in warnings:
                print(f"   • {warning}")
        
        if issues:
            print("\n❌ 错误:")
            for issue in issues:
                print(f"   • {issue}")
            
            print("\n📝 解决方案:")
            if is_local:
                print("   1. 确保安装依赖: pip install mem0ai chromadb")
                print("   2. 检查 ChromaDB 路径权限")
                print(f"   3. 设置环境变量: MEMO_USE_LOCAL=true")
            else:
                print("   1. 确保安装依赖: pip install mem0ai")
                print("   2. 设置 API Key: export MEM0_API_KEY=your_key")
                print(f"   3. 设置环境变量: MEMO_USE_LOCAL=false")
            
            return 1
        
        return 0


def print_env_template():
    """打印环境变量模板"""
    print("\n" + "="*60)
    print("环境变量配置模板")
    print("="*60)
    
    print("\n# 本地模式配置")
    print("MEMO_USE_LOCAL=true")
    print("MEM0_LLM_PROVIDER=openai")
    print("MEM0_LLM_CONFIG_MODEL=gpt-4o-mini")
    print("MEM0_LLM_CONFIG_MAX_TOKENS=32768")
    print("CHROMA_PERSIST_DIRECTORY=./chroma_db")
    print("CHROMA_COLLECTION_NAME=chat_history")
    
    print("\n# API 模式配置")
    print("MEMO_USE_LOCAL=false")
    print("MEM0_API_KEY=your_mem0_api_key_here")
    
    print("\n# 通用配置")
    print("MEMORY_RETRIEVAL_LIMIT=5")
    print("MEMORY_RETRIEVAL_TIMEOUT=10")
    print("MEMORY_SAVE_MODE=both")
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="检查 Mem0 配置")
    parser.add_argument("--template", action="store_true", help="显示环境变量配置模板")
    
    args = parser.parse_args()
    
    if args.template:
        print_env_template()
        sys.exit(0)
    
    exit_code = check_config()
    
    if exit_code == 0:
        print()
    
    sys.exit(exit_code)

