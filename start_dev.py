#!/usr/bin/env python3
"""
开发模式启动脚本
保留热重载但优化初始化逻辑
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
    
    # 开发模式配置
    config = {
        "app": "app:app",
        "host": "0.0.0.0",
        "port": 9800,
        "reload": True,  # 启用热重载
        "reload_dirs": [str(project_root)],  # 只监听项目目录
        "reload_excludes": [
            "*.pyc",
            "*.pyo", 
            "__pycache__",
            ".git",
            ".venv",
            "chroma_db",
            "logs",
            "test",
            "*.log"
        ],  # 排除不需要监听的文件
        "log_level": "info",
        "access_log": True,
        "use_colors": True,
        "loop": "asyncio",
        "http": "httptools",
        "ws": "websockets",
        "lifespan": "on",
    }
    
    print("🚀 启动开发模式yychat服务器...")
    print(f"📡 服务地址: http://0.0.0.0:{config['port']}")
    print(f"📚 API文档: http://0.0.0.0:{config['port']}/docs")
    print("⚡ 开发模式: 启用热重载，优化文件监听")
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
