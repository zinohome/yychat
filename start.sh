#!/bin/bash

# 创建必要的目录
mkdir -p personalities chroma_db

# 安装依赖
pip install -r requirements.txt

# 启动服务器
python app.py