import os
from mem0 import Memory, AsyncMemory
from mem0.configs.base import MemoryConfig
from config.config import get_config
from config.log_config import get_logger
import asyncio

logger = get_logger(__name__)

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
            
            # 检查memories的格式并相应处理
            if isinstance(memories, list):
                result = []
                for mem in memories:
                    # 如果mem是字典并且有content键，获取content值
                    if isinstance(mem, dict) and "content" in mem:
                        result.append(mem["content"])
                    # 如果mem是字符串，直接添加
                    elif isinstance(mem, str):
                        result.append(mem)
                    # 其他类型转换为字符串
                    else:
                        result.append(str(mem))
                return result
            # 如果memories不是列表，转换为列表返回
            elif memories is not None:
                return [str(memories)]
            else:
                return []
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
            )
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")

# 添加异步版本的ChatMemory类
def get_memory_config():
    """获取统一的MemoryConfig配置"""
    config = get_config()
    return MemoryConfig(
        vector_store={
            "provider": "chroma",
            "config": {
                "collection_name": config.CHROMA_COLLECTION_NAME,
                "path": config.CHROMA_PERSIST_DIRECTORY
            }
        }
    )

class AsyncChatMemory:
    def __init__(self, async_memory=None):
        # 在__init__方法内获取配置
        config = get_config()
        
        # 确保持久化目录存在
        os.makedirs(config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        
        # 如果没有提供async_memory对象，创建一个新的
        if async_memory is None:
            memory_config = get_memory_config()
            
            logger.debug(f"初始化AsyncMemory，配置: {memory_config}")
            # 使用MemoryConfig对象初始化AsyncMemory
            self.async_memory = AsyncMemory(config=memory_config)
            logger.debug(f"成功创建AsyncMemory实例: {self.async_memory}")
        else:
            # 使用提供的async_memory对象
            self.async_memory = async_memory
    
    async def add_message(self, conversation_id: str, message: dict):
        try:
            logger.debug(f"异步添加消息到记忆: {message}, conversation_id: {conversation_id}")
            # 创建metadata字典，只包含非None值
            metadata = {"role": message["role"]}
            # 只有当timestamp存在且不为None时才添加
            if "timestamp" in message and message["timestamp"] is not None:
                metadata["timestamp"] = message["timestamp"]
            
            await self.async_memory.add(
                message["content"],
                user_id=conversation_id,
                metadata=metadata
            )
            logger.debug("异步消息添加成功")
        except Exception as e:
            logger.error(f"Failed to add message to async memory: {e}", exc_info=True)
            # 可以选择是否抛出异常，这里选择记录错误但不中断程序
    
    async def add_messages_batch(self, conversation_id: str, messages: list):
        """批量添加多条消息到记忆"""
        try:
            logger.debug(f"批量异步添加消息到记忆，消息数量: {len(messages)}, conversation_id: {conversation_id}")
            
            # 使用异步内存的原生批量操作（如果支持）
            # 注意：这里根据mem0的AsyncMemory API调整，可能需要适当修改
            for message in messages:
                metadata = {"role": message["role"]}
                if "timestamp" in message and message["timestamp"] is not None:
                    metadata["timestamp"] = message["timestamp"]
                
                await self.async_memory.add(
                    message["content"],
                    user_id=conversation_id,
                    metadata=metadata
                )
            
            logger.debug("批量异步消息添加成功")
        except Exception as e:
            logger.error(f"Failed to add batch messages to async memory: {e}", exc_info=True)
    
    async def get_relevant_memory(self, conversation_id: str, query: str, limit: int = 5) -> list:
        try:
            # 直接调用AsyncMemory的get_relevant方法
            memories = await self.async_memory.search(query, limit=limit, user_id=conversation_id)
            
            # 确保返回格式与同步版本兼容
            if isinstance(memories, dict) and "results" in memories:
                return [mem["memory"] for mem in memories["results"]]
            return []
        except Exception as e:
            logger.error(f"Failed to get relevant async memory: {e}")
            return []
    
    async def get_all_memory(self, conversation_id: str) -> list:
        try:
            memories = await self.async_memory.get_all(user_id=conversation_id)
            
            # 检查memories的格式并相应处理
            result = []
            if isinstance(memories, list):
                for mem in memories:
                    # 如果mem是字典并且有content键，获取content值
                    if isinstance(mem, dict) and "content" in mem:
                        result.append(mem["content"])
                    # 如果mem是字符串，直接添加
                    elif isinstance(mem, str):
                        result.append(mem)
                    # 其他类型转换为字符串
                    else:
                        result.append(str(mem))
            return result
        except Exception as e:
            logger.error(f"Failed to get all async memory: {e}")
            return []
    
    async def delete_memory(self, conversation_id: str):
        try:
            await self.async_memory.delete_all(user_id=conversation_id)
        except Exception as e:
            logger.error(f"Failed to delete async memory: {e}")

# 创建一个全局的AsyncChatMemory实例，方便在异步环境中使用
def get_async_chat_memory():
    """获取全局的AsyncChatMemory实例"""
    global _async_chat_memory
    try:
        # 如果全局实例已存在，则直接返回
        return _async_chat_memory
    except NameError:
        # 否则创建新实例
        _async_chat_memory = AsyncChatMemory()
        return _async_chat_memory