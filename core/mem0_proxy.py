import time
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
import openai
from openai import OpenAI
from mem0.proxy.main import Mem0
import time
import json
import asyncio
from config.config import get_config
from utils.log import log
from core.chat_memory import ChatMemory, get_async_chat_memory
from core.personality_manager import PersonalityManager
from services.tools.manager import ToolManager
from services.mcp.manager import mcp_manager
from services.mcp.exceptions import MCPServiceError, MCPServerNotFoundError, MCPToolNotFoundError


config = get_config()

class Mem0ProxyManager:
    """
    基于Mem0官方Proxy接口的聊天引擎，结合Mem0的高性能和完整的前端API功能支持
    支持personality、conversation_id、use_tools、stream等功能
    """
    def __init__(self, custom_config=None):
        # 使用传入的配置或获取默认配置
        self.config = custom_config or config
        # 初始化Mem0客户端
        self._init_mem0_client()
        # 缓存已初始化的客户端，避免重复创建
        self.clients_cache = {}
        # 标记是否使用本地客户端（用于处理API差异）
        self.is_local_client = False
        
        # 初始化其他必要组件
        self.chat_memory = ChatMemory()
        self.async_chat_memory = get_async_chat_memory()
        self.personality_manager = PersonalityManager()
        self.tool_manager = ToolManager()
        
        # 初始化OpenAI客户端用于降级方案
        self._init_openai_client()
        
    def _init_openai_client(self):
        """初始化OpenAI客户端"""
        try:
            self.openai_client = OpenAI(
                api_key=self.config.OPENAI_API_KEY,
                base_url=self.config.OPENAI_BASE_URL,
                timeout=self.config.OPENAI_API_TIMEOUT,
                max_retries=self.config.OPENAI_API_RETRIES
            )
        except Exception as e:
            log.error(f"初始化OpenAI客户端失败: {e}")
            self.openai_client = None
        
    def _init_mem0_client(self):
        """初始化基础Mem0客户端"""
        try:
            # 本地配置初始化函数，避免代码重复
            def init_local_config():
                
                mem_config = {
                    "vector_store": {
                        "provider": "chroma",
                        "config": {
                            "collection_name": self.config.CHROMA_COLLECTION_NAME,
                            "path": self.config.CHROMA_PERSIST_DIRECTORY
                        }
                    },
                    "llm": {
                        "provider": self.config.MEM0_LLM_PROVIDER,
                        "config": {
                            "model": self.config.MEM0_LLM_CONFIG_MODEL,
                            "max_tokens": self.config.MEM0_LLM_CONFIG_MAX_TOKENS
                        }
                    }
                }
                self.base_client = Mem0(config=mem_config)
                self.is_local_client = True
                
                # 为本地客户端的mem0_client添加包装，移除filters参数
                if hasattr(self.base_client, 'mem0_client'):
                    original_add = self.base_client.mem0_client.add
                    
                    # 创建一个新的add方法，它不接受filters参数
                    def patched_add(*args, **kwargs):
                        # 移除filters参数
                        if 'filters' in kwargs:
                            del kwargs['filters']
                        # 调用原始方法
                        return original_add(*args, **kwargs)
                    
                    # 应用补丁
                    self.base_client.mem0_client.add = patched_add
                
                return "本地配置"

            # 判断逻辑简化：
            # 1. 如果MEMO_USE_LOCAL为True，强制使用本地配置
            # 2. 否则，如果有API密钥，使用API密钥方式
            # 3. 否则，使用本地配置作为后备方案
            if self.config.MEMO_USE_LOCAL:
                config_type = init_local_config()
                log.info(f"强制使用{config_type}初始化Mem0客户端")
            elif self.config.MEM0_API_KEY:
                self.base_client = Mem0(api_key=self.config.MEM0_API_KEY)
                self.is_local_client = False
                log.info("使用Mem0 API密钥初始化客户端")
            else:
                config_type = init_local_config()
                log.info(f"使用{config_type}初始化Mem0客户端")
        except Exception as e:
            log.error(f"初始化Mem0客户端失败: {e}")
            # 创建一个模拟客户端用于降级处理
            self.base_client = self._create_mock_client()
            self.is_local_client = True
    
    def _create_mock_client(self):
        """创建一个模拟客户端用于降级处理"""
        class MockMem0Client:
            @property
            def chat(self):
                class MockChat:
                    @property
                    def completions(self):
                        class MockCompletions:
                            def create(self, **kwargs):
                                # 直接调用OpenAI API作为降级方案
                                # 过滤掉OpenAI API不支持的参数
                                openai_kwargs = kwargs.copy()
                                if 'user_id' in openai_kwargs:
                                    del openai_kwargs['user_id']
                                if 'limit' in openai_kwargs:
                                    del openai_kwargs['limit']
                                
                                client = OpenAI(
                                    api_key=config.OPENAI_API_KEY,
                                    base_url=config.OPENAI_BASE_URL
                                )
                                return client.chat.completions.create(**openai_kwargs)
                        return MockCompletions()
                return MockChat()
        return MockMem0Client()
    
    def get_client(self, user_id: str = "default"):
        """获取或创建特定用户的Mem0客户端"""
        if user_id not in self.clients_cache:
            # 注意：这里可以根据需要为不同用户创建不同配置的客户端
            # 目前简单实现为所有用户共享同一个基础客户端
            self.clients_cache[user_id] = self.base_client
        # 返回客户端
        return self.clients_cache[user_id]
    
    async def generate_response(self, messages: List[Dict[str, str]], conversation_id: str, personality_id: str = None, use_tools: bool = False, stream: bool = False) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """生成响应"""
        start_time = time.time()
        
        try:
            # 记录请求信息
            log.debug(f"收到生成响应请求，对话ID: {conversation_id}, 人格ID: {personality_id}")
            
            # 准备调用参数，符合用户提示中的格式
            messages_copy = [msg.copy() for msg in messages]
            
            # 应用人格
            if personality_id:
                messages_copy = self.personality_manager.apply_personality(messages_copy, personality_id)
                
            # 构建请求参数
            call_params = {
                "messages": messages_copy,
                "model": self.config.OPENAI_MODEL,
                "user_id": conversation_id,
                "stream": stream,
                "temperature": float(self.config.OPENAI_TEMPERATURE),
                "limit": self.config.MEMORY_RETRIEVAL_LIMIT
            }
            
            # 如果启用了工具调用，添加工具配置
            if use_tools:
                from core.tools import get_available_tools
                
                # 获取所有可用工具
                all_tools = get_available_tools()
                
                # 检查是否有personality_id，且该personality有allowed_tools限制
                if personality_id:
                    personality = self.personality_manager.get_personality(personality_id)
                    if personality and personality.allowed_tools:
                        # 获取personality允许使用的工具名称列表，同时支持name和tool_name两种格式
                        allowed_tool_names = []
                        for tool in personality.allowed_tools:
                            if 'name' in tool:
                                allowed_tool_names.append(tool['name'])
                            elif 'tool_name' in tool:
                                allowed_tool_names.append(tool['tool_name'])
                        
                        if allowed_tool_names:
                            # 根据allowed_tools过滤工具列表
                            filtered_tools = [tool for tool in all_tools if tool.get('function', {}).get('name') in allowed_tool_names]
                            call_params["tools"] = filtered_tools
                            log.debug(f"应用personality {personality_id} 的工具限制，允许的工具数量: {len(filtered_tools)}")
                        else:
                            # 如果allowed_tools存在但格式不正确，使用所有工具
                            call_params["tools"] = all_tools
                            log.warning(f"personality {personality_id} 的allowed_tools格式不正确，使用所有可用工具")
                    else:
                        # 如果personality不存在或没有allowed_tools限制，使用所有工具
                        call_params["tools"] = all_tools
                else:
                    # 如果没有指定personality_id，使用所有工具
                    call_params["tools"] = all_tools
                    
                # 设置工具选择策略
                call_params["tool_choice"] = "auto"
            
            # 调用Mem0客户端生成响应
            client = self.get_client()
            
            # 处理流式和非流式请求
            if stream:
                # 对于流式请求，我们需要确保返回一个异步迭代器
                # 由于asyncio.to_thread会阻塞直到函数完成，我们需要手动创建异步生成器
                async def streaming_generator():
                    try:
                        # 在单独的线程中调用客户端并获取响应
                        result = await asyncio.to_thread(
                            client.chat.completions.create,
                            **call_params
                        )
                        
                        # 检查结果是否为None
                        if result is None:
                            log.error("Mem0 API返回None，无法处理流式响应")
                            yield {
                                "role": "assistant",
                                "content": "发生内部错误: 无法获取响应",
                                "finish_reason": "error",
                                "stream": True
                            }
                            return
                        
                        # 处理同步迭代器结果
                        if hasattr(result, '__iter__') and not hasattr(result, '__aiter__'):
                            # 将同步迭代器转换为异步生成器
                            for chunk in result:
                                yield chunk
                        elif hasattr(result, '__aiter__'):
                            # 已经是异步迭代器，可以直接迭代
                            async for chunk in result:
                                yield chunk
                        else:
                            log.error(f"Mem0 API返回的结果既不是迭代器也不是异步迭代器: {type(result)}")
                            yield {
                                "role": "assistant",
                                "content": "发生内部错误: 无法处理响应格式",
                                "finish_reason": "error",
                                "stream": True
                            }
                    except Exception as e:
                        log.error(f"流式请求处理异常: {e}")
                        yield {
                            "role": "assistant",
                            "content": f"发生内部错误: {str(e)}",
                            "finish_reason": "error",
                            "stream": True
                        }
                
                # 返回异步生成器
                return streaming_generator()
            else:
                # 对于非流式请求，使用asyncio.to_thread等待结果
                result = await asyncio.to_thread(
                    client.chat.completions.create,
                    **call_params
                )
            
            # 处理非流式响应
            if not stream:
                if result:
                    if hasattr(result, 'choices') and result.choices:
                        return {
                            "role": "assistant",
                            "content": result.choices[0].message.content if hasattr(result.choices[0].message, 'content') and result.choices[0].message.content else "",
                            "tool_calls": getattr(result.choices[0].message, 'tool_calls', None)
                        }
                    elif isinstance(result, dict) and "content" in result:
                        return result
                return {"role": "assistant", "content": "无法生成响应"}
        
        except Exception as e:
            log.error(f"使用Mem0代理生成响应失败: {e}")
            # 降级到直接调用OpenAI API
            return await self._fallback_to_openai(messages, conversation_id, personality_id, use_tools, stream)
        finally:
            log.debug(f"Mem0代理响应生成耗时: {time.time() - start_time:.3f}秒")

    async def _fallback_to_openai(self, messages: List[Dict[str, str]], conversation_id: str, personality_id: str = None, use_tools: bool = False, stream: bool = False) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """降级到OpenAI API"""
        fallback_start_time = time.time()
        log.warning(f"降级到OpenAI API，对话ID: {conversation_id}")
        
        try:
            # 准备调用OpenAI API所需的参数
            openai_params = {
                "model": "gpt-4o",  # 或者从配置中获取
                "messages": messages,
                "stream": stream
            }
            
            # 如果启用了工具调用，添加工具配置
            if use_tools:
                from core.tools import get_available_tools
                
                # 获取所有可用工具
                all_tools = get_available_tools()
                
                # 检查是否有personality_id，且该personality有allowed_tools限制
                if personality_id:
                    personality = self.personality_manager.get_personality(personality_id)
                    if personality and personality.allowed_tools:
                        # 获取personality允许使用的工具名称列表
                        allowed_tool_names = [tool['name'] for tool in personality.allowed_tools if 'name' in tool]
                        if allowed_tool_names:
                            # 根据allowed_tools过滤工具列表
                            filtered_tools = [tool for tool in all_tools if tool.get('function', {}).get('name') in allowed_tool_names]
                            openai_params["tools"] = filtered_tools
                            log.debug(f"应用personality {personality_id} 的工具限制，允许的工具数量: {len(filtered_tools)}")
                        else:
                            # 如果allowed_tools存在但格式不正确，使用所有工具
                            openai_params["tools"] = all_tools
                            log.warning(f"personality {personality_id} 的allowed_tools格式不正确，使用所有可用工具")
                    else:
                        # 如果personality不存在或没有allowed_tools限制，使用所有工具
                        openai_params["tools"] = all_tools
                else:
                    # 如果没有指定personality_id，使用所有工具
                    openai_params["tools"] = all_tools
                
                openai_params["tool_choice"] = "auto"
            
            # 调用OpenAI API
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            response = await client.chat.completions.create(**openai_params)
            
            # 处理非流式响应
            if not stream:
                if response and hasattr(response, 'choices') and response.choices:
                    choice = response.choices[0]
                    if hasattr(choice, 'message'):
                        return {
                            "role": "assistant",
                            "content": getattr(choice.message, 'content', ""),
                            "tool_calls": getattr(choice.message, 'tool_calls', None)
                        }
                return {"role": "assistant", "content": "无法生成响应"}
            
            # 处理流式响应
            else:
                # 确保response不是None
                if response is None:
                    log.error("OpenAI API返回None，无法处理流式响应")
                    # 创建并返回错误响应生成器
                    async def error_generator():
                        yield {
                            "role": "assistant",
                            "content": "发生内部错误: 无法获取OpenAI响应",
                            "finish_reason": "error",
                            "stream": True
                        }
                    return error_generator()
                
                # 确保response是异步迭代器
                if not hasattr(response, '__aiter__'):
                    log.error(f"OpenAI API返回的结果不是异步迭代器: {type(response)}")
                    # 创建并返回错误响应生成器
                    async def error_generator():
                        yield {
                            "role": "assistant",
                            "content": "发生内部错误: 无法处理OpenAI响应格式",
                            "finish_reason": "error",
                            "stream": True
                        }
                    return error_generator()
                
                # 调用_handle_streaming_response处理流式响应
                return self._handle_streaming_response(response, conversation_id, messages)
        
        except Exception as e:
            log.error(f"降级到OpenAI API失败: {e}")
            # 返回错误响应
            if not stream:
                return {"role": "assistant", "content": f"发生错误: {str(e)}"}
            else:
                # 确保即使在外部异常情况下也返回有效的异步生成器结果
                async def error_generator():
                    yield {
                        "role": "assistant",
                        "content": f"发生错误: {str(e)}",
                        "finish_reason": "error",
                        "stream": True
                    }
                return error_generator()
        finally:
            log.debug(f"OpenAI API调用耗时: {time.time() - fallback_start_time:.3f}秒")
    
    async def _handle_streaming_response(self, response, conversation_id: str, original_messages: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
        """处理流式响应
        
        Args:
            response: 从API获取的响应对象，应该是一个异步迭代器
            conversation_id: 对话ID
            original_messages: 原始消息列表
            
        Yields:
            Dict[str, Any]: 流式响应的每个分块
        """
        log.debug(f"开始处理流式响应，对话ID: {conversation_id}")
        
        # 记录API调用开始时间
        start_time = time.time()
        
        try:
            # 初始化变量
            tool_calls = None
            full_content = ""
            chunk_count = 0
            first_chunk_time = None
            
            # 确保response不是None
            if response is None:
                log.error("响应对象为None，无法处理流式响应")
                yield {
                    "role": "assistant",
                    "content": "发生内部错误: 无法处理响应",
                    "finish_reason": "error",
                    "stream": True
                }
                return
            
            # 确保response是可迭代的协程对象
            if not hasattr(response, '__aiter__'):
                log.error(f"响应对象不是异步迭代器: {type(response)}")
                yield {
                    "role": "assistant",
                    "content": "发生内部错误: 无法处理响应格式",
                    "finish_reason": "error",
                    "stream": True
                }
                return
            
            # 从流式响应中提取内容 - 添加额外的错误处理
            try:
                async for chunk in response:
                    chunk_count += 1
                    if chunk_count == 1:
                        first_chunk_time = time.time()
                        log.debug(f"首字节响应时间: {first_chunk_time - start_time:.2f}秒")
                        
                    if hasattr(chunk, 'choices') and chunk.choices:
                        choice = chunk.choices[0]
                        
                        # 检测工具调用
                        if hasattr(choice.delta, 'tool_calls') and choice.delta.tool_calls:
                            if not tool_calls:
                                tool_calls = []
                            # 收集工具调用信息
                            for tool_call in choice.delta.tool_calls:
                                # 初始化或更新工具调用信息
                                if tool_call.index >= len(tool_calls):
                                    tool_calls.append({"id": tool_call.id, "type": "function", "function": {}})
                                    
                                # 更新函数名称和参数
                                if hasattr(tool_call.function, 'name') and tool_call.function.name:
                                    tool_calls[tool_call.index]["function"]["name"] = tool_call.function.name
                                if hasattr(tool_call.function, 'arguments') and tool_call.function.arguments:
                                    if "arguments" not in tool_calls[tool_call.index]["function"]:
                                        tool_calls[tool_call.index]["function"]["arguments"] = ""
                                    tool_calls[tool_call.index]["function"]["arguments"] += tool_call.function.arguments
                        
                        # 处理普通内容，优化分块输出
                        elif hasattr(choice.delta, 'content') and choice.delta.content is not None:
                            content = choice.delta.content
                            full_content += content
                            
                            # 对于大块内容，可以考虑按标点符号或固定长度分块
                            if len(content) > 100:  # 超过100字符的大块内容
                                # 寻找合适的分块点
                                split_points = [i for i, c in enumerate(content) if c in ['.', '!', '?', '，', '。', '！', '？']]
                                if split_points:
                                    # 有标点符号，按标点分块
                                    last_idx = 0
                                    for idx in split_points:
                                        yield {
                                            "role": "assistant",
                                            "content": content[last_idx:idx+1],
                                            "finish_reason": None,
                                            "stream": True
                                        }
                                        last_idx = idx + 1
                                    # 发送剩余部分
                                    if last_idx < len(content):
                                        yield {
                                            "role": "assistant",
                                            "content": content[last_idx:],
                                            "finish_reason": None,
                                            "stream": True
                                        }
                                else:
                                    # 没有标点符号，按固定长度分块
                                    for i in range(0, len(content), 100):
                                        yield {
                                            "role": "assistant",
                                            "content": content[i:i+100],
                                            "finish_reason": None,
                                            "stream": True
                                        }
                            else:
                                # 小块内容直接发送
                                yield {
                                    "role": "assistant",
                                    "content": content,
                                    "finish_reason": None,
                                    "stream": True
                                }
                        
                        # 处理完成标志
                        elif choice.finish_reason is not None:
                            # 检查是否有工具调用需要处理
                            if tool_calls:
                                try:
                                    # 处理工具调用并获取结果
                                    tool_response = await self._handle_tool_calls(tool_calls, conversation_id, original_messages)
                                    
                                    # 由于_tool_calls返回的是非流式响应，我们需要模拟流式输出
                                    if tool_response and isinstance(tool_response, dict) and "content" in tool_response:
                                        # 这里可以根据需要将内容分块输出
                                        content = tool_response["content"]
                                        
                                        # 对于大块内容，可以考虑按标点符号或固定长度分块
                                        if len(content) > 100:  # 超过100字符的大块内容
                                            # 寻找合适的分块点
                                            split_points = [i for i, c in enumerate(content) if c in ['.', '!', '?', '，', '。', '！', '？']]
                                            if split_points:
                                                # 有标点符号，按标点分块
                                                last_idx = 0
                                                for idx in split_points:
                                                    yield {
                                                        "role": "assistant",
                                                        "content": content[last_idx:idx+1],
                                                        "finish_reason": None,
                                                        "stream": True
                                                    }
                                                    last_idx = idx + 1
                                                # 发送剩余部分
                                                if last_idx < len(content):
                                                    yield {
                                                        "role": "assistant",
                                                        "content": content[last_idx:],
                                                        "finish_reason": "stop",
                                                        "stream": True
                                                    }
                                            else:
                                                # 没有标点符号，按固定长度分块
                                                for i in range(0, len(content), 100):
                                                    is_last_chunk = i + 100 >= len(content)
                                                    yield {
                                                        "role": "assistant",
                                                        "content": content[i:i+100],
                                                        "finish_reason": "stop" if is_last_chunk else None,
                                                        "stream": True
                                                    }
                                        else:
                                            # 小块内容直接发送
                                            yield {
                                                "role": "assistant",
                                                "content": content,
                                                "finish_reason": "stop",
                                                "stream": True
                                            }
                                    else:
                                        # 工具调用返回的结果不符合预期
                                        log.error(f"工具调用返回的结果不符合预期: {type(tool_response)}")
                                        yield {
                                            "role": "assistant",
                                            "content": "工具调用处理失败",
                                            "finish_reason": "error",
                                            "stream": True
                                        }
                                except Exception as e:
                                    log.error(f"处理工具调用时出错: {e}")
                                    yield {
                                        "role": "assistant",
                                        "content": f"处理工具调用时出错: {str(e)}",
                                        "finish_reason": "error",
                                        "stream": True
                                    }
                            else:
                                # 保存到记忆
                                if conversation_id and full_content:
                                    # 创建异步任务但不等待其完成
                                    # 构建响应对象
                                    response = {"role": "assistant", "content": full_content}
                                    # 传递正确的参数给_save_memory_to_chat_memory
                                    asyncio.create_task(self._save_memory_to_chat_memory(
                                        original_messages,  # 完整的消息历史
                                        response,           # 助手的响应
                                        conversation_id     # 对话ID
                                    ))
                                
                                # 发送结束标志
                                yield {
                                    "role": "assistant",
                                    "content": "",
                                    "finish_reason": "stop",
                                    "stream": True
                                }
            except Exception as e:
                log.error(f"异步迭代响应时出错: {e}")
                # 确保返回有效的异步生成器
                yield {
                    "role": "assistant",
                    "content": f"发生内部错误: {str(e)}",
                    "finish_reason": "error",
                    "stream": True
                }
        except Exception as e:
            log.error(f"处理流式响应时出错: {e}")
            # 确保返回有效的异步生成器
            yield {
                "role": "assistant",
                "content": "发生内部错误: 无法处理响应",
                "finish_reason": "error",
                "stream": True
            }
        finally:
            # 记录总响应时间
            total_time = time.time() - start_time
            log.debug(f"流式响应处理完成，总耗时: {total_time:.3f}秒, 分块数量: {chunk_count}")
            if first_chunk_time:
                log.debug(f"首字节响应时间: {first_chunk_time - start_time:.3f}秒")
    
    async def _handle_tool_calls(
        self,
        tool_calls: list,
        conversation_id: str,
        original_messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """处理工具调用并获取模型对工具结果的响应"""
        try:
            # 准备工具调用列表
            calls_to_execute = []
            for tool_call in tool_calls:
                calls_to_execute.append({
                    "name": tool_call["function"]["name"],
                    "parameters": json.loads(tool_call["function"]["arguments"])
                })
            
            # 并行执行所有工具调用
            tool_results = await self.tool_manager.execute_tools_concurrently(calls_to_execute)
            
            # 构建工具调用响应消息
            tool_response_messages = []
            for i, result in enumerate(tool_results):
                tool_call = tool_calls[i]
                if result["success"]:
                    content = f"工具 '{result['tool_name']}' 调用结果: {json.dumps(result['result'])}"
                else:
                    content = f"工具 '{result['tool_name']}' 调用失败: {result.get('error', '未知错误')}"
                
                tool_response_messages.append({
                    "tool_call_id": tool_call["id"],
                    "role": "tool",
                    "name": tool_call["function"]["name"],
                    "content": content
                })
            
            # 将工具调用结果添加到消息历史中，再次调用模型
            new_messages = original_messages.copy()
            # 添加助手的工具调用消息
            assistant_tool_call_msg = {"role": "assistant", "tool_calls": tool_calls}
            new_messages.append(assistant_tool_call_msg)
            # 添加工具响应消息
            new_messages.extend(tool_response_messages)
            
            # 重新生成响应 - 明确设置stream=False
            # 确保generate_response返回字典而不是异步生成器
            response = await self.generate_response(new_messages, conversation_id, use_tools=False, stream=False)
            
            # 确保返回值始终是一个有效的字典
            if response is None:
                return {"content": "未能生成响应"}
            elif isinstance(response, dict):
                return response
            else:
                # 如果返回的不是字典，尝试转换或返回默认值
                return {"content": str(response) if response else "未能生成响应"}
        except Exception as e:
            log.error(f"处理工具调用时出错: {e}")
            return {"content": f"处理工具调用时出错: {str(e)}"}
    
    async def _handle_non_streaming_response(self, response, messages: List[Dict[str, str]], conversation_id: str) -> Dict[str, Any]:
        """处理非流式响应"""
        # 确保返回的是字典而不是异步生成器
        if hasattr(response, 'choices') and response.choices:
            message = response.choices[0].message
            result = {
                "role": "health_assistant",  # 与测试期望的role保持一致
                "content": message.content
            }
            
            # 提取usage信息
            if hasattr(response, 'usage'):
                result["usage"] = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            # 如果是本地客户端，需要手动保存记忆
            if self.is_local_client and conversation_id != "default" and messages:
                self._save_memory_to_chat_memory(messages, result, conversation_id)
                
            return result
        
        return {"role": "health_assistant", "content": "抱歉，未能生成响应。"}
    
    async def _fallback_to_openai(self, messages: List[Dict[str, str]], conversation_id: str, 
                                personality_id: Optional[str], use_tools: bool, stream: bool) -> Any:
        """降级到直接调用OpenAI API"""
        try:
            if not self.openai_client:
                raise Exception("OpenAI客户端未初始化")
            
            # 应用人格
            if personality_id:
                messages = self.personality_manager.apply_personality(messages, personality_id)
            
            # 准备调用参数
            call_params = {
                "messages": messages,
                "model": self.config.OPENAI_MODEL,
                "stream": stream,
                "temperature": float(self.config.OPENAI_TEMPERATURE)
            }
            
            # 添加工具相关配置
            if use_tools:
                # 使用tool_registry获取工具的函数调用模式
                from services.tools.registry import tool_registry
                tools = tool_registry.get_functions_schema()
                if tools:
                    call_params["tools"] = tools
                    call_params["tool_choice"] = "auto"
            
            response = self.openai_client.chat.completions.create(**call_params)
            
            if stream:
                # 处理流式响应 - 添加与generate_response相同的错误处理
                try:
                    # 先检查response是否有效
                    if response is None:
                        log.error("OpenAI API返回的响应为None")
                        # 创建一个简单的错误响应生成器
                        async def error_generator():
                            yield {
                                "role": "assistant",
                                "content": "发生内部错误: 服务响应为空",
                                "finish_reason": "error",
                                "stream": True
                            }
                        return error_generator()
                     
                    # 确保response是可异步迭代的
                    if not hasattr(response, '__aiter__'):
                        log.error(f"OpenAI API返回的响应不是异步迭代器: {type(response)}")
                        # 创建一个简单的错误响应生成器
                        async def error_generator():
                            yield {
                                "role": "assistant",
                                "content": "发生内部错误: 无法处理响应格式",
                                "finish_reason": "error",
                                "stream": True
                            }
                        return error_generator()
                     
                    # 确保_handle_streaming_response返回的是一个异步生成器
                    streaming_result = self._handle_streaming_response(response, conversation_id, messages)
                    if not hasattr(streaming_result, '__aiter__'):
                        log.error(f"_handle_streaming_response返回的不是异步生成器: {type(streaming_result)}")
                        # 创建一个简单的错误响应生成器
                        async def error_generator():
                            yield {
                                "role": "assistant",
                                "content": "发生内部错误: 流式响应处理失败",
                                "finish_reason": "error",
                                "stream": True
                            }
                        return error_generator()
                    return streaming_result
                except Exception as e:
                    log.error(f"准备流式响应时出错: {e}")
                    # 创建一个简单的错误响应生成器
                    async def error_generator():
                        yield {
                            "role": "assistant",
                            "content": f"发生内部错误: {str(e)}",
                            "finish_reason": "error",
                            "stream": True
                        }
                    return error_generator()
            else:
                # 处理非流式响应
                result = await self._handle_non_streaming_response(response, messages, conversation_id)
                # 确保返回的是字典而不是异步生成器
                if hasattr(result, '__aiter__'):
                    # 如果是异步生成器，获取第一个结果
                    async for chunk in result:
                        return chunk
                return result
        except Exception as fallback_error:
            log.error(f"降级到OpenAI API也失败: {fallback_error}")
            # 返回错误响应
            if stream:
                # 对于流式响应，返回一个异步生成器
                async def error_generator():
                    yield {"stream": True, "content": f"发生错误: {str(fallback_error)}", "finish_reason": "error"}
                return error_generator()
            else:
                return {"role": "assistant", "content": f"发生错误: {str(fallback_error)}"}
                
    def _save_memory_to_chat_memory(self, messages: List[Dict[str, str]], response: Dict[str, Any], conversation_id: str):
        """保存记忆到聊天记忆系统"""
        try:
            # 只保存用户和助手的最后一条消息
            user_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg
                    break
            
            if user_message and response.get("content"):
                # 异步保存消息到记忆
                asyncio.create_task(self.async_chat_memory.add_message(
                    conversation_id=conversation_id,
                    message={"role": "user", "content": user_message.get("content", "")}
                ))
                
                asyncio.create_task(self.async_chat_memory.add_message(
                    conversation_id=conversation_id,
                    message={"role": "assistant", "content": response.get("content", "")}
                ))
        except Exception as e:
            log.error(f"保存记忆失败: {e}")
            
    def clear_conversation_memory(self, conversation_id: str):
        """清除指定会话的记忆"""
        try:
            self.chat_memory.clear_memory(conversation_id)
            log.debug(f"Cleared memory for conversation: {conversation_id}")
        except Exception as e:
            log.error(f"Failed to clear memory: {e}")
            
    def get_conversation_memory(self, conversation_id: str) -> List[Dict[str, Any]]:
        """获取指定会话的记忆"""
        try:
            memories = self.chat_memory.get_memory(conversation_id)
            log.debug(f"Retrieved {len(memories)} memories for conversation: {conversation_id}")
            return memories
        except Exception as e:
            log.error(f"Failed to get memory: {e}")
            return []
            
    def call_mcp_service(self, tool_name: str = None, params: dict = None, 
                         service_name: str = None, method_name: str = None, 
                         mcp_server: str = None):
        """调用MCP服务"""
        try:
            # 参数验证
            params = params or {}
            
            # 确定工具名称
            if not tool_name:
                if not service_name or not method_name:
                    raise ValueError("Either 'tool_name' or both 'service_name' and 'method_name' must be provided")
                tool_name = f"{service_name}__{method_name}"
            
            log.info(f"Calling MCP service: {tool_name}, params: {params}, server: {mcp_server or 'auto'}")
            
            # 使用MCP管理器调用服务，支持指定服务器
            result = mcp_manager.call_tool(tool_name, params, mcp_server)
            
            # 更灵活的结果处理
            processed_result = []
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict) and 'text' in item:
                        processed_result.append(item['text'])
                    else:
                        processed_result.append(str(item))
                response_text = "\n".join(processed_result) if processed_result else str(result)
            else:
                response_text = str(result)
            
            return {"success": True, "result": response_text, "raw_result": result}
        except MCPServerNotFoundError as e:
            log.error(f"MCP server error: {str(e)}")
            return {"success": False, "error": f"MCP服务器错误: {str(e)}"}
        except MCPToolNotFoundError as e:
            log.error(f"MCP tool error: {str(e)}")
            return {"success": False, "error": f"MCP工具错误: {str(e)}"}
        except MCPServiceError as e:
            log.error(f"MCP service error: {str(e)}")
            return {"success": False, "error": f"MCP服务调用失败: {str(e)}"}
        except Exception as e:
            log.error(f"Unexpected error when calling MCP service: {str(e)}")
            return {"success": False, "error": f"调用MCP服务时发生未知错误: {str(e)}"}

# 创建全局实例
def get_mem0_proxy():
    """获取全局的Mem0ProxyManager实例"""
    global _mem0_proxy
    try:
        return _mem0_proxy
    except NameError:
        _mem0_proxy = Mem0ProxyManager()
        return _mem0_proxy

# 性能比较说明
"""
项目当前实现 vs Mem0官方Proxy实现的性能比较：

1. 项目当前实现（ChatEngine + ChatMemory）：
   - 优点：功能更丰富，错误处理更完善，与系统集成更紧密
   - 缺点：处理链更长，可能导致额外的几秒钟延迟
   - 主要耗时点：记忆检索、token估算、消息预处理、格式转换等

2. 本文件中的Mem0 Proxy实现：
   - 优点：更接近官方示例，性能更好，启动速度更快
   - 缺点：功能相对简单，与项目其他组件（如人格系统）集成度较低
   - 优化点：减少了中间处理步骤，直接使用Mem0的代理接口

选择建议：
- 如果更看重性能和启动速度，可以考虑使用本文件中的实现
- 如果需要更丰富的功能和更好的系统集成，建议保持当前实现
- 也可以考虑混合使用：对于新会话使用Proxy实现快速启动，后续交互使用完整实现
"""