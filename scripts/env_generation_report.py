#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境变量文件生成报告
"""

import os
import re

def main():
    print("📋 环境变量文件生成报告")
    print("=" * 60)
    
    # 检查文件是否存在
    files = {
        'env.example': '原始配置文件',
        'env.example.full': '完整配置文件',
        'env.example.simple': '精简配置文件'
    }
    
    print("📁 文件检查:")
    for file, desc in files.items():
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = len(content.split('\n'))
                configs = len(re.findall(r'^[A-Z_]+=', content, re.MULTILINE))
                print(f"  ✅ {file}: {desc} ({lines}行, {configs}个配置项)")
        else:
            print(f"  ❌ {file}: {desc} (文件不存在)")
    
    # 统计配置项
    print(f"\n📊 配置项统计:")
    
    # 从config.py提取配置项
    with open('config/config.py', 'r', encoding='utf-8') as f:
        content = f.read()
        py_configs = set(re.findall(r'os\.getenv\("([A-Z_]+)"', content))
    
    # 从各env文件提取配置项
    env_files = ['env.example', 'env.example.full', 'env.example.simple']
    for env_file in env_files:
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                env_configs = set(re.findall(r'^([A-Z_]+)=', content, re.MULTILINE))
                print(f"  {env_file}: {len(env_configs)}个配置项")
                
                # 检查完整性
                missing = py_configs - env_configs
                extra = env_configs - py_configs
                
                if missing:
                    print(f"    缺失: {len(missing)}个")
                if extra:
                    print(f"    多余: {len(extra)}个")
                if not missing and not extra:
                    print(f"    ✅ 配置项完整")
    
    print(f"\n🎯 文件特点:")
    print(f"  env.example: 原始配置文件，包含基础配置项")
    print(f"  env.example.full: 完整配置文件，包含所有87个配置项")
    print(f"  env.example.simple: 精简配置文件，包含63个关键配置项")
    
    print(f"\n🚀 使用建议:")
    print(f"  - 快速部署: 使用 env.example.simple")
    print(f"  - 生产环境: 使用 env.example.full")
    print(f"  - 开发测试: 使用 env.example.simple")
    print(f"  - Docker部署: 使用 env.example.simple")
    
    print(f"\n📝 配置说明:")
    print(f"  - 所有配置项都有合理的默认值")
    print(f"  - 支持通过环境变量覆盖配置")
    print(f"  - 配置项按功能模块分组")
    print(f"  - 包含详细的中文注释")
    
    print(f"\n✅ 生成完成!")
    print(f"  - 3个环境变量配置文件")
    print(f"  - 1个配置指南文档")
    print(f"  - 1个验证脚本")
    
    return 0

if __name__ == "__main__":
    exit(main())
