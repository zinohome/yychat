import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """设置测试环境，包括临时配置和目录"""
    # 创建临时目录作为ChromaDB存储位置
    original_chroma_dir = os.environ.get('CHROMA_PERSIST_DIRECTORY', 'chroma_db')
    temp_dir = tempfile.mkdtemp()
    
    # 保存原始环境变量
    original_env = dict(os.environ)
    
    # 设置测试环境变量
    os.environ['CHROMA_PERSIST_DIRECTORY'] = temp_dir
    os.environ['CHROMA_COLLECTION_NAME'] = 'test_collection'
    os.environ['OPENAI_API_KEY'] = 'test-api-key'
    os.environ['OPENAI_BASE_URL'] = 'http://localhost:8000/v1'
    os.environ['MEM0_TELEMETRY'] = 'false'
    os.environ['LOG_LEVEL'] = 'ERROR'  # 测试时减少日志输出
    
    try:
        yield
    finally:
        # 恢复原始环境变量
        os.environ.clear()
        os.environ.update(original_env)
        
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@pytest.fixture
def mock_openai_client():
    """模拟OpenAI客户端"""
    with patch('core.chat_engine.OpenAI') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # 设置模拟响应
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(content="这是一个测试响应"),
                finish_reason="stop"
            )],
            usage=MagicMock(
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30
            )
        )
        
        yield mock_instance

@pytest.fixture
def mock_memory():
    """模拟记忆存储"""
    # 修改patch的路径，使其匹配core/chat_memory.py中的导入
    with patch('core.chat_memory.Memory') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.add.return_value = None
        # 移除get_relevant的side_effect设置，让测试自己设置return_value
        # mock_instance.get_relevant.side_effect = lambda query, limit=5, user_id=None: []
        # 移除get的side_effect设置，让测试自己设置return_value
        # mock_instance.get.side_effect = lambda query, limit=5, user_id=None: []
        # 移除get_all的side_effect设置，让测试自己设置return_value
        # mock_instance.get_all.side_effect = lambda user_id=None: []
        mock_instance.delete_all.side_effect = lambda user_id=None: None
        
        # 修改这里，返回mock而不是mock_instance
        yield mock

@pytest.fixture
def test_client():
    """创建FastAPI测试客户端"""
    from fastapi.testclient import TestClient
    from app import app
    
    with TestClient(app) as client:
        yield client


import warnings
from pydantic.warnings import PydanticDeprecatedSince20

# 忽略来自mem0库的Pydantic弃用警告
warnings.filterwarnings(
    "ignore",
    category=PydanticDeprecatedSince20,
    message="Support for class-based `config` is deprecated, use ConfigDict instead.",
    module="mem0.*"
)