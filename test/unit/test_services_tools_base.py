"""
services/tools/base.py tests
Tests the Tool base class functionality
"""
import pytest
from unittest.mock import AsyncMock

from services.tools.base import Tool


class ConcreteTool(Tool):
    """Concrete implementation of Tool for testing"""
    tool_type = "test"
    
    def __init__(self, name="test_tool", description="Test tool", tool_type="test"):
        self._name = name
        self._description = description
        if tool_type != "test":
            self.tool_type = tool_type
        self._parameters = {
            "param1": {"type": "string", "description": "First parameter"},
            "param2": {"type": "integer", "description": "Second parameter"}
        }
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def parameters(self) -> dict:
        return self._parameters
    
    async def execute(self, params: dict) -> dict:
        return {"result": "success", "params": params}


class TestTool:
    def test_tool_initialization(self):
        """Test Tool initialization"""
        tool = ConcreteTool()
        assert tool.name == "test_tool"
        assert tool.description == "Test tool"
        assert tool.tool_type == "test"

    def test_tool_custom_initialization(self):
        """Test Tool with custom values"""
        tool = ConcreteTool(
            name="custom_tool",
            description="Custom tool description",
            tool_type="custom"
        )
        assert tool.name == "custom_tool"
        assert tool.description == "Custom tool description"
        assert tool.tool_type == "custom"

    def test_tool_parameters(self):
        """Test Tool parameters property"""
        tool = ConcreteTool()
        params = tool.parameters
        
        assert isinstance(params, dict)
        assert "param1" in params
        assert "param2" in params
        assert params["param1"]["type"] == "string"
        assert params["param2"]["type"] == "integer"

    @pytest.mark.asyncio
    async def test_tool_execute(self):
        """Test Tool execute method"""
        tool = ConcreteTool()
        
        result = await tool.execute({"param1": "value1", "param2": 42})
        
        assert result["result"] == "success"
        assert result["params"]["param1"] == "value1"
        assert result["params"]["param2"] == 42

    def test_to_function_call_schema_basic(self):
        """Test to_function_call_schema with basic parameters"""
        tool = ConcreteTool()
        
        schema = tool.to_function_call_schema()
        
        assert schema["type"] == "function"
        assert "function" in schema
        assert schema["function"]["name"] == "test_tool"
        assert schema["function"]["description"] == "Test tool"
        assert "parameters" in schema["function"]
        
        params_schema = schema["function"]["parameters"]
        assert params_schema["type"] == "object"
        assert "properties" in params_schema
        assert "param1" in params_schema["properties"]
        assert "param2" in params_schema["properties"]

    def test_to_function_call_schema_with_complete_schema(self):
        """Test to_function_call_schema with complete schema in parameters"""
        class CompleteSchemaTool(Tool):
            def __init__(self):
                self._name = "complete_tool"
                self._description = "Complete tool"
                self._parameters = {
                    "type": "object",
                    "properties": {
                        "param": {"type": "string", "description": "Parameter"}
                    },
                    "required": ["param"]
                }
            
            @property
            def name(self) -> str:
                return self._name
            
            @property
            def description(self) -> str:
                return self._description
            
            @property
            def parameters(self) -> dict:
                return self._parameters
            
            async def execute(self, params: dict) -> dict:
                return {"result": "success"}
        
        tool = CompleteSchemaTool()
        schema = tool.to_function_call_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "complete_tool"
        assert schema["function"]["description"] == "Complete tool"
        
        params_schema = schema["function"]["parameters"]
        assert params_schema["type"] == "object"
        assert "required" in params_schema
        assert params_schema["required"] == ["param"]

    def test_to_function_call_schema_with_empty_parameters(self):
        """Test to_function_call_schema with empty parameters"""
        class EmptyParamsTool(Tool):
            def __init__(self):
                self._name = "empty_tool"
                self._description = "Empty tool"
                self._parameters = {}
            
            @property
            def name(self) -> str:
                return self._name
            
            @property
            def description(self) -> str:
                return self._description
            
            @property
            def parameters(self) -> dict:
                return self._parameters
            
            async def execute(self, params: dict) -> dict:
                return {"result": "success"}
        
        tool = EmptyParamsTool()
        schema = tool.to_function_call_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "empty_tool"
        
        params_schema = schema["function"]["parameters"]
        assert params_schema["type"] == "object"
        assert params_schema["properties"] == {}
        assert params_schema["required"] == []

    def test_to_function_call_schema_with_none_parameters(self):
        """Test to_function_call_schema with None parameters"""
        class NoneParamsTool(Tool):
            def __init__(self):
                self._name = "none_tool"
                self._description = "None tool"
                self._parameters = None
            
            @property
            def name(self) -> str:
                return self._name
            
            @property
            def description(self) -> str:
                return self._description
            
            @property
            def parameters(self) -> dict:
                return self._parameters
            
            async def execute(self, params: dict) -> dict:
                return {"result": "success"}
        
        tool = NoneParamsTool()
        schema = tool.to_function_call_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "none_tool"
        
        params_schema = schema["function"]["parameters"]
        assert params_schema["type"] == "object"
        assert params_schema["properties"] == {}
        assert params_schema["required"] == []

    def test_tool_type_default(self):
        """Test Tool type default value"""
        tool = ConcreteTool()
        assert tool.tool_type == "test"

    def test_tool_type_custom(self):
        """Test Tool type custom value"""
        tool = ConcreteTool(tool_type="custom_type")
        assert tool.tool_type == "custom_type"

    def test_tool_type_none(self):
        """Test Tool type None value"""
        tool = ConcreteTool(tool_type=None)
        assert tool.tool_type is None

    @pytest.mark.asyncio
    async def test_tool_execute_with_empty_params(self):
        """Test Tool execute with empty parameters"""
        tool = ConcreteTool()
        
        result = await tool.execute({})
        
        assert result["result"] == "success"
        assert result["params"] == {}

    @pytest.mark.asyncio
    async def test_tool_execute_with_complex_params(self):
        """Test Tool execute with complex parameters"""
        tool = ConcreteTool()
        
        complex_params = {
            "param1": "string_value",
            "param2": 123,
            "param3": [1, 2, 3],
            "param4": {"nested": "value"},
            "param5": True,
            "param6": None
        }
        
        result = await tool.execute(complex_params)
        
        assert result["result"] == "success"
        assert result["params"] == complex_params

    def test_tool_abstract_methods(self):
        """Test that Tool is abstract and cannot be instantiated directly"""
        with pytest.raises(TypeError):
            Tool()

    def test_tool_subclass_must_implement_abstract_methods(self):
        """Test that Tool subclasses must implement all abstract methods"""
        class IncompleteTool(Tool):
            @property
            def name(self) -> str:
                return "incomplete"
            
            @property
            def description(self) -> str:
                return "incomplete"
            
            # Missing parameters and execute methods
        
        with pytest.raises(TypeError):
            IncompleteTool()

    def test_tool_schema_structure(self):
        """Test that to_function_call_schema returns proper structure"""
        tool = ConcreteTool()
        schema = tool.to_function_call_schema()
        
        # Check top-level structure
        assert "type" in schema
        assert "function" in schema
        assert schema["type"] == "function"
        
        # Check function structure
        func = schema["function"]
        assert "name" in func
        assert "description" in func
        assert "parameters" in func
        
        # Check parameters structure
        params = func["parameters"]
        assert "type" in params
        assert "properties" in params
        assert "required" in params
        assert params["type"] == "object"
        assert isinstance(params["properties"], dict)
        assert isinstance(params["required"], list)
