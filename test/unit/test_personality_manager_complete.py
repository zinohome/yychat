"""
PersonalityManager完整测试
测试人格管理器的所有功能
"""
import pytest
import json
import os
import tempfile
import shutil
from core.personality_manager import PersonalityManager, Personality

class TestPersonalityManagerComplete:
    """PersonalityManager完整功能测试"""
    
    def test_personality_model(self):
        """测试Personality模型"""
        personality = Personality(
            id="test_p",
            name="测试人格",
            system_prompt="测试提示词",
            traits=["特质1", "特质2"],
            examples=["示例1"],
            allowed_tools=[{"tool_name": "calculator", "description": "计算器"}]
        )
        
        assert personality.id == "test_p"
        assert personality.name == "测试人格"
        assert len(personality.traits) == 2
        assert len(personality.allowed_tools) == 1
        print("✅ Personality模型测试通过")
    
    def test_personality_manager_initialization(self):
        """测试PersonalityManager初始化"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = PersonalityManager(personalities_dir=tmp_dir)
            
            assert manager is not None
            assert hasattr(manager, 'personalities')
            assert isinstance(manager.personalities, dict)
            print("✅ PersonalityManager初始化成功")
    
    def test_load_default_personalities(self):
        """测试加载默认人格"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = PersonalityManager(personalities_dir=tmp_dir)
            
            # 应该加载了默认人格
            assert len(manager.personalities) > 0
            assert "professional" in manager.personalities
            assert "friendly" in manager.personalities
            print(f"✅ 加载了{len(manager.personalities)}个默认人格")
    
    def test_add_personality(self):
        """测试添加人格"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = PersonalityManager(personalities_dir=tmp_dir)
            
            new_personality = Personality(
                id="custom",
                name="自定义",
                system_prompt="自定义提示"
            )
            
            manager.add_personality(new_personality)
            
            assert "custom" in manager.personalities
            assert manager.personalities["custom"].name == "自定义"
            print("✅ 添加人格成功")
    
    def test_get_personality(self):
        """测试获取人格"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = PersonalityManager(personalities_dir=tmp_dir)
            
            # 获取存在的人格
            personality = manager.get_personality("professional")
            assert personality is not None
            assert personality.id == "professional"
            
            # 获取不存在的人格
            none_personality = manager.get_personality("nonexistent")
            assert none_personality is None
            
            print("✅ 获取人格功能正确")
    
    def test_save_personality(self):
        """测试保存人格"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = PersonalityManager(personalities_dir=tmp_dir)
            
            test_personality = Personality(
                id="save_test",
                name="保存测试",
                system_prompt="测试保存功能"
            )
            
            manager.add_personality(test_personality)
            manager.save_personality(test_personality)
            
            # 验证文件已创建
            file_path = os.path.join(tmp_dir, "save_test.json")
            assert os.path.exists(file_path)
            
            # 验证文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert data['id'] == 'save_test'
                assert data['name'] == '保存测试'
            
            print("✅ 保存人格成功")
    
    def test_list_personalities(self):
        """测试列出所有人格"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = PersonalityManager(personalities_dir=tmp_dir)
            
            personalities_list = manager.list_personalities()
            
            assert isinstance(personalities_list, list)
            assert len(personalities_list) > 0
            
            # 检查列表项格式
            for item in personalities_list:
                assert "id" in item
                assert "name" in item
            
            print(f"✅ 列出{len(personalities_list)}个人格")
    
    def test_apply_personality(self):
        """测试应用人格"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = PersonalityManager(personalities_dir=tmp_dir)
            
            messages = [
                {"role": "user", "content": "Hello"}
            ]
            
            # 应用存在的人格
            result = manager.apply_personality(messages, "professional")
            
            assert len(result) == 2  # system + user
            assert result[0]["role"] == "system"
            assert "专业" in result[0]["content"]
            assert result[1] == messages[0]
            
            print("✅ 应用人格成功")
    
    def test_apply_nonexistent_personality(self):
        """测试应用不存在的人格"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = PersonalityManager(personalities_dir=tmp_dir)
            
            messages = [{"role": "user", "content": "Test"}]
            
            # 应用不存在的人格应该返回原消息
            result = manager.apply_personality(messages, "nonexistent_999")
            
            assert result == messages
            print("✅ 不存在的人格处理正确")
    
    def test_apply_personality_with_tools(self):
        """测试应用带工具规则的人格"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = PersonalityManager(personalities_dir=tmp_dir)
            
            # 创建带工具的人格
            tool_personality = Personality(
                id="with_tools",
                name="工具人格",
                system_prompt="你可以使用工具",
                allowed_tools=[
                    {"tool_name": "calculator", "description": "用于数学计算"},
                    {"tool_name": "search", "description": "用于搜索信息"}
                ]
            )
            
            manager.add_personality(tool_personality)
            
            messages = [{"role": "user", "content": "Help me"}]
            result = manager.apply_personality(messages, "with_tools")
            
            assert len(result) == 2
            assert "工具使用规则" in result[0]["content"]
            assert "数学计算" in result[0]["content"]
            assert "搜索信息" in result[0]["content"]
            
            print("✅ 带工具规则的人格应用成功")
    
    def test_load_from_file(self):
        """测试从文件加载人格"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 创建一个人格文件
            personality_data = {
                "id": "file_test",
                "name": "文件测试",
                "system_prompt": "从文件加载",
                "traits": ["trait1"],
                "examples": [],
                "allowed_tools": []
            }
            
            file_path = os.path.join(tmp_dir, "file_test.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(personality_data, f, ensure_ascii=False)
            
            # 创建manager（应该自动加载文件）
            manager = PersonalityManager(personalities_dir=tmp_dir)
            
            # 验证加载成功
            assert "file_test" in manager.personalities
            personality = manager.get_personality("file_test")
            assert personality.name == "文件测试"
            
            print("✅ 从文件加载人格成功")
    
    def test_load_invalid_json(self):
        """测试加载无效JSON文件"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 创建无效JSON文件
            invalid_file = os.path.join(tmp_dir, "invalid.json")
            with open(invalid_file, 'w') as f:
                f.write("{invalid json")
            
            # 应该能处理错误并继续
            manager = PersonalityManager(personalities_dir=tmp_dir)
            
            # 应该只有默认人格
            assert len(manager.personalities) >= 2
            print("✅ 无效JSON文件处理正确")
    
    def test_personality_with_empty_fields(self):
        """测试空字段的人格"""
        personality = Personality(
            id="minimal",
            name="最小人格",
            system_prompt="最小提示"
        )
        
        assert personality.traits == []
        assert personality.examples == []
        assert personality.allowed_tools == []
        print("✅ 空字段人格创建成功")
    
    def test_directory_creation(self):
        """测试目录自动创建"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            non_existent_dir = os.path.join(tmp_dir, "new_dir")
            
            # 目录不存在
            assert not os.path.exists(non_existent_dir)
            
            # 创建manager应该自动创建目录
            manager = PersonalityManager(personalities_dir=non_existent_dir)
            
            # 目录应该被创建
            assert os.path.exists(non_existent_dir)
            print("✅ 目录自动创建成功")
    
    def test_personality_update(self):
        """测试更新人格"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = PersonalityManager(personalities_dir=tmp_dir)
            
            # 添加初始人格
            initial = Personality(
                id="update_test",
                name="初始名称",
                system_prompt="初始提示"
            )
            manager.add_personality(initial)
            
            # 更新人格
            updated = Personality(
                id="update_test",
                name="更新后名称",
                system_prompt="更新后提示"
            )
            manager.add_personality(updated)
            
            # 验证更新
            result = manager.get_personality("update_test")
            assert result.name == "更新后名称"
            assert result.system_prompt == "更新后提示"
            
            print("✅ 人格更新成功")
    
    def test_multiple_personalities(self):
        """测试多个人格管理"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = PersonalityManager(personalities_dir=tmp_dir)
            
            # 添加多个自定义人格
            for i in range(5):
                p = Personality(
                    id=f"test_{i}",
                    name=f"测试{i}",
                    system_prompt=f"提示{i}"
                )
                manager.add_personality(p)
            
            # 验证所有人格都存在
            personalities = manager.list_personalities()
            test_personalities = [p for p in personalities if p['id'].startswith('test_')]
            
            assert len(test_personalities) == 5
            print(f"✅ 成功管理{len(personalities)}个人格")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
