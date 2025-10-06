from services.tools.registry import tool_registry
from utils.log import log
from typing import List, Dict, Any


def get_available_tools() -> List[Dict[str, Any]]:
    """获取所有可用的工具列表，用于OpenAI API的tools参数
    
    Returns:
        List[Dict[str, Any]]: 工具函数模式列表，格式符合OpenAI API要求
    """
    try:
        # 使用tool_registry获取所有工具的函数调用模式
        return tool_registry.get_functions_schema()
    except Exception as e:
        log.error(f"获取可用工具失败: {e}")
        # 发生错误时返回空列表
        return []