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
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters
                }
            }
        }