#!/bin/bash

# 引擎管理器测试脚本

# 从 .env 文件加载 YYCHAT_API_KEY
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "$YYCHAT_API_KEY" ]; then
  echo "Error: YYCHAT_API_KEY not found in .env"
  exit 1
fi

BASE_URL="http://localhost:8000"
API_KEY="Bearer $YYCHAT_API_KEY"

echo "========================================="
echo "  引擎管理器功能测试"
echo "========================================="
echo ""

# 测试1: 列出所有引擎
echo "✅ 测试1: 列出所有引擎"
curl -s -X GET "${BASE_URL}/v1/engines/list" \
  -H "Authorization: ${API_KEY}" \
  -H "Content-Type: application/json" | jq .
echo ""
echo ""

# 测试2: 获取当前引擎信息
echo "✅ 测试2: 获取当前引擎信息"
curl -s -X GET "${BASE_URL}/v1/engines/current" \
  -H "Authorization: ${API_KEY}" \
  -H "Content-Type: application/json" | jq .
echo ""
echo ""

# 测试3: 健康检查
echo "✅ 测试3: 引擎健康检查"
curl -s -X GET "${BASE_URL}/v1/engines/health" \
  -H "Authorization: ${API_KEY}" \
  -H "Content-Type: application/json" | jq .
echo ""
echo ""

# 测试4: 尝试切换引擎（如果只有一个引擎，会失败，这是正常的）
echo "✅ 测试4: 尝试切换引擎（测试功能）"
curl -s -X POST "${BASE_URL}/v1/engines/switch?engine_name=chat_engine" \
  -H "Authorization: ${API_KEY}" \
  -H "Content-Type: application/json" | jq .
echo ""
echo ""

echo "========================================="
echo "  测试完成！"
echo "========================================="

