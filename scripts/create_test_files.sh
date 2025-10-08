#!/bin/bash

# 创建YYChat测试文件脚本
# 用途：快速创建测试目录结构

echo "======================================"
echo "  创建YYChat测试文件结构"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在项目根目录
if [ ! -f "app.py" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 创建测试目录结构
echo "📁 创建测试目录..."
mkdir -p test/unit
mkdir -p test/integration
mkdir -p test/fixtures/data
mkdir -p test/e2e

# 创建__init__.py
echo "📝 创建__init__.py文件..."
touch test/__init__.py
touch test/unit/__init__.py
touch test/integration/__init__.py
touch test/fixtures/__init__.py

# 创建conftest.py
echo "📝 创建conftest.py..."
cat > test/conftest.py << 'EOF'
"""
Pytest配置和固件
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def test_conversation_id():
    """测试用的会话ID"""
    return "test_conv_001"

@pytest.fixture
def test_messages():
    """测试用的消息列表"""
    return [
        {"role": "user", "content": "Hello, how are you?"}
    ]

@pytest.fixture
async def chat_engine():
    """Chat引擎fixture"""
    from core.chat_engine import chat_engine
    return chat_engine

@pytest.fixture
async def mem0_proxy():
    """Mem0Proxy引擎fixture"""
    from core.mem0_proxy import get_mem0_proxy
    return get_mem0_proxy()
EOF

# 创建简单的环境测试
echo "📝 创建环境验证测试..."
cat > test/test_environment.py << 'EOF'
"""环境验证测试"""

def test_environment():
    """验证测试环境正常"""
    assert True

def test_imports():
    """验证关键模块可导入"""
    from core.chat_engine import chat_engine
    assert chat_engine is not None
EOF

echo ""
echo -e "${GREEN}✅ 测试文件结构创建完成！${NC}"
echo ""
echo "目录结构："
tree test/ 2>/dev/null || find test/ -print | sed -e 's;[^/]*/;|____;g;s;____|; |;g'

echo ""
echo "接下来："
echo "1. 运行: pytest test/test_environment.py -v"
echo "2. 开始编写测试用例"
echo "3. 参考: docs/DAY1_EXECUTION_GUIDE.md"

