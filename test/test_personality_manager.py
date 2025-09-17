import pytest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
from core.personality_manager import PersonalityManager, Personality
from config.log_config import get_logger

@pytest.fixture
def mock_config():
    # 模拟配置对象
    with patch('config.config.get_config') as mock_get_config:
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config
        yield mock_config

@pytest.fixture
def mock_logger():
    # 模拟日志记录器
    import core.personality_manager
    with patch.object(core.personality_manager, 'logger') as mock_logger:
        yield mock_logger

@pytest.fixture
def temp_personality_dir(tmp_path):
    # 创建临时人格目录
    temp_dir = tmp_path / "personalities"
    temp_dir.mkdir()
    return str(temp_dir)

@pytest.mark.asyncio
async def test_personality_manager_initialization(temp_personality_dir, mock_config, mock_logger):
    # 测试PersonalityManager的初始化
    with patch('os.path.exists', return_value=True):
        # 创建PersonalityManager实例
        personality_manager = PersonalityManager(personalities_dir=temp_personality_dir)
        
        # 验证初始化结果
        assert personality_manager.personalities_dir == temp_personality_dir
        assert isinstance(personality_manager.personalities, dict)

@pytest.mark.asyncio
async def test_ensure_dir_exists(temp_personality_dir, mock_config, mock_logger):
    # 测试确保目录存在的功能
    # 创建一个不存在的目录路径
    non_existent_dir = os.path.join(temp_personality_dir, "non_existent")
    
    with patch('os.path.exists', side_effect=lambda path: path != non_existent_dir):
        with patch('os.makedirs') as mock_makedirs:
            # 创建PersonalityManager实例
            personality_manager = PersonalityManager(personalities_dir=non_existent_dir)
            
            # 验证os.makedirs被调用
            mock_makedirs.assert_called_once_with(non_existent_dir)

@pytest.mark.asyncio
async def test_load_personalities(temp_personality_dir, mock_config, mock_logger):
    # 测试加载人格文件
    # 创建测试人格文件
    personality_data = {
        "id": "test_personality",
        "name": "测试人格",
        "system_prompt": "这是一个测试人格",
        "traits": ["测试", "示例"],
        "examples": ["用户: 你是谁？\n助手: 我是一个测试人格。"]
    }
    
    personality_file = os.path.join(temp_personality_dir, "test_personality.json")
    with open(personality_file, "w", encoding="utf-8") as f:
        json.dump(personality_data, f, ensure_ascii=False, indent=2)
    
    # 创建PersonalityManager实例
    personality_manager = PersonalityManager(personalities_dir=temp_personality_dir)
    
    # 验证人格加载成功
    assert "test_personality" in personality_manager.personalities
    loaded_personality = personality_manager.personalities["test_personality"]
    assert loaded_personality.id == "test_personality"
    assert loaded_personality.name == "测试人格"
    assert loaded_personality.system_prompt == "这是一个测试人格"

@pytest.mark.asyncio
async def test_load_default_personalities(temp_personality_dir, mock_config, mock_logger):
    # 测试加载默认人格
    # 模拟os.listdir返回空列表，表示没有人格文件
    with patch('os.listdir', return_value=[]):
        with patch('core.personality_manager.PersonalityManager.save_personality') as mock_save:
            # 创建PersonalityManager实例
            personality_manager = PersonalityManager(personalities_dir=temp_personality_dir)
            
            # 验证加载了默认人格
            assert "professional" in personality_manager.personalities
            assert "friendly" in personality_manager.personalities
            # 验证保存了默认人格
            assert mock_save.call_count == 2

@pytest.mark.asyncio
async def test_add_personality(temp_personality_dir, mock_config, mock_logger):
    # 测试添加人格
    personality_manager = PersonalityManager(personalities_dir=temp_personality_dir)
    
    # 创建一个新的人格
    new_personality = Personality(
        id="new_personality",
        name="新人格",
        system_prompt="这是一个新人格",
        traits=["新", "创新"],
        examples=["用户: 你好\n助手: 你好！我是新人格。"]
    )
    
    # 添加人格
    personality_manager.add_personality(new_personality)
    
    # 验证人格添加成功
    assert "new_personality" in personality_manager.personalities
    assert personality_manager.personalities["new_personality"] == new_personality

@pytest.mark.asyncio
async def test_get_personality(temp_personality_dir, mock_config, mock_logger):
    # 测试获取人格
    personality_manager = PersonalityManager(personalities_dir=temp_personality_dir)
    
    # 创建一个新的人格
    new_personality = Personality(
        id="test_id",
        name="测试人格",
        system_prompt="这是一个测试人格",
        traits=["测试"],
        examples=[]
    )
    
    # 添加人格
    personality_manager.add_personality(new_personality)
    
    # 获取存在的人格
    retrieved_personality = personality_manager.get_personality("test_id")
    assert retrieved_personality == new_personality
    
    # 获取不存在的人格
    non_existent_personality = personality_manager.get_personality("non_existent")
    assert non_existent_personality is None

@pytest.mark.asyncio
async def test_save_personality(temp_personality_dir, mock_config, mock_logger):
    # 测试保存人格
    personality_manager = PersonalityManager(personalities_dir=temp_personality_dir)
    
    # 创建一个新的人格
    new_personality = Personality(
        id="save_test",
        name="保存测试人格",
        system_prompt="这是一个保存测试人格",
        traits=["保存", "测试"],
        examples=[]
    )
    
    # 保存人格
    personality_manager.save_personality(new_personality)
    
    # 验证文件是否创建
    personality_file = os.path.join(temp_personality_dir, "save_test.json")
    assert os.path.exists(personality_file)
    
    # 验证文件内容
    with open(personality_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
        assert saved_data["id"] == "save_test"
        assert saved_data["name"] == "保存测试人格"

@pytest.mark.asyncio
async def test_list_personalities(temp_personality_dir, mock_config, mock_logger):
    # 测试列出人格
    personality_manager = PersonalityManager(personalities_dir=temp_personality_dir)
    
    # 清空默认加载的人格
    personality_manager.personalities = {}
    
    # 创建几个人格
    personality1 = Personality(
        id="person1",
        name="人格1",
        system_prompt="这是人格1",
        traits=[],
        examples=[]
    )
    
    personality2 = Personality(
        id="person2",
        name="人格2",
        system_prompt="这是人格2",
        traits=[],
        examples=[]
    )
    
    # 添加人格
    personality_manager.add_personality(personality1)
    personality_manager.add_personality(personality2)
    
    # 列出人格
    personalities_list = personality_manager.list_personalities()
    
    # 验证结果
    assert len(personalities_list) == 2
    # 验证是否包含我们添加的人格
    assert {"id": "person1", "name": "人格1"} in personalities_list
    assert {"id": "person2", "name": "人格2"} in personalities_list

@pytest.mark.asyncio
async def test_apply_personality(temp_personality_dir, mock_config, mock_logger):
    # 测试应用人格到消息列表
    personality_manager = PersonalityManager(personalities_dir=temp_personality_dir)
    
    # 创建一个人格
    test_personality = Personality(
        id="apply_test",
        name="应用测试人格",
        system_prompt="这是应用测试的系统提示词",
        traits=[],
        examples=[]
    )
    
    # 添加人格
    personality_manager.add_personality(test_personality)
    
    # 创建消息列表
    messages = [
        {"role": "user", "content": "你好！"}
    ]
    
    # 应用人格
    messages_with_personality = personality_manager.apply_personality(messages, "apply_test")
    
    # 验证结果
    assert len(messages_with_personality) == 2
    assert messages_with_personality[0]["role"] == "system"
    assert messages_with_personality[0]["content"] == "这是应用测试的系统提示词"
    assert messages_with_personality[1] == messages[0]

@pytest.mark.asyncio
async def test_apply_non_existent_personality(temp_personality_dir, mock_config, mock_logger):
    # 测试应用不存在的人格
    personality_manager = PersonalityManager(personalities_dir=temp_personality_dir)
    
    # 准备消息
    messages = [{"role": "user", "content": "你好"}]
    
    # 应用不存在的人格
    result = personality_manager.apply_personality(messages, "non_existent")
    
    # 验证结果
    assert result == messages  # 应该返回原始消息
    # 验证警告日志
    mock_logger.warning.assert_called_once_with("Personality non_existent not found, using default")

@pytest.mark.asyncio
async def test_load_personality_invalid_json(temp_personality_dir, mock_config, mock_logger):
    # 测试加载无效的JSON文件
    # 创建一个无效的JSON文件
    invalid_file = os.path.join(temp_personality_dir, "invalid.json")
    with open(invalid_file, "w", encoding="utf-8") as f:
        f.write("{invalid json}")
    
    # 创建PersonalityManager实例
    personality_manager = PersonalityManager(personalities_dir=temp_personality_dir)
    
    # 验证日志中有错误记录
    mock_logger.error.assert_called_once()
    assert "Failed to load personality from" in mock_logger.error.call_args[0][0]

@pytest.mark.asyncio
async def test_load_personality_validation_error(temp_personality_dir, mock_config, mock_logger):
    # 测试加载验证失败的人格文件
    # 创建一个缺少必要字段的JSON文件
    invalid_data = {
        "name": "缺少ID的人格",
        "system_prompt": "这是一个缺少ID的人格"
    }
    
    invalid_file = os.path.join(temp_personality_dir, "invalid_validation.json")
    with open(invalid_file, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f, ensure_ascii=False, indent=2)
    
    # 创建PersonalityManager实例
    personality_manager = PersonalityManager(personalities_dir=temp_personality_dir)
    
    # 验证日志中有错误记录
    mock_logger.error.assert_called_once()
    assert "Failed to load personality from" in mock_logger.error.call_args[0][0]