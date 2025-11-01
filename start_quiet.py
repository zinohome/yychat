#!/usr/bin/env python3
"""
静默启动脚本 - 抑制所有警告
用于开发环境，减少控制台噪音
"""

import warnings
import sys
import os

# 在导入任何其他模块之前抑制所有警告
warnings.filterwarnings("ignore")

# 设置环境变量以减少日志输出
os.environ["PYTHONWARNINGS"] = "ignore"

# 导入并启动应用
if __name__ == "__main__":
    # 导入应用
    from app import app
    import uvicorn
    
    print("🚀 启动 YYChat 后端服务 (静默模式)")
    print("📍 服务地址: http://192.168.66.145:9800")
    print("🔇 警告已抑制")
    
    # 启动服务
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=9800,
        reload=True,
        log_level="warning"  # 只显示警告级别以上的日志
    )
