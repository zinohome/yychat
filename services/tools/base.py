from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class Tool(ABC):
    # 添加工具类型属性，默认为None
    tool_type: Optional[str] = None
    
    @property
    @abstractmethod
    def name(self):
        pass
    
    @property
    @abstractmethod
    def description(self):
        pass
    
    @property
    @abstractmethod
    def parameters(self):
        pass
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]):
        pass
    
    def to_function_call_schema(self):
        # 如果 parameters 已经是完整的 schema（包含 type），直接使用
        # 否则包装成标准格式
        params = self.parameters
        if isinstance(params, dict) and "type" in params:
            # 已经是完整的 schema
            parameters_schema = params
        else:
            # 需要包装
            parameters_schema = {
                "type": "object",
                "properties": params if params else {},
                "required": []
            }
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters_schema
            }
        }