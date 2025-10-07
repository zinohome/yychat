#!/bin/bash

# 性能测试脚本 - Memory优化验证

echo "🧪 Memory优化性能测试"
echo "===================="
echo ""

# 从.env加载API密钥
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$YYCHAT_API_KEY" ]; then
    echo "❌ Error: YYCHAT_API_KEY not found in .env"
    exit 1
fi

API_URL="http://192.168.66.209:9800"

echo "📋 测试配置:"
echo "  - Memory超时: $(grep MEMORY_RETRIEVAL_TIMEOUT .env)"
echo "  - Memory限制: $(grep MEMORY_RETRIEVAL_LIMIT .env)"
echo "  - 缓存时间: $(grep MEMORY_CACHE_TTL .env | tail -1)"
echo ""

# 测试1: 基本响应性能
echo "1️⃣ 测试基本响应性能（3次）"
echo "--------------------------------"
for i in {1..3}; do
    echo -n "第${i}次: "
    START=$(date +%s.%N)
    curl -s -X POST "$API_URL/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $YYCHAT_API_KEY" \
        -d '{"messages": [{"role": "user", "content": "你好，请简单回复"}], "stream": false}' \
        > /dev/null
    END=$(date +%s.%N)
    ELAPSED=$(echo "$END - $START" | bc)
    echo "耗时 ${ELAPSED}s"
    sleep 1
done
echo ""

# 测试2: 缓存效果（相同问题3次）
echo "2️⃣ 测试缓存效果（相同问题3次）"
echo "--------------------------------"
SAME_QUESTION="今天天气怎么样？"
for i in {1..3}; do
    echo -n "第${i}次: "
    START=$(date +%s.%N)
    curl -s -X POST "$API_URL/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $YYCHAT_API_KEY" \
        -d "{\"messages\": [{\"role\": \"user\", \"content\": \"$SAME_QUESTION\"}], \"stream\": false}" \
        > /dev/null
    END=$(date +%s.%N)
    ELAPSED=$(echo "$END - $START" | bc)
    echo "耗时 ${ELAPSED}s"
    if [ $i -eq 1 ]; then
        echo "   ⏱️  (首次，Memory未命中)"
    else
        echo "   ✅ (应该缓存命中，Memory < 0.01s)"
    fi
    sleep 1
done
echo ""

# 测试3: 查看性能统计
echo "3️⃣ 性能统计数据"
echo "--------------------------------"
STATS=$(curl -s -X GET "$API_URL/v1/performance/stats" \
    -H "Authorization: Bearer $YYCHAT_API_KEY")

echo "$STATS" | python3 -c "
import sys
import json
try:
    data = json.load(sys.stdin)
    if data.get('status') == 'ok':
        print(f\"📊 总请求数: {data['summary']['total_requests']}\")
        print(f\"⏱️  平均响应: {data['total_time']['avg']}\")
        print(f\"📈 P95响应: {data['total_time']['p95']}\")
        print(f\"💾 缓存命中率: {data['cache']['hit_rate']}\")
        if 'memory_retrieval' in data:
            print(f\"🧠 Memory平均: {data['memory_retrieval']['avg']}\")
    else:
        print('暂无性能数据')
except:
    print('暂无性能数据')
" || echo "暂无性能数据"

echo ""

# 测试4: 查看最近3次请求详情
echo "4️⃣ 最近3次请求详情"
echo "--------------------------------"
RECENT=$(curl -s -X GET "$API_URL/v1/performance/recent?count=3" \
    -H "Authorization: Bearer $YYCHAT_API_KEY")

echo "$RECENT" | python3 -c "
import sys
import json
try:
    data = json.load(sys.stdin)
    if 'metrics' in data:
        for i, m in enumerate(data['metrics'][-3:], 1):
            total = m.get('total_time', 0)
            mem = m.get('memory_retrieval_time', 0)
            hit = '✓' if m.get('memory_cache_hit') else '✗'
            print(f\"  请求{i}: 总耗时={total:.3f}s, Memory={mem:.3f}s({hit}))\")
    else:
        print('  暂无数据')
except:
    print('  暂无数据')
" || echo "  暂无数据"

echo ""
echo "===================="
echo "✅ 测试完成"
echo ""
echo "💡 提示:"
echo "  - 观察第2、3次相同问题的Memory时间"
echo "  - 应该从 0.3s 降到 < 0.01s (缓存命中)"
echo "  - 总响应时间应该有明显下降"
echo ""

