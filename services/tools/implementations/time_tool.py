from typing import Dict, Any
from datetime import datetime
import pytz
from ..base import Tool
from ..registry import tool_registry

class TimeTool(Tool):
    @property
    def name(self) -> str:
        return "gettime"
    
    @property
    def description(self) -> str:
        return "获取上海时区（UTC+8）的当前时间，以年月日时分秒的形式返回"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        # 这个工具不需要参数，但需要返回符合 OpenAI schema 的空参数定义
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # 获取上海时区的当前时间
        shanghai_tz = pytz.timezone('Asia/Shanghai')
        current_time = datetime.now(shanghai_tz)
        
        # 格式化为年月日时分秒形式
        formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            "current_time": formatted_time,
            "timezone": "Asia/Shanghai (UTC+8)",
            "timestamp": current_time.timestamp()
        }

# 注册工具（传入类，不是实例）
tool_registry.register(TimeTool)