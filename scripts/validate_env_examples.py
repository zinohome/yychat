#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证env.example文件的完整性
"""

import re
import os

def extract_config_from_py():
    """从config.py中提取所有配置项"""
    config_items = set()
    with open('config/config.py', 'r', encoding='utf-8') as f:
        content = f.read()
        # 匹配 os.getenv("CONFIG_NAME", "default")
        matches = re.findall(r'os\.getenv\("([A-Z_]+)"', content)
        config_items.update(matches)
    return config_items

def extract_config_from_env_file(file_path):
    """从env文件中提取配置项"""
    config_items = set()
    if not os.path.exists(file_path):
        return config_items
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 匹配 CONFIG_NAME=value
        matches = re.findall(r'^([A-Z_]+)=', content, re.MULTILINE)
        config_items.update(matches)
    return config_items

def main():
    print("🔍 环境变量示例文件完整性检查")
    print("=" * 60)
    
    # 提取所有配置项
    py_configs = extract_config_from_py()
    full_configs = extract_config_from_env_file('env.example.full')
    simple_configs = extract_config_from_env_file('env.example.simple')
    
    print(f"📊 统计信息:")
    print(f"  config.py 中的配置项: {len(py_configs)}")
    print(f"  env.example.full 中的配置项: {len(full_configs)}")
    print(f"  env.example.simple 中的配置项: {len(simple_configs)}")
    
    # 检查完整版
    print(f"\n📋 env.example.full 检查:")
    missing_in_full = py_configs - full_configs
    extra_in_full = full_configs - py_configs
    
    if missing_in_full:
        print(f"  ❌ 缺失的配置项 ({len(missing_in_full)}个):")
        for item in sorted(missing_in_full):
            print(f"    - {item}")
    else:
        print(f"  ✅ 包含所有配置项")
    
    if extra_in_full:
        print(f"  ⚠️  多余的配置项 ({len(extra_in_full)}个):")
        for item in sorted(extra_in_full):
            print(f"    - {item}")
    
    # 检查精简版
    print(f"\n📋 env.example.simple 检查:")
    missing_in_simple = py_configs - simple_configs
    extra_in_simple = simple_configs - py_configs
    
    if missing_in_simple:
        print(f"  ⚠️  精简版缺失的配置项 ({len(missing_in_simple)}个):")
        for item in sorted(missing_in_simple):
            print(f"    - {item}")
    else:
        print(f"  ✅ 精简版包含所有配置项")
    
    if extra_in_simple:
        print(f"  ❌ 精简版多余的配置项 ({len(extra_in_simple)}个):")
        for item in sorted(extra_in_simple):
            print(f"    - {item}")
    
    # 检查精简版是否真的是精简版
    if len(simple_configs) < len(full_configs):
        print(f"\n✅ 精简版确实比完整版精简: {len(simple_configs)} < {len(full_configs)}")
    else:
        print(f"\n⚠️  精简版配置项数量: {len(simple_configs)} >= 完整版: {len(full_configs)}")
    
    # 检查关键配置项是否都在精简版中
    key_configs = {
        'OPENAI_API_KEY', 'OPENAI_MODEL', 'OPENAI_BASE_URL', 'OPENAI_TEMPERATURE',
        'SERVER_HOST', 'SERVER_PORT', 'CHAT_ENGINE', 'DEFAULT_PERSONALITY',
        'VECTOR_STORE_PROVIDER', 'CHROMA_PERSIST_DIRECTORY', 'CHROMA_COLLECTION_NAME',
        'ENABLE_MEMORY_RETRIEVAL', 'MEMORY_RETRIEVAL_LIMIT', 'LOG_LEVEL'
    }
    
    missing_key_configs = key_configs - simple_configs
    if missing_key_configs:
        print(f"\n❌ 精简版缺失关键配置项 ({len(missing_key_configs)}个):")
        for item in sorted(missing_key_configs):
            print(f"  - {item}")
    else:
        print(f"\n✅ 精简版包含所有关键配置项")
    
    return 0

if __name__ == "__main__":
    exit(main())
