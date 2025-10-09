"""
services/tools/registry.py tests
Tests the ToolRegistry class functionality
"""
import pytest
from unittest.mock import MagicMock, patch

from services.tools.registry import ToolRegistry, tool_registry
from services.tools.base import Tool


class MockTool(Tool):
    """Mock tool for testing"""
    def __init__(self, name="mock_tool", tool_type=None):
        self._name = name
        self._tool_type = tool_type
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return "Mock tool for testing"
    
    @property
    def parameters(self) -> dict:
        return {
            "param": {"type": "string", "description": "Test parameter"}
        }
    
    @property
    def tool_type(self) -> str:
        return self._tool_type or "test"
    
    async def execute(self, params: dict) -> dict:
        return {"result": "mock_result"}


class TestToolRegistry:
    def test_tool_registry_initialization(self):
        """Test ToolRegistry initialization"""
        registry = ToolRegistry()
        assert registry._tools == {}
        assert registry._schema_cache is None
        assert registry._schema_dirty is False

    def test_register_valid_tool(self):
        """Test registering a valid tool"""
        registry = ToolRegistry()
        
        registry.register(MockTool)
        
        assert "mock_tool" in registry._tools
        assert registry._tools["mock_tool"] == MockTool
        assert registry._schema_dirty is True

    def test_register_invalid_tool(self):
        """Test registering an invalid tool (not Tool subclass)"""
        registry = ToolRegistry()
        
        class InvalidTool:
            pass
        
        with pytest.raises(TypeError, match="Only Tool subclasses can be registered"):
            registry.register(InvalidTool)

    def test_register_duplicate_tool(self):
        """Test registering a duplicate tool (should be skipped)"""
        registry = ToolRegistry()
        
        # Register first time
        registry.register(MockTool)
        assert "mock_tool" in registry._tools
        
        # Register second time (should be skipped)
        registry.register(MockTool)
        assert len(registry._tools) == 1
        assert "mock_tool" in registry._tools

    def test_get_tool_existing(self):
        """Test getting an existing tool"""
        registry = ToolRegistry()
        registry.register(MockTool)
        
        tool = registry.get_tool("mock_tool")
        
        assert tool is not None
        assert isinstance(tool, MockTool)
        assert tool.name == "mock_tool"

    def test_get_tool_nonexistent(self):
        """Test getting a nonexistent tool"""
        registry = ToolRegistry()
        
        tool = registry.get_tool("nonexistent_tool")
        
        assert tool is None

    def test_list_tools_all(self):
        """Test listing all tools"""
        registry = ToolRegistry()
        
        # Register multiple tools
        class Tool1(MockTool):
            tool_type = "type1"
            def __init__(self):
                super().__init__("tool1", "type1")
        
        class Tool2(MockTool):
            tool_type = "type2"
            def __init__(self):
                super().__init__("tool2", "type2")
        
        registry.register(Tool1)
        registry.register(Tool2)
        
        tools = registry.list_tools()
        
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools
        assert isinstance(tools["tool1"], Tool1)
        assert isinstance(tools["tool2"], Tool2)

    def test_list_tools_by_type(self):
        """Test listing tools by type"""
        registry = ToolRegistry()
        
        # Register tools with different types
        class Tool1(MockTool):
            tool_type = "type1"
            def __init__(self):
                super().__init__("tool1", "type1")
        
        class Tool2(MockTool):
            tool_type = "type2"
            def __init__(self):
                super().__init__("tool2", "type2")
        
        class Tool3(MockTool):
            tool_type = "type1"
            def __init__(self):
                super().__init__("tool3", "type1")
        
        registry.register(Tool1)
        registry.register(Tool2)
        registry.register(Tool3)
        
        # List tools of type1
        tools = registry.list_tools("type1")
        
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool3" in tools
        assert "tool2" not in tools

    def test_list_tools_by_nonexistent_type(self):
        """Test listing tools by nonexistent type"""
        registry = ToolRegistry()
        
        class Tool1(MockTool):
            tool_type = "type1"
            def __init__(self):
                super().__init__("tool1", "type1")
        
        registry.register(Tool1)
        
        tools = registry.list_tools("nonexistent_type")
        
        assert len(tools) == 0

    def test_get_functions_schema_no_cache(self):
        """Test getting functions schema without cache"""
        registry = ToolRegistry()
        
        class Tool1(MockTool):
            tool_type = "type1"
            def __init__(self):
                super().__init__("tool1", "type1")
        
        registry.register(Tool1)
        
        schema = registry.get_functions_schema()
        
        assert isinstance(schema, list)
        assert len(schema) == 1
        assert schema[0]["type"] == "function"
        assert schema[0]["function"]["name"] == "tool1"
        assert registry._schema_cache is not None
        assert registry._schema_dirty is False

    def test_get_functions_schema_with_cache(self):
        """Test getting functions schema with cache"""
        registry = ToolRegistry()
        
        class Tool1(MockTool):
            tool_type = "type1"
            def __init__(self):
                super().__init__("tool1", "type1")
        
        registry.register(Tool1)
        
        # First call - builds cache
        schema1 = registry.get_functions_schema()
        
        # Second call - uses cache
        schema2 = registry.get_functions_schema()
        
        assert schema1 == schema2
        assert registry._schema_cache is not None
        assert registry._schema_dirty is False

    def test_get_functions_schema_cache_invalidation(self):
        """Test schema cache invalidation"""
        registry = ToolRegistry()
        
        class Tool1(MockTool):
            tool_type = "type1"
            def __init__(self):
                super().__init__("tool1", "type1")
        
        registry.register(Tool1)
        
        # First call - builds cache
        schema1 = registry.get_functions_schema()
        
        # Register new tool - invalidates cache
        class Tool2(MockTool):
            tool_type = "type2"
            def __init__(self):
                super().__init__("tool2", "type2")
        
        registry.register(Tool2)
        assert registry._schema_dirty is True
        
        # Second call - rebuilds cache
        schema2 = registry.get_functions_schema()
        
        assert len(schema2) == 2
        assert registry._schema_dirty is False

    def test_get_functions_schema_by_type(self):
        """Test getting functions schema by type"""
        registry = ToolRegistry()
        
        class Tool1(MockTool):
            tool_type = "type1"
            def __init__(self):
                super().__init__("tool1", "type1")
        
        class Tool2(MockTool):
            tool_type = "type2"
            def __init__(self):
                super().__init__("tool2", "type2")
        
        registry.register(Tool1)
        registry.register(Tool2)
        
        # Get schema for type1 only
        schema = registry.get_functions_schema("type1")
        
        assert isinstance(schema, list)
        assert len(schema) == 1
        assert schema[0]["function"]["name"] == "tool1"
        
        # Cache should not be affected by type filtering
        assert registry._schema_cache is None

    def test_get_functions_schema_empty_registry(self):
        """Test getting functions schema from empty registry"""
        registry = ToolRegistry()
        
        schema = registry.get_functions_schema()
        
        assert schema == []

    def test_register_tool_with_custom_name(self):
        """Test registering tool with custom name"""
        registry = ToolRegistry()
        
        class CustomTool(MockTool):
            tool_type = "custom_type"
            def __init__(self):
                super().__init__("custom_tool", "custom_type")
        
        registry.register(CustomTool)
        
        tool = registry.get_tool("custom_tool")
        assert tool is not None
        assert tool.name == "custom_tool"
        assert tool.tool_type == "custom_type"

    def test_register_multiple_tools_same_type(self):
        """Test registering multiple tools with same type"""
        registry = ToolRegistry()
        
        class Tool1(MockTool):
            tool_type = "same_type"
            def __init__(self):
                super().__init__("tool1", "same_type")
        
        class Tool2(MockTool):
            tool_type = "same_type"
            def __init__(self):
                super().__init__("tool2", "same_type")
        
        registry.register(Tool1)
        registry.register(Tool2)
        
        tools = registry.list_tools("same_type")
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools

    def test_tool_without_tool_type_attribute(self):
        """Test tool without tool_type attribute"""
        registry = ToolRegistry()
        
        class ToolWithoutType(MockTool):
            def __init__(self):
                super().__init__("tool_without_type", None)
            
            @property
            def tool_type(self):
                # Simulate tool without tool_type attribute
                raise AttributeError("No tool_type")
        
        registry.register(ToolWithoutType)
        
        # Should not crash when listing tools
        tools = registry.list_tools("some_type")
        assert len(tools) == 0
        
        # Should still be able to get all tools
        all_tools = registry.list_tools()
        assert len(all_tools) == 1
        assert "tool_without_type" in all_tools


class TestGlobalToolRegistry:
    def test_global_tool_registry_instance(self):
        """Test global tool registry instance"""
        assert tool_registry is not None
        assert isinstance(tool_registry, ToolRegistry)

    def test_global_tool_registry_singleton(self):
        """Test that global tool registry is a singleton"""
        from services.tools.registry import tool_registry as registry1
        from services.tools.registry import tool_registry as registry2
        
        assert registry1 is registry2
        assert registry1 is tool_registry
