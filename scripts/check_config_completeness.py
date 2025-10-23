#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置完整性检查脚本
检查config.py和env.example中的配置项是否一致
"""

import re
import os

def extract_config_from_py():
    """从config.py中提取配置项"""
    config_items = set()
    with open('config/config.py', 'r', encoding='utf-8') as f:
        content = f.read()
        # 匹配 os.getenv("CONFIG_NAME", "default")
        matches = re.findall(r'os\.getenv\("([A-Z_]+)"', content)
        config_items.update(matches)
    return config_items

def extract_config_from_env():
    """从env.example中提取配置项"""
    config_items = set()
    with open('env.example', 'r', encoding='utf-8') as f:
        content = f.read()
        # 匹配 CONFIG_NAME=value
        matches = re.findall(r'^([A-Z_]+)=', content, re.MULTILINE)
        config_items.update(matches)
    return config_items

def main():
    print("🔍 配置完整性检查")
    print("=" * 50)
    
    # 提取配置项
    py_configs = extract_config_from_py()
    env_configs = extract_config_from_env()
    
    print(f"📊 统计信息:")
    print(f"  config.py 中的配置项: {len(py_configs)}")
    print(f"  env.example 中的配置项: {len(env_configs)}")
    
    # 检查差异
    missing_in_env = py_configs - env_configs
    missing_in_py = env_configs - py_configs
    
    if missing_in_env:
        print(f"\n❌ env.example 中缺失的配置项 ({len(missing_in_env)}个):")
        for item in sorted(missing_in_env):
            print(f"  - {item}")
    
    if missing_in_py:
        print(f"\n❌ config.py 中缺失的配置项 ({len(missing_in_py)}个):")
        for item in sorted(missing_in_py):
            print(f"  - {item}")
    
    if not missing_in_env and not missing_in_py:
        print("\n✅ 配置项完全一致！")
        return 0
    else:
        print(f"\n❌ 发现配置项不一致")
        return 1

if __name__ == "__main__":
    exit(main())
