import os
from mem0 import Memory
from mem0.configs.base import MemoryConfig
from config.config import get_config
from config.log_config import get_logger

logger = get_logger(__name__)
# 移除全局config变量，在需要的地方获取

# 添加日志以便调试
class ChatMemory:
    def __init__(self, memory=None):
        # 在__init__方法内获取配置
        config = get_config()
        
        # 如果没有提供memory对象，创建一个新的
        if memory is None:
            # 正确创建MemoryConfig对象来配置Memory，使用path而不是persist_directory
            memory_config = MemoryConfig(
                vector_store={
                    "provider": "chroma",
                    "config": {
                        "collection_name": config.CHROMA_COLLECTION_NAME,
                        "path": config.CHROMA_PERSIST_DIRECTORY
                    }
                }
            )
            
            logger.debug(f"初始化Memory，配置: {memory_config}")
            # 使用MemoryConfig对象初始化Memory
            self.memory = Memory(config=memory_config)
            logger.debug(f"成功创建Memory实例: {self.memory}")
            
            # 确保持久化目录存在
            os.makedirs(config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        else:
            # 使用提供的memory对象
            self.memory = memory
    
    def add_message(self, conversation_id: str, message: dict):
        try:
            logger.debug(f"添加消息到记忆: {message}, conversation_id: {conversation_id}")
            # 创建metadata字典，只包含非None值
            metadata = {"role": message["role"]}
            # 只有当timestamp存在且不为None时才添加
            if "timestamp" in message and message["timestamp"] is not None:
                metadata["timestamp"] = message["timestamp"]
            
            self.memory.add(
                message["content"],
                user_id=conversation_id,
                metadata=metadata
            )
            logger.debug("消息添加成功")
        except Exception as e:
            logger.error(f"Failed to add message to memory: {e}", exc_info=True)
    
    def get_relevant_memory(self, conversation_id: str, query: str, limit: int = 5) -> list:
        try:
            # 尝试get_relevant方法，并传递user_id参数
            try:
                memories = self.memory.get_relevant(query, limit=limit, user_id=conversation_id)
            except AttributeError:
                # 如果get_relevant不存在，尝试get方法并传递user_id
                memories = self.memory.get(query, limit=limit, user_id=conversation_id)
            
            return [mem["content"] for mem in memories]
        except Exception as e:
            logger.error(f"Failed to get relevant memory: {e}")
            return []
    
    def get_all_memory(self, conversation_id: str) -> list:
        try:
            memories = self.memory.get_all(user_id=conversation_id)
            return [mem["content"] for mem in memories]
        except Exception as e:
            logger.error(f"Failed to get all memory: {e}")
            return []
    
    def delete_memory(self, conversation_id: str):
        try:
            self.memory.delete_all(user_id=conversation_id)
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
    
    # 添加缺失的 add_memory 方法
    def add_memory(self, conversation_id: str, user_message: str, assistant_message: str):
        try:
            content = f"User: {user_message}\nAssistant: {assistant_message}"
            # 创建metadata字典，不包含timestamp字段或使用有效的默认值
            self.memory.add(
                content,
                user_id=conversation_id,
                metadata={"type": "conversation"}
                # 移除或替换为有效的timestamp值
            )
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")