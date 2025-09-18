import pytest
import os
import importlib
import inspect
from unittest.mock import patch, MagicMock, mock_open
from services.tools.discovery import ToolDiscoverer
from services.tools.base import Tool
from services.tools.registry import tool_registry

# 测试ToolDiscoverer.discover_tools方法
@patch('services.tools.discovery.os.listdir')
@patch('services.tools.discovery.importlib.import_module')
@patch('services.tools.discovery.inspect.getmembers')
@patch('services.tools.discovery.os.path.abspath')
def test_tool_discoverer_discover_tools(mock_abspath, mock_getmembers, mock_import_module, mock_listdir):
    # 配置mock返回值
    mock_abspath.return_value = "/fake/path"
    mock_listdir.return_value = ["tool1.py", "tool2.py", "__init__.py", "not_a_tool.txt"]
    
    # 创建模拟工具类
    class MockTool1(Tool):
        @property
        def name(self):
            return "mock_tool_1"
        
        @property
        def description(self):
            return "Mock tool 1"
        
        @property
        def parameters(self):
            return {}
        
        async def execute(self, params):
            return "Result 1"
    
    class MockTool2(Tool):
        @property
        def name(self):
            return "mock_tool_2"
        
        @property
        def description(self):
            return "Mock tool 2"
        
        @property
        def parameters(self):
            return {}
        
        async def execute(self, params):
            return "Result 2"
    
    # 配置mock_import_module返回包含工具类的模块
    mock_module1 = MagicMock()
    mock_module1.__name__ = "services.tools.implementations.tool1"
    mock_module2 = MagicMock()
    mock_module2.__name__ = "services.tools.implementations.tool2"
    
    mock_import_module.side_effect = [mock_module1, mock_module2]
    
    # 配置mock_getmembers返回工具类
    mock_getmembers.side_effect = [
        [("MockTool1", MockTool1), ("SomeOtherClass", MagicMock())],
        [("MockTool2", MockTool2)]
    ]
    
    # 配置inspect.isclass
    with patch('inspect.isclass', side_effect=lambda x: x in [MockTool1, MockTool2, MagicMock()]):
        # 执行discover_tools
        tools = ToolDiscoverer.discover_tools("/some/directory")
        
        # 验证结果
        assert len(tools) == 2
        assert MockTool1 in tools
        assert MockTool2 in tools
        
        # 验证调用参数
        mock_abspath.assert_called_once_with("/some/directory")
        mock_listdir.assert_called_once_with("/fake/path")
        assert mock_import_module.call_count == 2
        mock_import_module.assert_any_call("services.tools.implementations.tool1")
        mock_import_module.assert_any_call("services.tools.implementations.tool2")

# 测试ToolDiscoverer.discover_tools方法 - 导入异常
@patch('services.tools.discovery.os.listdir')
@patch('services.tools.discovery.importlib.import_module')
@patch('services.tools.discovery.os.path.abspath')
def test_tool_discoverer_discover_tools_import_error(mock_abspath, mock_import_module, mock_listdir):
    # 配置mock返回值
    mock_abspath.return_value = "/fake/path"
    mock_listdir.return_value = ["tool1.py"]
    
    # 配置mock_import_module抛出异常
    mock_import_module.side_effect = Exception("Import error")
    
    # 执行discover_tools
    tools = ToolDiscoverer.discover_tools("/some/directory")
    
    # 验证结果是空列表
    assert len(tools) == 0

# 测试ToolDiscoverer.register_discovered_tools方法
@patch('services.tools.discovery.ToolDiscoverer.discover_tools')
@patch('services.tools.registry.tool_registry.register')
@patch('os.path.join')
@patch('os.path.dirname')
def test_tool_discoverer_register_discovered_tools(mock_dirname, mock_join, mock_register, mock_discover_tools):
    # 创建模拟工具类
    class MockTool1(Tool):
        @property
        def name(self):
            return "mock_tool_1"
        
        @property
        def description(self):
            return "Mock tool 1"
        
        @property
        def parameters(self):
            return {}
        
        async def execute(self, params):
            return "Result 1"
    
    class MockTool2(Tool):
        @property
        def name(self):
            return "mock_tool_2"
        
        @property
        def description(self):
            return "Mock tool 2"
        
        @property
        def parameters(self):
            return {}
        
        async def execute(self, params):
            return "Result 2"
    
    # 配置mock返回值
    mock_discover_tools.return_value = [MockTool1, MockTool2]
    mock_dirname.return_value = "/path/to/services/tools"
    mock_join.return_value = "/path/to/services/tools/implementations"
    
    # 执行register_discovered_tools
    count = ToolDiscoverer.register_discovered_tools()
    
    # 验证结果
    assert count == 2
    mock_discover_tools.assert_called_once_with("/path/to/services/tools/implementations")
    assert mock_register.call_count == 2
    mock_register.assert_any_call(MockTool1)
    mock_register.assert_any_call(MockTool2)

# 测试ToolDiscoverer.register_discovered_tools方法 - 指定目录
@patch('services.tools.discovery.ToolDiscoverer.discover_tools')
@patch('services.tools.registry.tool_registry.register')
def test_tool_discoverer_register_discovered_tools_with_directory(mock_register, mock_discover_tools):
    # 配置mock返回值
    mock_discover_tools.return_value = []
    
    # 执行register_discovered_tools并指定目录
    count = ToolDiscoverer.register_discovered_tools("/custom/directory")
    
    # 验证结果
    assert count == 0
    mock_discover_tools.assert_called_once_with("/custom/directory")
    mock_register.assert_not_called()

# 测试ToolDiscoverer.register_discovered_tools方法 - 空目录
@patch('services.tools.discovery.ToolDiscoverer.discover_tools')
@patch('services.tools.registry.tool_registry.register')
@patch('os.path.join')
@patch('os.path.dirname')
def test_tool_discoverer_register_discovered_tools_empty_directory(mock_dirname, mock_join, mock_register, mock_discover_tools):
    # 配置mock返回值
    mock_discover_tools.return_value = []
    mock_dirname.return_value = "/path/to/services/tools"
    mock_join.return_value = "/path/to/services/tools/implementations"
    
    # 执行register_discovered_tools
    count = ToolDiscoverer.register_discovered_tools()
    
    # 验证结果
    assert count == 0
    mock_discover_tools.assert_called_once_with("/path/to/services/tools/implementations")
    mock_register.assert_not_called()