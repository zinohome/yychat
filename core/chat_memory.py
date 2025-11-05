"""
优化后的Memory管理模块
包含缓存和异步优化
"""
import os
from typing import Optional
import threading
import asyncio
from cachetools import TTLCache
import hashlib
from config.config import get_config
from utils.log import log


class ChatMemory:
    def __init__(self, memory=None):
        # 在__init__方法内获取配置
        self.config = get_config()  # 保存配置为实例变量
        self.is_local = self.config.MEMO_USE_LOCAL
        
        # 添加缓存 (5分钟过期，最多100条)
        self._memory_cache = TTLCache(maxsize=100, ttl=300)
        
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
                # 本地模式：使用 Memory + 可选向量库（chroma 或 qdrant）
                from mem0 import Memory
                from mem0.configs.base import MemoryConfig
                
                # 选择向量库
                provider = getattr(self.config, 'VECTOR_STORE_PROVIDER', 'chroma').lower()
                if provider == 'qdrant':
                    vector_store = {
                        "provider": "qdrant",
                        "config": {
                            "collection_name": getattr(self.config, 'QDRANT_COLLECTION_NAME', self.config.CHROMA_COLLECTION_NAME),
                            "host": getattr(self.config, 'QDRANT_HOST', '127.0.0.1'),
                            "port": int(getattr(self.config, 'QDRANT_PORT', 6333)),
                            **({"api_key": self.config.QDRANT_API_KEY} if getattr(self.config, 'QDRANT_API_KEY', None) else {})
                        }
                    }
                else:
                    vector_store = {
                        "provider": "chroma",
                        "config": {
                            "collection_name": self.config.CHROMA_COLLECTION_NAME,
                            "path": self.config.CHROMA_PERSIST_DIRECTORY
                        }
                    }

                memory_config = MemoryConfig(
                    llm={
                        "provider": self.config.MEM0_LLM_PROVIDER,
                        "config": {
                            "api_key": self.config.OPENAI_API_KEY,
                            "openai_base_url": self.config.OPENAI_BASE_URL,
                            "model": self.config.MEM0_LLM_CONFIG_MODEL,
                            "max_tokens": self.config.MEM0_LLM_CONFIG_MAX_TOKENS
                        }
                    },
                    vector_store=vector_store,
                    embedder={
                        "provider": "openai",
                        "config": {
                            "model": getattr(self.config, 'MEM0_EMBEDDER_MODEL', 'text-embedding-3-small'),
                            "api_key": self.config.OPENAI_API_KEY,
                            "openai_base_url": self.config.OPENAI_BASE_URL
                        }
                    }
                )
                
                log.info(f"使用本地模式初始化Memory，配置: {memory_config}")
                self.memory = Memory(config=memory_config)
                log.info(f"成功创建本地Memory实例")
                
                # 确保持久化目录存在
                if provider == 'chroma':
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
            
            # 清除相关缓存
            self._invalidate_cache(conversation_id)
            
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
    
    def _get_cache_key(self, conversation_id: str, query: str, limit: Optional[int]) -> str:
        """生成缓存键"""
        cache_str = f"{conversation_id}:{query}:{limit}"
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _invalidate_cache(self, conversation_id: str):
        """清除指定会话的缓存"""
        # 简单实现：清除所有包含该conversation_id的缓存
        # 更精确的实现需要维护conversation_id到cache_key的映射
        keys_to_remove = []
        for key in list(self._memory_cache.keys()):
            # 这里简化处理，实际应该维护更精确的映射
            keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._memory_cache.pop(key, None)
        
        if keys_to_remove:
            log.debug(f"清除了 {len(keys_to_remove)} 个Memory缓存项")
    
    def get_relevant_memory(self, conversation_id: str, query: str, limit: Optional[int] = None) -> list:
        # 如果没有提供limit，使用配置中的默认值
        if limit is None:
            limit = self.config.MEMORY_RETRIEVAL_LIMIT
        
        # 生成缓存键
        cache_key = self._get_cache_key(conversation_id, query, limit)
        
        # 检查缓存
        if cache_key in self._memory_cache:
            log.debug(f"Memory缓存命中: {cache_key[:8]}...")
            return self._memory_cache[cache_key]
        
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
            
            # 缓存结果
            self._memory_cache[cache_key] = result
            log.debug(f"Memory检索完成，结果已缓存: {len(result)}条记忆")
            
            return result
        except Exception as e:
            log.error(f"Failed to get relevant memory: {e}")
            return []
    
    def get_all_memory(self, conversation_id: str) -> list:
        try:
            memories = self.memory.get_all(user_id=conversation_id)
            
            # 检查memories的格式并相应处理
            if isinstance(memories, dict) and "results" in memories:
                # 如果memories是字典且包含results键，处理results列表
                results = memories["results"]
                if isinstance(results, list):
                    result = []
                    for mem in results:
                        # 如果mem是字典，优先获取memory字段，其次content字段
                        if isinstance(mem, dict):
                            if "memory" in mem:
                                result.append(mem["memory"])
                            elif "content" in mem:
                                result.append(mem["content"])
                            else:
                                result.append(str(mem))
                        # 如果mem是字符串，直接添加
                        elif isinstance(mem, str):
                            result.append(mem)
                        # 其他类型转换为字符串
                        else:
                            result.append(str(mem))
                    return result
                else:
                    return [str(results)]
            elif isinstance(memories, list):
                # 如果memories直接是列表
                result = []
                for mem in memories:
                    # 如果mem是字典，优先获取memory字段，其次content字段
                    if isinstance(mem, dict):
                        if "memory" in mem:
                            result.append(mem["memory"])
                        elif "content" in mem:
                            result.append(mem["content"])
                        else:
                            result.append(str(mem))
                    # 如果mem是字符串，直接添加
                    elif isinstance(mem, str):
                        result.append(mem)
                    # 其他类型转换为字符串
                    else:
                        result.append(str(mem))
                return result
            # 如果memories不是列表也不是字典，转换为列表返回
            elif memories is not None:
                return [str(memories)]
            else:
                return []
        except Exception as e:
            log.error(f"Failed to get all memory: {e}")
            return []
    
    def delete_memory(self, conversation_id: str):
        try:
            # 清除缓存
            self._invalidate_cache(conversation_id)
            
            self.memory.delete_all(user_id=conversation_id)
        except Exception as e:
            log.error(f"Failed to delete memory: {e}")
    
    def add_memory(self, conversation_id: str, user_message: str, assistant_message: str):
        try:
            # 清除缓存
            self._invalidate_cache(conversation_id)
            
            content = f"User: {user_message}\nAssistant: {assistant_message}"
            self.memory.add(
                content,
                user_id=conversation_id,
                metadata={"role": "conversation"}
            )
        except Exception as e:
            log.error(f"Failed to add memory: {e}")
    
    def get_memory(self, conversation_id: str) -> list:
        return self.get_all_memory(conversation_id)
    
    def clear_memory(self, conversation_id: str):
        self.delete_memory(conversation_id)


class AsyncChatMemory:
    """异步Memory管理类 (优化版本)"""
    
    def __init__(self, memory=None):
        self.config = get_config()
        self.is_local = self.config.MEMO_USE_LOCAL
        
        # 添加缓存
        self._memory_cache = TTLCache(maxsize=100, ttl=300)
        
        # 如果没有提供memory对象，创建一个新的
        if memory is None:
            self._init_memory()
        else:
            # 使用提供的memory对象
            self.memory = memory
    
    def _init_memory(self):
        """根据配置初始化AsyncMemory实例（本地或API模式）"""
        try:
            if self.is_local:
                from mem0 import AsyncMemory
                from mem0.configs.base import MemoryConfig
                
                # 选择向量库
                provider = getattr(self.config, 'VECTOR_STORE_PROVIDER', 'chroma').lower()
                if provider == 'qdrant':
                    vector_store = {
                        "provider": "qdrant",
                        "config": {
                            "collection_name": getattr(self.config, 'QDRANT_COLLECTION_NAME', self.config.CHROMA_COLLECTION_NAME),
                            "host": getattr(self.config, 'QDRANT_HOST', '127.0.0.1'),
                            "port": int(getattr(self.config, 'QDRANT_PORT', 6333)),
                            **({"api_key": self.config.QDRANT_API_KEY} if getattr(self.config, 'QDRANT_API_KEY', None) else {})
                        }
                    }
                else:
                    vector_store = {
                        "provider": "chroma",
                        "config": {
                            "collection_name": self.config.CHROMA_COLLECTION_NAME,
                            "path": self.config.CHROMA_PERSIST_DIRECTORY
                        }
                    }

                memory_config = MemoryConfig(
                    llm={
                        "provider": self.config.MEM0_LLM_PROVIDER,
                        "config": {
                            "model": self.config.MEM0_LLM_CONFIG_MODEL,
                            "max_tokens": self.config.MEM0_LLM_CONFIG_MAX_TOKENS
                        }
                    },
                    vector_store=vector_store,
                    embedder={
                        "provider": "openai",
                        "config": {
                            "model": getattr(self.config, 'MEM0_EMBEDDER_MODEL', 'text-embedding-3-small'),
                            "api_key": self.config.OPENAI_API_KEY,
                            "openai_base_url": self.config.OPENAI_BASE_URL
                        }
                    }
                )
                
                log.info(f"使用本地模式初始化AsyncMemory")
                self.memory = AsyncMemory(config=memory_config)
                if provider == 'chroma':
                    os.makedirs(self.config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
            else:
                from mem0 import AsyncMemoryClient
                
                if not self.config.MEM0_API_KEY:
                    raise ValueError("API模式需要配置 MEM0_API_KEY")
                
                log.info(f"使用API模式初始化AsyncMemoryClient")
                self.memory = AsyncMemoryClient(api_key=self.config.MEM0_API_KEY)
        except Exception as e:
            log.error(f"初始化AsyncMemory失败: {e}")
            raise
    
    def _get_cache_key(self, conversation_id: str, query: str, limit: Optional[int]) -> str:
        """生成缓存键"""
        cache_str = f"{conversation_id}:{query}:{limit}"
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _invalidate_cache(self, conversation_id: str):
        """清除指定会话的缓存"""
        self._memory_cache.clear()  # 简化实现，清除所有缓存
        log.debug(f"已清除所有Memory缓存")
    
    async def get_relevant_memory(self, conversation_id: str, query: str, limit: Optional[int] = None) -> list:
        """异步获取相关记忆 (带缓存和超时)"""
        if limit is None:
            limit = self.config.MEMORY_RETRIEVAL_LIMIT
        
        # 检查缓存
        cache_key = self._get_cache_key(conversation_id, query, limit)
        if cache_key in self._memory_cache:
            cached_result = self._memory_cache[cache_key]
            log.debug(f"💾 Memory缓存命中: conversation_id={conversation_id}, cache_key={cache_key[:8]}..., 返回{len(cached_result)}条记忆")
            return cached_result
        
        log.debug(f"🔍 开始Memory检索: conversation_id={conversation_id}, query='{query[:100]}...', limit={limit}")
        try:
            # 使用 asyncio.wait_for 实现超时
            result = await asyncio.wait_for(
                self._retrieve_memory(conversation_id, query, limit),
                timeout=self.config.MEMORY_RETRIEVAL_TIMEOUT
            )
            
            # 缓存结果
            self._memory_cache[cache_key] = result
            log.debug(f"✅ Memory检索完成，结果已缓存: conversation_id={conversation_id}, 找到{len(result)}条记忆, cache_key={cache_key[:8]}...")
            
            return result
        except asyncio.TimeoutError:
            log.warning(f"⏱️ Memory检索超时: conversation_id={conversation_id}, timeout={self.config.MEMORY_RETRIEVAL_TIMEOUT}s")
            return []
        except Exception as e:
            log.error(f"❌ Memory检索失败: conversation_id={conversation_id}, error={e}", exc_info=True)
            return []
    
    async def _retrieve_memory(self, conversation_id: str, query: str, limit: int) -> list:
        """实际的Memory检索逻辑"""
        try:
            # 预处理查询
            processed_query = ' '.join(query.strip().split())[:500]
            log.debug(f"🔍 _retrieve_memory: conversation_id={conversation_id}, processed_query='{processed_query[:100]}...', limit={limit}")
            
            # 异步调用Memory
            try:
                log.debug(f"🔍 尝试使用 memory.get_relevant() 方法")
                memories = await self.memory.get_relevant(
                    processed_query, 
                    limit=limit, 
                    user_id=conversation_id
                )
                log.debug(f"✅ 使用 get_relevant() 成功，返回类型: {type(memories)}")
            except AttributeError:
                try:
                    log.debug(f"🔍 get_relevant() 不存在，尝试使用 memory.search() 方法")
                    memories = await self.memory.search(
                        processed_query, 
                        limit=limit, 
                        user_id=conversation_id
                    )
                    log.debug(f"✅ 使用 search() 成功，返回类型: {type(memories)}")
                except AttributeError:
                    log.debug(f"🔍 search() 不存在，尝试使用 memory.get() 方法")
                    memories = await self.memory.get(
                        processed_query, 
                        user_id=conversation_id
                    )
                    log.debug(f"✅ 使用 get() 成功，返回类型: {type(memories)}")
                    if isinstance(memories, list) and len(memories) > limit:
                        memories = memories[:limit]
                        log.debug(f"📝 截取记忆到limit={limit}条")
            
            # 处理返回格式
            if isinstance(memories, dict) and 'results' in memories:
                result = [mem.get('content', str(mem)) for mem in memories['results']]
                log.debug(f"📝 处理dict格式结果，提取到{len(result)}条记忆")
                return result
            elif isinstance(memories, list):
                result = [mem.get('content', str(mem)) if isinstance(mem, dict) else str(mem) for mem in memories]
                log.debug(f"📝 处理list格式结果，提取到{len(result)}条记忆")
                return result
            else:
                log.debug(f"⚠️ 未知的记忆返回格式: {type(memories)}, 返回空列表")
                return []
        except Exception as e:
            log.error(f"❌ _retrieve_memory error: conversation_id={conversation_id}, error={e}", exc_info=True)
            return []
    
    async def add_message(self, conversation_id: str, message: dict):
        """异步添加消息"""
        try:
            content_preview = str(message.get("content", ""))[:100]  # 只记录前100个字符
            log.debug(f"💾 开始添加消息到记忆: conversation_id={conversation_id}, role={message.get('role')}, content='{content_preview}...'")
            
            # 清除缓存
            self._invalidate_cache(conversation_id)
            
            metadata = {"role": message["role"]}
            if "timestamp" in message and message["timestamp"] is not None:
                metadata["timestamp"] = message["timestamp"]
            
            if self.is_local:
                log.debug(f"💾 使用本地模式添加消息: conversation_id={conversation_id}")
                await self.memory.add(
                    message["content"],
                    user_id=conversation_id,
                    metadata=metadata
                )
            else:
                log.debug(f"💾 使用API模式添加消息: conversation_id={conversation_id}")
                await self.memory.add(
                    messages=[{
                        "role": message["role"],
                        "content": message["content"]
                    }],
                    user_id=conversation_id,
                    metadata=metadata
                )
            log.debug(f"✅ 异步消息添加成功: conversation_id={conversation_id}, role={message.get('role')}")
        except Exception as e:
            log.error(f"❌ 异步消息添加失败: conversation_id={conversation_id}, error={e}", exc_info=True)
    
    async def add_messages_batch(self, conversation_id: str, messages: list):
        """异步批量添加消息"""
        try:
            log.debug(f"💾 开始批量添加消息到记忆: conversation_id={conversation_id}, 消息数量={len(messages)}")
            
            # 清除缓存
            self._invalidate_cache(conversation_id)
            
            for idx, message in enumerate(messages):
                content_preview = str(message.get("content", ""))[:50]  # 只记录前50个字符
                log.debug(f"💾 添加第{idx+1}/{len(messages)}条消息: conversation_id={conversation_id}, role={message.get('role')}, content='{content_preview}...'")
                
                metadata = {"role": message["role"]}
                if "timestamp" in message and message["timestamp"] is not None:
                    metadata["timestamp"] = message["timestamp"]
                
                if self.is_local:
                    await self.memory.add(
                        message["content"],
                        user_id=conversation_id,
                        metadata=metadata
                    )
                else:
                    await self.memory.add(
                        messages=[{
                            "role": message["role"],
                            "content": message["content"]
                        }],
                        user_id=conversation_id,
                        metadata=metadata
                    )
            
            log.debug(f"✅ 异步批量添加 {len(messages)} 条消息成功: conversation_id={conversation_id}")
        except Exception as e:
            log.error(f"❌ 异步批量添加消息失败: conversation_id={conversation_id}, error={e}", exc_info=True)
            raise

    async def get_all_memory(self, conversation_id: str) -> list:
        """异步获取所有记忆"""
        try:
            memories = await self.memory.get_all(user_id=conversation_id)
            
            # 检查memories的格式并相应处理
            if isinstance(memories, dict) and "results" in memories:
                # 如果memories是字典且包含results键，处理results列表
                results = memories["results"]
                if isinstance(results, list):
                    result = []
                    for mem in results:
                        # 如果mem是字典，优先获取memory字段，其次content字段
                        if isinstance(mem, dict):
                            if "memory" in mem:
                                result.append(mem["memory"])
                            elif "content" in mem:
                                result.append(mem["content"])
                            else:
                                result.append(str(mem))
                        # 如果mem是字符串，直接添加
                        elif isinstance(mem, str):
                            result.append(mem)
                        # 其他类型转换为字符串
                        else:
                            result.append(str(mem))
                    return result
                else:
                    return [str(results)]
            elif isinstance(memories, list):
                # 如果memories直接是列表
                result = []
                for mem in memories:
                    # 如果mem是字典，优先获取memory字段，其次content字段
                    if isinstance(mem, dict):
                        if "memory" in mem:
                            result.append(mem["memory"])
                        elif "content" in mem:
                            result.append(mem["content"])
                        else:
                            result.append(str(mem))
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
            log.error(f"Failed to get all async memory: {e}")
            return []

    async def delete_memory(self, conversation_id: str):
        """异步删除记忆"""
        try:
            # 清除缓存
            self._invalidate_cache(conversation_id)
            
            await self.memory.delete_all(user_id=conversation_id)
        except Exception as e:
            log.error(f"Failed to delete async memory: {e}")


# 全局实例
_async_chat_memory = None

def get_async_chat_memory(memory=None):
    """获取全局AsyncChatMemory实例"""
    global _async_chat_memory
    if _async_chat_memory is None:
        _async_chat_memory = AsyncChatMemory(memory)
    return _async_chat_memory

