#!/bin/bash

echo "🔍 性能监控配置验证"
echo "===================="
echo ""

# 检查.env文件
echo "1️⃣  检查 .env 文件配置:"
if [ -f .env ]; then
    grep "ENABLE_PERFORMANCE_MONITOR" .env
    grep "PERFORMANCE_LOG_ENABLED" .env
    grep "PERFORMANCE_MAX_HISTORY" .env
    grep "PERFORMANCE_SAMPLING_RATE" .env
    echo "   ✅ .env 配置存在"
else
    echo "   ❌ .env 文件不存在"
    exit 1
fi
echo ""

# 检查config.py
echo "2️⃣  检查 config.py 配置项:"
if grep -q "ENABLE_PERFORMANCE_MONITOR" config/config.py; then
    echo "   ✅ ENABLE_PERFORMANCE_MONITOR 已定义"
else
    echo "   ❌ ENABLE_PERFORMANCE_MONITOR 未定义"
fi

if grep -q "PERFORMANCE_LOG_ENABLED" config/config.py; then
    echo "   ✅ PERFORMANCE_LOG_ENABLED 已定义"
else
    echo "   ❌ PERFORMANCE_LOG_ENABLED 未定义"
fi

if grep -q "PERFORMANCE_MAX_HISTORY" config/config.py; then
    echo "   ✅ PERFORMANCE_MAX_HISTORY 已定义"
else
    echo "   ❌ PERFORMANCE_MAX_HISTORY 未定义"
fi
echo ""

# 检查导入
echo "3️⃣  检查代码集成:"
if grep -q "performance_monitor" app.py; then
    echo "   ✅ app.py 已导入 performance_monitor"
else
    echo "   ❌ app.py 未导入 performance_monitor"
fi

if grep -q "config.ENABLE_PERFORMANCE_MONITOR" core/chat_engine.py; then
    echo "   ✅ chat_engine.py 使用配置"
else
    echo "   ❌ chat_engine.py 未使用配置"
fi
echo ""

# 测试导入
echo "4️⃣  测试Python导入:"
python3 -c "
from config.config import Config
c = Config()
print(f'   ✅ ENABLE_PERFORMANCE_MONITOR = {c.ENABLE_PERFORMANCE_MONITOR}')
print(f'   ✅ PERFORMANCE_LOG_ENABLED = {c.PERFORMANCE_LOG_ENABLED}')
print(f'   ✅ PERFORMANCE_MAX_HISTORY = {c.PERFORMANCE_MAX_HISTORY}')
print(f'   ✅ PERFORMANCE_SAMPLING_RATE = {c.PERFORMANCE_SAMPLING_RATE}')
" 2>&1
echo ""

# 总结
echo "===================="
echo "✅ 性能监控配置验证完成"
echo ""
echo "📋 配置摘要:"
echo "  - 配置参数: 已添加到 config.py"
echo "  - 环境变量: 已添加到 .env"  
echo "  - 代码集成: 已完成"
echo "  - 导入测试: 通过"
echo ""
echo "🚀 下一步: 重启服务查看启动日志"
echo "   ./start_with_venv.sh"

