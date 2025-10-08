"""
统一引擎基类
提供所有聊天引擎必须实现的标准接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, AsyncGenerator


class BaseEngine(ABC):
    """
    统一的聊天引擎基类
    
    所有引擎（ChatEngine, Mem0ChatEngine等）都应继承此基类并实现所有抽象方法
    这样可以确保引擎间接口一致，便于切换和维护
    """
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        conversation_id: str = "default",
        personality_id: Optional[str] = None,
        use_tools: Optional[bool] = None,
        stream: Optional[bool] = None
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """
        生成响应 - 核心方法
        
        Args:
            messages: 消息历史，格式为 [{"role": "user", "content": "..."}, ...]
            conversation_id: 会话ID，用于Memory检索和管理
            personality_id: 人格ID，决定系统提示词和工具限制
            use_tools: 是否使用工具，None表示使用配置默认值
            stream: 是否流式响应，None表示使用配置默认值
            
        Returns:
            非流式: Dict[str, Any] - {"role": "assistant", "content": "..."}
            流式: AsyncGenerator[Dict[str, Any], None] - 异步生成器，逐块yield数据
            
        Raises:
            ValueError: 输入参数无效
            Exception: 生成响应过程中的其他错误
        """
        pass
    
    @abstractmethod
    async def get_engine_info(self) -> Dict[str, Any]:
        """
        获取引擎信息
        
        返回引擎的基本信息，用于监控和调试
        
        Returns:
            Dict包含以下字段:
            {
                "name": str,           # 引擎名称，如 "chat_engine"
                "version": str,        # 版本号，如 "1.0.0"
                "features": List[str], # 支持的特性，如 ["memory", "tools", "personality"]
                "status": str,         # 状态，如 "healthy", "degraded", "unhealthy"
                "description": str     # 简短描述
            }
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        检查引擎及其依赖服务的健康状态
        
        Returns:
            Dict包含以下字段:
            {
                "healthy": bool,           # 总体是否健康
                "timestamp": float,        # 检查时间戳
                "details": {               # 详细信息
                    "openai_api": bool,    # OpenAI API是否可用
                    "memory_system": bool, # Memory系统是否可用
                    "tool_system": bool,   # 工具系统是否可用
                    "personality_system": bool  # 人格系统是否可用
                },
                "errors": List[str]        # 错误信息列表（如果有）
            }
        """
        pass
    
    @abstractmethod
    async def clear_conversation_memory(self, conversation_id: str) -> Dict[str, Any]:
        """
        清除指定会话的记忆
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            Dict包含以下字段:
            {
                "success": bool,       # 是否成功
                "conversation_id": str, # 会话ID
                "deleted_count": int,  # 删除的记忆条数
                "message": str         # 操作消息
            }
        """
        pass
    
    @abstractmethod
    async def get_conversation_memory(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取指定会话的记忆
        
        Args:
            conversation_id: 会话ID
            limit: 限制返回数量，None表示返回所有
            
        Returns:
            Dict包含以下字段:
            {
                "success": bool,           # 是否成功
                "conversation_id": str,    # 会话ID
                "memories": List[Dict],    # 记忆列表
                "total_count": int,        # 总记忆数
                "returned_count": int      # 本次返回数
            }
        """
        pass
    
    @abstractmethod
    async def get_supported_personalities(self) -> List[Dict[str, Any]]:
        """
        获取支持的人格列表
        
        Returns:
            List[Dict]，每个Dict包含:
            {
                "id": str,              # 人格ID
                "name": str,            # 人格名称
                "description": str,     # 人格描述
                "allowed_tools": List[str]  # 允许使用的工具
            }
        """
        pass
    
    @abstractmethod
    async def get_available_tools(self, personality_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取可用的工具列表
        
        Args:
            personality_id: 人格ID，如果指定则只返回该人格允许的工具
            
        Returns:
            List[Dict]，每个Dict包含:
            {
                "name": str,        # 工具名称
                "description": str, # 工具描述
                "parameters": Dict  # 工具参数schema
            }
        """
        pass


class EngineCapabilities:
    """引擎能力标识"""
    MEMORY = "memory"
    TOOLS = "tools"
    PERSONALITY = "personality"
    STREAMING = "streaming"
    PERFORMANCE_MONITORING = "performance_monitoring"
    FALLBACK = "fallback"
    CACHE = "cache"
    MCP_INTEGRATION = "mcp_integration"


class EngineStatus:
    """引擎状态常量"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    INITIALIZING = "initializing"
    STOPPED = "stopped"

