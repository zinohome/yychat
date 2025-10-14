#!/usr/bin/env python3
"""
优化的yychat启动脚本
避免热重载导致的重复初始化问题
"""

import uvicorn
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主启动函数"""
    # 设置环境变量
    os.environ.setdefault("PYTHONPATH", str(project_root))
    
    # 启动配置
    config = {
        "app": "app:app",
        "host": "0.0.0.0",
        "port": 9800,
        "reload": False,  # 禁用热重载，避免重复初始化
        "reload_dirs": [],  # 空的重载目录
        "log_level": "info",
        "access_log": True,
        "use_colors": True,
        "loop": "asyncio",
        "http": "httptools",  # 使用更快的HTTP解析器
        "ws": "websockets",
        "lifespan": "on",  # 启用lifespan事件
    }
    
    print("🚀 启动优化的yychat服务器...")
    print(f"📡 服务地址: http://0.0.0.0:{config['port']}")
    print(f"📚 API文档: http://0.0.0.0:{config['port']}/docs")
    print("⚡ 优化模式: 禁用热重载，避免重复初始化")
    print("=" * 50)
    
    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
