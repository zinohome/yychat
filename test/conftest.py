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
def test_multi_turn_messages():
    """多轮对话消息"""
    return [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": "How are you?"}
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
