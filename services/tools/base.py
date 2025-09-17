from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypeVar, Generic

T = TypeVar('T')

class Tool(ABC, Generic[T]):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> T:
        pass
    
    @property
    def parameters(self) -> Dict[str, Any]:
        # 默认参数定义，可以在子类中覆盖
        return {}
    
    def to_function_call_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",  # 添加缺失的type字段
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": []
                }
            }
        }