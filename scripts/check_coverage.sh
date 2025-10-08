#!/bin/bash

# 测试覆盖率检查脚本
# 用途：运行测试并生成覆盖率报告

echo "======================================"
echo "  YYChat 测试覆盖率检查"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查pytest是否安装
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest未安装${NC}"
    echo "安装命令: pip install pytest pytest-cov pytest-asyncio"
    exit 1
fi

# 检查pytest-cov是否安装
if ! python -c "import pytest_cov" 2>/dev/null; then
    echo -e "${RED}❌ pytest-cov未安装${NC}"
    echo "安装命令: pip install pytest-cov"
    exit 1
fi

# 运行测试并生成覆盖率
echo "🧪 运行测试..."
echo ""

pytest test/ \
    --cov=core \
    --cov=services \
    --cov=utils \
    --cov-report=term-missing \
    --cov-report=html \
    -v

test_result=$?

echo ""
echo "======================================"
echo "  覆盖率报告"
echo "======================================"
echo ""

# 生成摘要报告
if [ $test_result -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过${NC}"
else
    echo -e "${RED}❌ 有测试失败${NC}"
fi

echo ""
echo "📊 HTML报告已生成: htmlcov/index.html"
echo ""

# 提取覆盖率数字
if command -v coverage &> /dev/null; then
    coverage_percent=$(coverage report | grep TOTAL | awk '{print $4}')
    current=${coverage_percent%\%}
    
    echo "当前覆盖率: $coverage_percent"
    echo ""
    
    # 检查是否达标
    target=80
    
    if (( $(echo "$current >= $target" | bc -l 2>/dev/null || echo "0") )); then
        echo -e "${GREEN}🎉 覆盖率达标！超过${target}%${NC}"
    else
        remaining=$((target - current))
        echo -e "${YELLOW}⚠️  还需提高 ${remaining}% 达到目标${NC}"
        
        # 给出进度条
        progress=$((current * 100 / target))
        bar_length=$((progress / 2))
        printf "进度: ["
        for i in $(seq 1 50); do
            if [ $i -le $bar_length ]; then
                printf "="
            else
                printf " "
            fi
        done
        printf "] ${progress}%%\n"
    fi
fi

echo ""
echo "查看详细报告:"
echo "  在浏览器打开: htmlcov/index.html"
echo "  或运行: open htmlcov/index.html"
echo ""

# 显示未覆盖文件
echo "未覆盖或覆盖率低的文件："
coverage report --skip-covered 2>/dev/null | head -20 || echo "需要先安装coverage"

exit $test_result

