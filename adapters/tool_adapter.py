"""
工具调用系统适配器
复用现有工具系统，为实时语音提供工具调用功能
"""

from typing import List, Dict, Any, Optional
from utils.log import log


class ToolAdapter:
    """工具调用系统适配器"""
    
    def __init__(self):
        """初始化工具适配器"""
        try:
            from services.tools.manager import ToolManager
            self.tool_manager = ToolManager()
            log.info("工具适配器初始化成功")
        except Exception as e:
            log.error(f"工具适配器初始化失败: {e}")
            self.tool_manager = None
    
    async def get_tools_for_realtime(self, personality_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取实时语音专用工具列表
        
        Args:
            personality_id: 人格ID，用于过滤工具
            
        Returns:
            List[Dict[str, Any]]: 实时语音工具列表
        """
        try:
            if not self.tool_manager:
                log.warning("工具系统未初始化，返回空工具列表")
                return []
            
            # 复用现有工具系统
            all_tools = await self.tool_manager.get_available_tools()
            
            # 根据人格过滤工具
            if personality_id and hasattr(self.tool_manager, 'get_allowed_tools'):
                try:
                    # 尝试获取人格允许的工具
                    allowed_tools = await self.tool_manager.get_allowed_tools(personality_id)
                    if allowed_tools:
                        all_tools = allowed_tools
                except Exception as e:
                    log.warning(f"获取人格允许的工具失败: {e}")
            
            # 转换为实时语音专用格式
            realtime_tools = self._convert_to_realtime_format(all_tools)
            
            log.debug(f"工具适配器获取到 {len(realtime_tools)} 个工具")
            return realtime_tools
            
        except Exception as e:
            log.error(f"获取工具列表失败: {e}")
            return []
    
    def _convert_to_realtime_format(self, tools: List[Any]) -> List[Dict[str, Any]]:
        """
        转换为实时语音专用格式
        
        Args:
            tools: 工具列表
            
        Returns:
            List[Dict[str, Any]]: 实时语音格式的工具列表
        """
        realtime_tools = []
        
        try:
            for tool in tools:
                # 获取工具基本信息
                name = getattr(tool, 'name', '') or ''
                description = getattr(tool, 'description', '') or ''
                parameters = getattr(tool, 'parameters', {}) or {}
                
                # 转换为OpenAI Realtime API格式
                realtime_tool = {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": parameters
                    }
                }
                
                realtime_tools.append(realtime_tool)
                
        except Exception as e:
            log.error(f"转换工具格式失败: {e}")
        
        return realtime_tools
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具调用
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            if not self.tool_manager:
                return {
                    "success": False,
                    "error": "工具系统未初始化"
                }
            
            # 复用现有工具执行功能
            result = await self.tool_manager.execute_tool(tool_name, parameters)
            
            log.debug(f"工具适配器执行工具成功: {tool_name}")
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            log.error(f"执行工具失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[Dict[str, Any]]: 工具信息
        """
        try:
            if not self.tool_manager:
                return None
            
            # 这里可以添加获取特定工具信息的逻辑
            # 暂时返回None，后续可以扩展
            return None
            
        except Exception as e:
            log.error(f"获取工具信息失败: {e}")
            return None
    
    def is_available(self) -> bool:
        """
        检查工具系统是否可用
        
        Returns:
            bool: 是否可用
        """
        return self.tool_manager is not None


# 全局工具适配器实例
tool_adapter = ToolAdapter()
