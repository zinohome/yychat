import os
from typing import Optional
import threading
from config.config import get_config
from utils.log import log
import asyncio

class ChatMemory:
    def __init__(self, memory=None):
        # 在__init__方法内获取配置
        self.config = get_config()  # 保存配置为实例变量
        self.is_local = self.config.MEMO_USE_LOCAL
        
        # 如果没有提供memory对象，创建一个新的
        if memory is None:
            self._init_memory()
        else:
            # 使用提供的memory对象
            self.memory = memory
    
    def _init_memory(self):
        """根据配置初始化Memory实例（本地或API模式）"""
        try:
            if self.is_local:
                # 本地模式：使用 Memory + ChromaDB
                from mem0 import Memory
                from mem0.configs.base import MemoryConfig
                
                memory_config = MemoryConfig(
                    llm={
                        "provider": self.config.MEM0_LLM_PROVIDER,
                        "config": {
                            "model": self.config.MEM0_LLM_CONFIG_MODEL, 
                            "max_tokens": self.config.MEM0_LLM_CONFIG_MAX_TOKENS
                        }
                    },
                    vector_store={
                        "provider": "chroma",
                        "config": {
                            "collection_name": self.config.CHROMA_COLLECTION_NAME,
                            "path": self.config.CHROMA_PERSIST_DIRECTORY
                        }
                    }
                )
                
                log.info(f"使用本地模式初始化Memory，配置: {memory_config}")
                self.memory = Memory(config=memory_config)
                log.info(f"成功创建本地Memory实例")
                
                # 确保持久化目录存在
                os.makedirs(self.config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
            else:
                # API模式：使用 MemoryClient
                from mem0 import MemoryClient
                
                if not self.config.MEM0_API_KEY:
                    raise ValueError("API模式需要配置 MEM0_API_KEY")
                
                log.info(f"使用API模式初始化MemoryClient")
                self.memory = MemoryClient(api_key=self.config.MEM0_API_KEY)
                log.info(f"成功创建API MemoryClient实例")
        except Exception as e:
            log.error(f"初始化Memory失败: {e}")
            raise

    def _preprocess_query(self, query: str) -> str:
        """预处理查询文本以提高检索效率"""
        # 移除多余空格和换行
        query = ' '.join(query.strip().split())
        # 限制查询长度，过长的查询可能导致性能问题
        max_query_length = 500  # 可配置化
        if len(query) > max_query_length:
            # 保留前max_query_length个字符，确保不会截断单词
            query = query[:max_query_length].rsplit(' ', 1)[0]
        return query

    def add_message(self, conversation_id: str, message: dict):
        try:
            log.debug(f"添加消息到记忆: {message}, conversation_id: {conversation_id}")
            # 创建metadata字典，只包含非None值
            metadata = {"role": message["role"]}
            # 只有当timestamp存在且不为None时才添加
            if "timestamp" in message and message["timestamp"] is not None:
                metadata["timestamp"] = message["timestamp"]
            
            # API 模式和本地模式的参数有所不同
            if self.is_local:
                # 本地模式：使用 Memory.add()
                self.memory.add(
                    message["content"],
                    user_id=conversation_id,
                    metadata=metadata
                )
            else:
                # API 模式：使用 MemoryClient.add()
                # API 需要 messages 参数而不是直接的 content
                self.memory.add(
                    messages=[{
                        "role": message["role"],
                        "content": message["content"]
                    }],
                    user_id=conversation_id,
                    metadata=metadata
                )
            log.debug("消息添加成功")
        except Exception as e:
            log.error(f"Failed to add message to memory: {e}", exc_info=True)
    
    def get_relevant_memory(self, conversation_id: str, query: str, limit: Optional[int] = None) -> list:
        # 如果没有提供limit，使用配置中的默认值
        if limit is None:
            limit = self.config.MEMORY_RETRIEVAL_LIMIT
        
        try:
            # 添加超时控制
            result = []
            exception = None
            
            def _retrieve_memory():
                nonlocal result, exception
                try:
                    # 尝试get_relevant方法，并传递user_id参数
                    # 预处理查询
                    processed_query = self._preprocess_query(query)
                    try:
                        memories = self.memory.get_relevant(processed_query, limit=limit, user_id=conversation_id)
                    except AttributeError:
                        # 如果get_relevant不存在，尝试search方法（这是Mem0 v2.x的推荐方法）
                        try:
                            memories = self.memory.search(processed_query, limit=limit, user_id=conversation_id)
                        except AttributeError:
                            # 如果search也不存在，尝试不带limit参数的get方法
                            memories = self.memory.get(processed_query, user_id=conversation_id)
                            # 如果获取到的结果过多，手动截取
                            if isinstance(memories, list) and len(memories) > limit:
                                memories = memories[:limit]
                    
                    # 处理不同格式的返回结果
                    if isinstance(memories, dict) and 'results' in memories:
                        result = [mem.get('content', str(mem)) for mem in memories['results']]
                    elif isinstance(memories, list):
                        result = [mem.get('content', str(mem)) for mem in memories]
                except Exception as e:
                    nonlocal exception
                    exception = e
            
            # 创建并启动线程
            thread = threading.Thread(target=_retrieve_memory)
            thread.daemon = True
            thread.start()
            
            # 等待线程完成或超时
            thread.join(timeout=self.config.MEMORY_RETRIEVAL_TIMEOUT)
            
            if thread.is_alive():
                log.warning(f"记忆检索超时（{self.config.MEMORY_RETRIEVAL_TIMEOUT}秒）")
                return []
            
            if exception:
                raise exception
            
            return result
        except Exception as e:
            log.error(f"Failed to get relevant memory: {e}")
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
            log.error(f"Failed to get all memory: {e}")
            return []
    
    def delete_memory(self, conversation_id: str):
        try:
            self.memory.delete_all(user_id=conversation_id)
        except Exception as e:
            log.error(f"Failed to delete memory: {e}")
    
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
            log.error(f"Failed to add memory: {e}")

# 添加异步版本的ChatMemory类
class AsyncChatMemory:
    def __init__(self, async_memory=None, config=None):
        # 如果提供了config参数，使用它；否则使用get_config()获取默认配置
        self.config = config if config is not None else get_config()
        self.is_local = self.config.MEMO_USE_LOCAL
        
        # 如果没有提供async_memory对象，创建一个新的
        if async_memory is None:
            self._init_async_memory()
        else:
            # 使用提供的async_memory对象
            self.async_memory = async_memory
    
    def _init_async_memory(self):
        """根据配置初始化AsyncMemory实例（本地或API模式）"""
        try:
            if self.is_local:
                # 本地模式：使用 AsyncMemory + ChromaDB
                from mem0 import AsyncMemory
                from mem0.configs.base import MemoryConfig
                
                # 确保持久化目录存在
                os.makedirs(self.config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
                
                memory_config = MemoryConfig(
                    llm={
                        "provider": self.config.MEM0_LLM_PROVIDER,
                        "config": {
                            "model": self.config.MEM0_LLM_CONFIG_MODEL,
                            "max_tokens": self.config.MEM0_LLM_CONFIG_MAX_TOKENS
                        }
                    },
                    vector_store={
                        "provider": "chroma",
                        "config": {
                            "collection_name": self.config.CHROMA_COLLECTION_NAME,
                            "path": self.config.CHROMA_PERSIST_DIRECTORY
                        }
                    }
                )
                
                log.info(f"使用本地模式初始化AsyncMemory，配置: {memory_config}")
                self.async_memory = AsyncMemory(config=memory_config)
                log.info(f"成功创建本地AsyncMemory实例")
            else:
                # API模式：使用 AsyncMemoryClient
                from mem0 import AsyncMemoryClient
                
                if not self.config.MEM0_API_KEY:
                    raise ValueError("API模式需要配置 MEM0_API_KEY")
                
                log.info(f"使用API模式初始化AsyncMemoryClient")
                self.async_memory = AsyncMemoryClient(api_key=self.config.MEM0_API_KEY)
                log.info(f"成功创建API AsyncMemoryClient实例")
        except Exception as e:
            log.error(f"初始化AsyncMemory失败: {e}")
            raise
    
    def _preprocess_query(self, query: str) -> str:
        """预处理查询文本以提高检索效率"""
        # 移除多余空格和换行
        query = ' '.join(query.strip().split())
        # 限制查询长度，过长的查询可能导致性能问题
        max_query_length = 500  # 可配置化
        if len(query) > max_query_length:
            # 保留前max_query_length个字符，确保不会截断单词
            query = query[:max_query_length].rsplit(' ', 1)[0]
        return query

    async def add_message(self, conversation_id: str, message: dict):
        try:
            log.debug(f"异步添加消息到记忆: {message}, conversation_id: {conversation_id}")
            # 创建metadata字典，只包含非None值
            metadata = {"role": message["role"]}
            # 只有当timestamp存在且不为None时才添加
            if "timestamp" in message and message["timestamp"] is not None:
                metadata["timestamp"] = message["timestamp"]
            
            # API 模式和本地模式的参数有所不同
            if self.is_local:
                # 本地模式：使用 AsyncMemory.add()
                await self.async_memory.add(
                    message["content"],
                    user_id=conversation_id,
                    metadata=metadata
                )
            else:
                # API 模式：使用 AsyncMemoryClient.add()
                # API 需要 messages 参数而不是直接的 content
                await self.async_memory.add(
                    messages=[{
                        "role": message["role"],
                        "content": message["content"]
                    }],
                    user_id=conversation_id,
                    metadata=metadata
                )
            log.debug("异步消息添加成功")
        except Exception as e:
            log.error(f"Failed to add message to async memory: {e}", exc_info=True)
            # 可以选择是否抛出异常，这里选择记录错误但不中断程序
    
    # 同时优化AsyncChatMemory.add_messages_batch方法，改进对add返回值的处理
    async def add_messages_batch(self, conversation_id: str, messages: list):
        """批量添加多条消息到记忆"""
        try:
            log.debug(f"批量异步添加消息到记忆，消息数量: {len(messages)}, conversation_id: {conversation_id}")
            
            # 用于验证添加结果的消息列表
            added_messages = []
            
            for message in messages:
                metadata = {"role": message["role"]}
                if "timestamp" in message and message["timestamp"] is not None:
                    metadata["timestamp"] = message["timestamp"]
                
                # 大幅改进消息格式，使其更结构化，增强mem0的事实提取能力
                content = message["content"]
                if message["role"] == "user":
                    # 增加更丰富的上下文和明确的事实描述
                    formatted_content = f"用户提问: {content}\n"
                    formatted_content += f"主要话题: 关于{content[:20]}的问题\n"
                    formatted_content += f"用户需求概述: 寻求关于{content[:15]}的信息和建议\n"
                    formatted_content += f"重要程度: 高\n"
                    formatted_content += f"需要记忆: 是"
                else:
                    # 为助手回复添加更多结构化信息
                    formatted_content = f"助手回答: {content}\n"
                    formatted_content += f"回答要点: 针对用户关于{content[:20] if len(content)>=20 else content}的问题提供了详细解答\n"
                    formatted_content += f"信息类型: 知识分享和建议\n"
                    formatted_content += f"需要记忆: 是"
                
                log.debug(f"准备添加的格式化内容: {formatted_content[:100]}..., metadata: {metadata}")
                
                # 修复：添加await关键字等待异步方法执行
                try:
                    # API 模式和本地模式的参数有所不同
                    if self.is_local:
                        # 本地模式：使用直接的 content
                        result = await self.async_memory.add(
                            formatted_content,
                            user_id=conversation_id,
                            metadata=metadata
                        )
                    else:
                        # API 模式：使用 messages 列表
                        result = await self.async_memory.add(
                            messages=[{
                                "role": message["role"],
                                "content": formatted_content
                            }],
                            user_id=conversation_id,
                            metadata=metadata
                        )
                    # 改进日志记录，显示返回值的类型和内容
                    log.debug(f"异步添加结果类型: {type(result)}, 结果内容: {result}")
                    
                    # 无论返回什么，只要没有异常就视为成功添加
                    added_messages.append(formatted_content)
                except Exception as add_error:
                    log.error(f"添加消息时出错: {add_error}")
                    
                    # 尝试使用同步版本作为备选
                    try:
                        chat_memory = ChatMemory()
                        chat_memory.add_message(conversation_id, {
                            "role": message["role"],
                            "content": formatted_content,
                            "timestamp": message.get("timestamp")
                        })
                        added_messages.append(formatted_content)
                        log.info("已使用同步版本备选添加消息")
                    except Exception as fallback_error:
                        log.error(f"备选方法也添加失败: {fallback_error}")
            
            log.info(f"批量异步消息添加成功，共添加{len(added_messages)}条消息")
            
            # 恢复验证步骤，但使用适当的注释而不是被注释掉的代码
            try:
                await asyncio.sleep(0.5)
                # 尝试直接从mem0获取所有记忆来验证
                verification_memories = await self.async_memory.get_all(user_id=conversation_id)
                
                # 详细记录验证结果，特别处理字典格式的情况
                if isinstance(verification_memories, list):
                    log.info(f"验证添加结果: 获取到{len(verification_memories)}条记忆")
                elif isinstance(verification_memories, dict):
                    # 处理字典格式的返回结果
                    log.info(f"验证添加结果: 获取到字典格式的记忆，键: {list(verification_memories.keys())}")
                else:
                    log.info(f"验证添加结果: 获取到未知格式的记忆: {type(verification_memories)}")
            except Exception as e:
                log.warning(f"验证记忆添加结果时出错: {e}")
        
        except Exception as e:
            log.error(f"Failed to add batch messages to async memory: {e}", exc_info=True)
    
    async def get_relevant_memory(self, conversation_id: str, query: str, limit: Optional[int] = None) -> list:
        # 如果没有提供limit，使用配置中的默认值
        if limit is None:
            limit = self.config.MEMORY_RETRIEVAL_LIMIT
        try:
            # 直接调用AsyncMemory的get_relevant方法
            # 预处理查询
            processed_query = self._preprocess_query(query)
            # 使用asyncio.wait_for添加超时控制
            memories = await asyncio.wait_for(
                self.async_memory.search(processed_query, limit=limit, user_id=conversation_id),
                timeout=self.config.MEMORY_RETRIEVAL_TIMEOUT
            )
            
            # 确保返回格式与同步版本兼容
            if isinstance(memories, dict) and "results" in memories:
                return [mem.get("memory", mem.get("content", str(mem))) for mem in memories["results"]]
            elif isinstance(memories, list):
                return [mem.get("content", str(mem)) for mem in memories]
            return []
        except asyncio.TimeoutError:
            log.warning(f"异步记忆检索超时（{self.config.MEMORY_RETRIEVAL_TIMEOUT}秒）")
            return []
        except Exception as e:
            log.error(f"Failed to get relevant async memory: {e}")
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
            log.error(f"Failed to get all async memory: {e}")
            return []
    
    async def delete_memory(self, conversation_id: str):
        try:
            await self.async_memory.delete_all(user_id=conversation_id)
        except Exception as e:
            log.error(f"Failed to delete async memory: {e}")

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

# 修改get_memory_config函数，接受可选的config参数
def get_memory_config(config=None):
    """
    获取统一的MemoryConfig配置（仅用于本地模式）
    API模式下不需要此函数
    """
    # 如果提供了config参数，使用它；否则使用get_config()获取默认配置
    config = config if config is not None else get_config()
    
    # 只有在本地模式下才需要MemoryConfig
    if config.MEMO_USE_LOCAL:
        from mem0.configs.base import MemoryConfig
        return MemoryConfig(
            llm={
                "provider": config.MEM0_LLM_PROVIDER,
                "config": {
                    "model": config.MEM0_LLM_CONFIG_MODEL,
                    "max_tokens": config.MEM0_LLM_CONFIG_MAX_TOKENS
                }
            },
            vector_store={
                "provider": "chroma",
                "config": {
                    "collection_name": config.CHROMA_COLLECTION_NAME,
                    "path": config.CHROMA_PERSIST_DIRECTORY
                }
            }
        )
    else:
        # API模式下返回None，因为不需要MemoryConfig
        return None