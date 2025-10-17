#!/bin/bash
# 静默启动脚本

echo "🚀 启动 YYChat 后端服务 (静默模式)"
echo "📍 服务地址: http://192.168.66.209:9800"
echo "🔇 警告已抑制"

# 设置环境变量
export PYTHONWARNINGS=ignore
export LOG_LEVEL=WARNING

# 启动服务
cd /Users/zhangjun/PycharmProjects/yychat
python -W ignore app.py
