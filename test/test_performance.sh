#!/bin/bash

# YYChat 性能测试脚本
# 用于测试优化前后的性能对比

YYCHAT_URL="http://localhost:8000"
YYCHAT_API_KEY="${YYCHAT_API_KEY:-yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4}"

echo "========================================="
echo "YYChat 性能测试"
echo "========================================="
echo "服务地址: $YYCHAT_URL"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 测试1: 基本响应测试
echo "📊 测试1: 基本响应性能 (非流式，5次请求)"
echo "-----------------------------------------"
total_time=0
for i in {1..5}; do
  echo -n "请求 $i: "
  START=$(date +%s.%N)
  
  response=$(curl -s -X POST "$YYCHAT_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $YYCHAT_API_KEY" \
    -d '{
      "messages": [{"role": "user", "content": "你好"}],
      "stream": false
    }')
  
  END=$(date +%s.%N)
  DIFF=$(echo "$END - $START" | bc)
  total_time=$(echo "$total_time + $DIFF" | bc)
  echo "${DIFF}s"
  
  # 检查是否成功
  if echo "$response" | grep -q "error"; then
    echo "  ❌ 错误: $(echo $response | jq -r '.error.message')"
  fi
  
  sleep 0.5
done

avg_time=$(echo "scale=3; $total_time / 5" | bc)
echo ""
echo "✅ 平均响应时间: ${avg_time}s"
echo ""

# 测试2: 缓存效果测试
echo "📊 测试2: Memory缓存效果 (相同问题，3次请求)"
echo "-----------------------------------------"
cache_test_times=()
for i in {1..3}; do
  echo -n "请求 $i: "
  START=$(date +%s.%N)
  
  curl -s -X POST "$YYCHAT_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $YYCHAT_API_KEY" \
    -d '{
      "messages": [{"role": "user", "content": "介绍一下人工智能"}],
      "conversation_id": "test_cache_user",
      "stream": false
    }' > /dev/null
  
  END=$(date +%s.%N)
  DIFF=$(echo "$END - $START" | bc)
  cache_test_times+=($DIFF)
  echo "${DIFF}s"
  sleep 0.3
done

echo ""
echo "✅ 首次请求: ${cache_test_times[0]}s (无缓存)"
echo "✅ 第2次请求: ${cache_test_times[1]}s (可能命中缓存)"
echo "✅ 第3次请求: ${cache_test_times[2]}s (可能命中缓存)"
echo ""

# 测试3: 工具调用测试
echo "📊 测试3: 工具调用性能 (gettime工具，3次请求)"
echo "-----------------------------------------"
for i in {1..3}; do
  echo -n "请求 $i: "
  START=$(date +%s.%N)
  
  curl -s -X POST "$YYCHAT_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $YYCHAT_API_KEY" \
    -d '{
      "messages": [{"role": "user", "content": "现在几点钟？"}],
      "personality_id": "health_assistant",
      "use_tools": true,
      "stream": false
    }' > /dev/null
  
  END=$(date +%s.%N)
  DIFF=$(echo "$END - $START" | bc)
  echo "${DIFF}s"
  sleep 0.5
done
echo ""

# 测试4: 获取性能统计
echo "📊 测试4: 获取性能统计信息"
echo "-----------------------------------------"
stats=$(curl -s -X GET "$YYCHAT_URL/v1/performance/stats" \
  -H "Authorization: Bearer $YYCHAT_API_KEY")

if echo "$stats" | jq -e '.status == "ok"' > /dev/null 2>&1; then
  echo "✅ 性能统计已启用"
  echo ""
  echo "总请求数: $(echo $stats | jq -r '.summary.total_requests')"
  echo "平均响应时间: $(echo $stats | jq -r '.total_time.avg')"
  echo "中位数响应时间: $(echo $stats | jq -r '.total_time.median')"
  echo "P95响应时间: $(echo $stats | jq -r '.total_time.p95')"
  echo "P99响应时间: $(echo $stats | jq -r '.total_time.p99')"
  echo ""
  echo "缓存命中率: $(echo $stats | jq -r '.cache.hit_rate')"
  echo "缓存命中数: $(echo $stats | jq -r '.cache.hit_count')"
  echo "缓存未命中数: $(echo $stats | jq -r '.cache.miss_count')"
else
  echo "⚠️  性能统计暂无数据或未启用"
fi

echo ""
echo "========================================="
echo "测试完成: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================="
echo ""
echo "💡 提示:"
echo "  - 查看详细统计: curl $YYCHAT_URL/v1/performance/stats -H 'Authorization: Bearer \$YYCHAT_API_KEY'"
echo "  - 查看最近请求: curl $YYCHAT_URL/v1/performance/recent?count=10 -H 'Authorization: Bearer \$YYCHAT_API_KEY'"
echo "  - 清除统计数据: curl -X DELETE $YYCHAT_URL/v1/performance/clear -H 'Authorization: Bearer \$YYCHAT_API_KEY'"
echo ""

