"""
记忆系统适配器
复用现有记忆系统，为实时语音提供记忆功能
"""

from typing import List, Dict, Any, Optional
from utils.log import log


class MemoryAdapter:
    """记忆系统适配器"""
    
    def __init__(self):
        """初始化记忆适配器"""
        try:
            from core.chat_memory import get_async_chat_memory
            self.memory = get_async_chat_memory()
            log.info("记忆适配器初始化成功")
        except Exception as e:
            log.error(f"记忆适配器初始化失败: {e}")
            self.memory = None
    
    async def get_relevant_memory(self, conversation_id: str, query: str) -> List[str]:
        """
        获取相关记忆
        
        Args:
            conversation_id: 对话ID
            query: 查询内容
            
        Returns:
            List[str]: 相关记忆列表
        """
        try:
            if not self.memory:
                log.warning("记忆系统未初始化，返回空记忆")
                return []
            
            # 复用现有记忆检索功能
            memories = await self.memory.get_relevant_memory(conversation_id, query)
            
            # 转换为字符串列表
            if isinstance(memories, list):
                memory_strings = [str(memory) for memory in memories]
            else:
                memory_strings = [str(memories)] if memories else []
            
            log.debug(f"记忆适配器检索到 {len(memory_strings)} 条相关记忆")
            return memory_strings
            
        except Exception as e:
            log.error(f"获取相关记忆失败: {e}")
            return []
    
    async def save_memory(self, conversation_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        保存记忆
        
        Args:
            conversation_id: 对话ID
            content: 记忆内容
            metadata: 元数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if not self.memory:
                log.warning("记忆系统未初始化，无法保存记忆")
                return False
            
            # 复用现有记忆保存功能
            result = await self.memory.save_memory(conversation_id, content, metadata)
            
            log.debug(f"记忆适配器保存记忆成功: {conversation_id}")
            return result
            
        except Exception as e:
            log.error(f"保存记忆失败: {e}")
            return False
    
    async def get_memory_stats(self, conversation_id: str) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            Dict[str, Any]: 记忆统计信息
        """
        try:
            if not self.memory:
                return {"total_memories": 0, "last_updated": None}
            
            # 这里可以添加更多统计信息的获取逻辑
            return {
                "total_memories": 0,  # 暂时返回0，后续可以扩展
                "last_updated": None
            }
            
        except Exception as e:
            log.error(f"获取记忆统计信息失败: {e}")
            return {"total_memories": 0, "last_updated": None}
    
    def is_available(self) -> bool:
        """
        检查记忆系统是否可用
        
        Returns:
            bool: 是否可用
        """
        return self.memory is not None


# 全局记忆适配器实例
memory_adapter = MemoryAdapter()
