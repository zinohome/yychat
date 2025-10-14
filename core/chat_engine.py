import asyncio
import time
import json
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
from openai import OpenAI
from config.config import get_config
from utils.log import log
from core.chat_memory import ChatMemory, get_async_chat_memory
from core.personality_manager import PersonalityManager
from services.tools.manager import ToolManager
import httpx
from services.tools.registry import tool_registry
from services.mcp.manager import get_mcp_manager
from services.mcp.exceptions import MCPServiceError, MCPServerNotFoundError, MCPToolNotFoundError
# 新增模块导入
from core.openai_client import AsyncOpenAIWrapper
from core.request_builder import build_request_params
from core.tools_adapter import normalize_tool_calls, build_tool_response_messages
from core.token_budget import should_include_memory
from core.prompt_builder import compose_system_prompt
# 性能监控
from utils.performance import performance_monitor, PerformanceMetrics
import uuid
# 基类导入
from core.base_engine import BaseEngine, EngineCapabilities, EngineStatus


config = get_config()

class ChatEngine(BaseEngine):
    def __init__(self):
        # 初始化同步客户端
        self.sync_client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL,
            timeout=config.OPENAI_API_TIMEOUT,
            http_client=httpx.Client(
                follow_redirects=True,
                verify=config.VERIFY_SSL,
                http2=True,
                timeout=httpx.Timeout(
                    connect=config.OPENAI_CONNECT_TIMEOUT,
                    read=config.OPENAI_READ_TIMEOUT,
                    write=config.OPENAI_WRITE_TIMEOUT,
                    pool=config.OPENAI_POOL_TIMEOUT
                ),
                limits=httpx.Limits(
                    max_connections=config.MAX_CONNECTIONS,
                    max_keepalive_connections=config.MAX_KEEPALIVE_CONNECTIONS,
                    keepalive_expiry=config.KEEPALIVE_EXPIRY
                )
            )
        )
        # 包装为异步客户端
        self.client = AsyncOpenAIWrapper(self.sync_client)
        self.chat_memory = None
        self.async_chat_memory = None
        self.personality_manager = None
        self.tool_manager = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """确保组件已初始化（延迟初始化）"""
        if not self._initialized:
            log.info("ChatEngine: 开始延迟初始化组件...")
            self.chat_memory = ChatMemory()
            self.async_chat_memory = get_async_chat_memory()
            self.personality_manager = PersonalityManager()
            self.tool_manager = ToolManager()
            self._initialized = True
            log.info("ChatEngine: 延迟初始化完成")
       
    # 在generate_response方法中添加性能监控
    async def generate_response(self, messages: List[Dict[str, str]], conversation_id: str = "default", 
                               personality_id: Optional[str] = None, use_tools: Optional[bool] = None, 
                               stream: Optional[bool] = None) -> Any:
        # 确保组件已初始化
        self._ensure_initialized()
        
        # 记录总请求处理开始时间
        total_start_time = time.time()
        
        # 创建性能指标对象
        metrics = PerformanceMetrics(
            request_id=str(uuid.uuid4())[:8],
            timestamp=total_start_time,
            stream=stream if stream is not None else config.STREAM_DEFAULT,
            use_tools=use_tools if use_tools is not None else config.USE_TOOLS_DEFAULT,
            personality_id=personality_id
        )
        try:
            # 验证输入参数
            if not messages or not isinstance(messages, list):
                error_msg = "消息列表不能为空且必须是列表类型"
                log.error(error_msg)
                if stream:
                    async def error_gen():
                        yield {"role": "assistant", "content": error_msg, "finish_reason": "error", "stream": True}
                    return error_gen()
                return {"role": "assistant", "content": error_msg}
            
            # 验证每条消息格式
            for idx, msg in enumerate(messages):
                if not isinstance(msg, dict):
                    error_msg = f"消息 #{idx} 格式错误：必须是字典类型"
                    log.error(error_msg)
                    if stream:
                        async def error_gen():
                            yield {"role": "assistant", "content": error_msg, "finish_reason": "error", "stream": True}
                        return error_gen()
                    return {"role": "assistant", "content": error_msg}
                if "role" not in msg or "content" not in msg:
                    error_msg = f"消息 #{idx} 格式错误：缺少必需的 'role' 或 'content' 字段"
                    log.error(error_msg)
                    if stream:
                        async def error_gen():
                            yield {"role": "assistant", "content": error_msg, "finish_reason": "error", "stream": True}
                        return error_gen()
                    return {"role": "assistant", "content": error_msg}
            
            # 打印传入的参数值，用于调试
            log.debug(f"传入参数 - personality_id: {personality_id}, use_tools: {use_tools}, stream: {stream}, type(personality_id): {type(personality_id)}, type(use_tools): {type(use_tools)}, type(stream): {type(stream)}")
            
            # 创建messages的深拷贝，避免修改原始列表
            messages_copy = [msg.copy() for msg in messages]
            # 若历史过长，仅保留最后3条，减少请求体体积
            if len(messages_copy) > 3:
                messages_copy = messages_copy[-3:]
            
            log.debug(f"原始消息: {messages_copy}")
            
            # 如果没有指定人格ID，使用默认人格
            if personality_id is None:
                personality_id = config.DEFAULT_PERSONALITY
                log.info(f"未指定人格ID，使用默认人格: {personality_id}")
            
            # 如果没有指定use_tools，使用默认值
            if use_tools is None:
                use_tools = config.USE_TOOLS_DEFAULT
                log.info(f"未指定use_tools，使用默认值: {use_tools}")
            
            # 如果没有指定stream，使用默认值
            if stream is None:
                stream = config.STREAM_DEFAULT
                log.info(f"未指定stream，使用默认值: {stream}")
            
            # 获取记忆和人格信息
            memory_section = ""
            personality_system = ""
            
            # 从记忆中检索相关内容
            if config.ENABLE_MEMORY_RETRIEVAL and conversation_id != "default" and messages_copy:
                memory_start = time.time()
                relevant_memories = await self.async_chat_memory.get_relevant_memory(conversation_id, messages_copy[-1]["content"])
                metrics.memory_retrieval_time = time.time() - memory_start
                
                # 检查是否命中缓存（通过检索时间判断）
                metrics.memory_cache_hit = metrics.memory_retrieval_time < 0.01  # 小于10ms认为是缓存命中
                
                if relevant_memories:
                    memory_text = "\n".join(relevant_memories)
                    memory_section = f"参考记忆：\n{memory_text}"
                    log.debug(f"检索到相关记忆 {len(relevant_memories)} 条")
                    
                    # 使用新的token预算模块检查是否应该包含记忆
                    max_tokens = getattr(config, 'OPENAI_MAX_TOKENS', 8192)
                    if not should_include_memory(messages_copy, memory_section, max_tokens):
                        log.warning("避免超出模型token限制，不添加记忆到系统提示")
                        memory_section = ""
            elif not config.ENABLE_MEMORY_RETRIEVAL:
                log.debug("Memory检索已禁用")
            
            # 获取人格的系统提示
            if personality_id:
                try:
                    personality = self.personality_manager.get_personality(personality_id)
                    if personality:
                        personality_system = personality.system_prompt or ""
                except Exception as e:
                    log.warning(f"获取人格时出错，忽略人格设置: {e}")
            
            # 使用新的提示构建器合成系统提示
            messages_copy = compose_system_prompt(messages_copy, personality_system, memory_section)
            log.debug(f"合成系统提示后消息: {messages_copy}")
            
            # 使用新的方法获取允许的工具schema（已根据personality过滤）
            allowed_tools_schema = await self.get_allowed_tools_schema(personality_id) if use_tools else None
            request_params = build_request_params(
                model=config.OPENAI_MODEL,
                temperature=float(config.OPENAI_TEMPERATURE),
                messages=messages_copy,
                use_tools=use_tools,
                all_tools_schema=allowed_tools_schema,
                allowed_tool_names=None  # 不再需要单独传递，已在schema中过滤
            )
            
            log.debug(f"最终请求参数: {request_params}")
            # 记录总请求处理时间
            log.debug(f"总请求处理时间一: {time.time() - total_start_time:.2f}秒")
            if stream:
                # 包装异步生成器以确保性能指标被记录
                return self._wrap_streaming_response_with_performance(
                    self._generate_streaming_response(request_params, conversation_id, messages, personality_id, metrics),
                    metrics, total_start_time
                )
            else:
                result = await self._generate_non_streaming_response(request_params, conversation_id, messages, personality_id, metrics)
                
                # 记录性能指标
                metrics.total_time = time.time() - total_start_time
                if config.ENABLE_PERFORMANCE_MONITOR:
                    performance_monitor.record(metrics, log_enabled=config.PERFORMANCE_LOG_ENABLED)
                
                return result
        except Exception as e:
            log.error(f"Error in generate_response: {e}")
            # 返回适当的错误响应对象，而不是简单的错误字典
            if stream:
                # 对于流式响应，返回一个可以异步迭代的对象
                async def error_generator():
                    yield {
                        "role": "assistant",
                        "content": f"发生错误: {str(e)}",
                        "finish_reason": "error",
                        "stream": True
                    }
                return error_generator()
            else:
                # 对于非流式响应，返回标准的错误消息格式
                return {"role": "assistant", "content": f"发生错误: {str(e)}"}
    
    async def _generate_non_streaming_response(
        self,
        request_params: Dict[str, Any],
        conversation_id: str,
        original_messages: List[Dict[str, str]],
        personality_id: Optional[str] = None,
        metrics: Optional[PerformanceMetrics] = None
    ) -> Dict[str, Any]:
        try:
            # 调用异步OpenAI API
            response = await self.client.create_chat(request_params)
            log.debug(f"OpenAI API响应: {response}")
            
            # 增加响应格式验证
            if not hasattr(response, 'choices') or not response.choices:
                log.error(f"Invalid API response format: {dir(response)}")
                return {"role": "assistant", "content": "获取AI响应时发生格式错误，请检查API配置。"}
            
            # 处理响应
            if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                # 处理工具调用
                return await self._handle_tool_calls(
                    response.choices[0].message.tool_calls,
                    conversation_id,
                    original_messages,
                    personality_id
                )
            else:
                # 确保content存在
                if not hasattr(response.choices[0].message, 'content') or response.choices[0].message.content is None:
                    log.error(f"Response missing content: {response}")
                    return {"role": "assistant", "content": "AI响应内容为空，请检查API配置。"}
                
                # 普通响应
                content = response.choices[0].message.content
                
                # 保存到记忆 - 使用原生异步API
                if conversation_id:
                    # 创建异步任务但不等待其完成
                    asyncio.create_task(self._async_save_message_to_memory(
                        conversation_id, 
                        [{"role": "assistant", "content": content}, original_messages[-1]]
                    ))
                
                return {
                    "role": "assistant",
                    "content": content,
                    "model": response.model if hasattr(response, 'model') else "unknown",
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') and response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') and response.usage else 0,
                        "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0
                    }
                }
                
        except json.JSONDecodeError as e:
            log.error(f"JSON解析错误: {e}. 请检查API端点是否正确且返回有效JSON格式。")
            return {"role": "assistant", "content": "API返回内容格式错误，请确认API端点配置正确。"}
        except Exception as e:
            log.error(f"生成响应时出错: {e}")
            # 尝试获取更详细的错误信息
            detailed_error = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                detailed_error += f"\n响应内容: {e.response.text[:200]}..."
            return {"role": "assistant", "content": f"抱歉，我现在无法为您提供帮助。错误信息: {detailed_error}"}
    
    async def _wrap_streaming_response_with_performance(
        self, 
        streaming_generator: AsyncGenerator[Dict[str, Any], None], 
        metrics: PerformanceMetrics, 
        total_start_time: float
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """包装流式响应生成器，确保性能指标被记录"""
        log.info(f"[PERF WRAPPER] 开始包装流式响应，request_id={metrics.request_id}")
        first_chunk_time = None
        chunk_count = 0
        
        try:
            async for chunk in streaming_generator:
                chunk_count += 1
                if chunk_count == 1:
                    first_chunk_time = time.time()
                    log.debug(f"流式响应首字节时间: {first_chunk_time - total_start_time:.2f}秒")
                
                #log.debug(f"流式响应chunk {chunk_count}: {chunk}")
                yield chunk
                
        except Exception as e:
            log.error(f"流式响应包装器出错: {e}")
            # 重新抛出异常
            raise e
        finally:
            # 无论是否发生异常，都记录性能指标
            log.info(f"[PERF WRAPPER] 流式响应完成（finally块），chunk_count={chunk_count}")
            metrics.total_time = time.time() - total_start_time
            if first_chunk_time:
                metrics.first_chunk_time = first_chunk_time - total_start_time
            metrics.openai_api_time = metrics.total_time  # 流式响应中，总时间就是API时间
            
            log.info(f"[PERF WRAPPER] 准备记录性能指标: ENABLE={config.ENABLE_PERFORMANCE_MONITOR}, total_time={metrics.total_time:.3f}s")
            if config.ENABLE_PERFORMANCE_MONITOR:
                log.info(f"[PERF] 记录流式响应性能指标: total_time={metrics.total_time:.3f}s, chunks={chunk_count}, stream=True")
                performance_monitor.record(metrics, log_enabled=config.PERFORMANCE_LOG_ENABLED)
                log.info(f"[PERF] 性能指标已记录")
    
    async def _generate_streaming_response(
        self, 
        request_params: Dict[str, Any],
        conversation_id: str,
        original_messages: List[Dict[str, str]],
        personality_id: Optional[str] = None,
        metrics: Optional[PerformanceMetrics] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            # 记录API调用开始时间
            api_start_time = time.time()
            
            # 初始化变量
            tool_calls = None
            full_content = ""
            chunk_count = 0
            first_chunk_time = None
            
            # 使用异步流式API
            async for chunk in self.client.create_chat_stream(request_params):
                chunk_count += 1
                if chunk_count == 1:
                    first_chunk_time = time.time()
                    log.debug(f"首字节响应时间: {first_chunk_time - api_start_time:.2f}秒")
                    
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    
                    # 检测工具调用
                    if hasattr(choice.delta, 'tool_calls') and choice.delta.tool_calls:
                        if not tool_calls:
                            tool_calls = []
                        # 收集工具调用信息
                        for tool_call in choice.delta.tool_calls:
                            log.debug(f"收到工具调用 chunk: index={tool_call.index}, id={getattr(tool_call, 'id', None)}, "
                                     f"has_function={hasattr(tool_call, 'function')}, "
                                     f"function={getattr(tool_call, 'function', None)}")
                            
                            # 初始化或更新工具调用信息
                            if tool_call.index >= len(tool_calls):
                                tool_calls.append({"id": None, "type": "function", "function": {}})
                            
                            # 更新 ID（可能在后续 chunk 中才提供）
                            if hasattr(tool_call, 'id') and tool_call.id:
                                tool_calls[tool_call.index]["id"] = tool_call.id
                                log.debug(f"更新工具调用 ID: index={tool_call.index}, id={tool_call.id}")
                            
                            # 更新函数名称和参数
                            if hasattr(tool_call, 'function') and tool_call.function:
                                if hasattr(tool_call.function, 'name') and tool_call.function.name:
                                    tool_calls[tool_call.index]["function"]["name"] = tool_call.function.name
                                    log.debug(f"更新工具名称: index={tool_call.index}, name={tool_call.function.name}")
                                if hasattr(tool_call.function, 'arguments') and tool_call.function.arguments:
                                    if "arguments" not in tool_calls[tool_call.index]["function"]:
                                        tool_calls[tool_call.index]["function"]["arguments"] = ""
                                    tool_calls[tool_call.index]["function"]["arguments"] += tool_call.function.arguments
                                    log.debug(f"累加工具参数: index={tool_call.index}, 当前长度={len(tool_calls[tool_call.index]['function']['arguments'])}")
                    
                    # 处理普通内容，优化分块输出
                    elif choice.delta.content is not None:
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
            
            # 检查是否有工具调用需要处理
            if tool_calls:
                log.debug(f"收集到的工具调用原始数据: {tool_calls}")
                
                # 验证所有工具调用都有有效的 ID
                for idx, call in enumerate(tool_calls):
                    if not call.get("id"):
                        # 生成一个临时 ID
                        call["id"] = f"call_{idx}_{int(time.time() * 1000)}"
                        log.warning(f"工具调用 #{idx} 缺少 ID，已生成临时 ID: {call['id']}")
                
                log.debug(f"验证后的工具调用数据: {tool_calls}")
                
                # 使用新的工具适配器规范化工具调用
                normalized_calls = normalize_tool_calls(tool_calls)
                log.debug(f"规范化后的工具调用: {normalized_calls}")
                
                # 准备工具调用列表
                calls_to_execute = []
                for call in normalized_calls:
                    # 安全地解析 JSON 参数
                    args_str = call["function"]["arguments"]
                    try:
                        parameters = json.loads(args_str) if args_str else {}
                    except json.JSONDecodeError as e:
                        log.error(f"工具参数 JSON 解析失败: {args_str}, 错误: {e}")
                        parameters = {}
                    
                    calls_to_execute.append({
                        "name": call["function"]["name"],
                        "parameters": parameters
                    })
                
                # 并行执行所有工具调用
                tool_results = await self.tool_manager.execute_tools_concurrently(calls_to_execute)
                
                # 使用新的工具适配器构建工具响应消息
                tool_response_messages = build_tool_response_messages(normalized_calls, tool_results)
                
                # 构建新的消息历史（包含工具调用和结果）
                new_messages = original_messages.copy()
                assistant_message_with_tools = {"role": "assistant", "tool_calls": normalized_calls}
                log.debug(f"准备发送的 assistant 消息: {assistant_message_with_tools}")
                new_messages.append(assistant_message_with_tools)
                new_messages.extend(tool_response_messages)
                log.debug(f"完整的新消息历史（共{len(new_messages)}条）: {json.dumps(new_messages, ensure_ascii=False, indent=2)}")
                
                # 获取 personality 系统提示并添加到消息中
                personality_system_prompt = ""
                if personality_id:
                    try:
                        personality = self.personality_manager.get_personality(personality_id)
                        if personality:
                            personality_system_prompt = personality.system_prompt or ""
                    except Exception as e:
                        log.warning(f"获取人格时出错: {e}")
                
                # 使用 compose_system_prompt 添加系统提示
                new_messages_with_system = compose_system_prompt(new_messages, personality_system_prompt, "")
                log.debug(f"添加系统提示后的消息（共{len(new_messages_with_system)}条）")
                
                # 重新构建请求参数，继续流式生成
                follow_up_params = build_request_params(
                    model=config.OPENAI_MODEL,
                    temperature=float(config.OPENAI_TEMPERATURE),
                    messages=new_messages_with_system,  # 使用包含系统提示的消息
                    use_tools=False,  # 工具调用后不再使用工具
                    all_tools_schema=None,
                    allowed_tool_names=None,
                    force_tool_from_message=False  # 不强制选择工具
                )
                
                # 继续流式输出工具调用后的回答
                follow_up_content = ""
                async for follow_up_chunk in self.client.create_chat_stream(follow_up_params):
                    if follow_up_chunk.choices and len(follow_up_chunk.choices) > 0:
                        choice = follow_up_chunk.choices[0]
                        if choice.delta.content is not None:
                            follow_up_content += choice.delta.content
                            yield {
                                "role": "assistant",
                                "content": choice.delta.content,
                                "finish_reason": None,
                                "stream": True
                            }
                
                # 保存工具调用后的响应到记忆
                if conversation_id and follow_up_content:
                    asyncio.create_task(self._async_save_message_to_memory(
                        conversation_id, 
                        [{"role": "assistant", "content": follow_up_content}, original_messages[-1]]
                    ))
                
                # 发送结束标志
                    yield {
                        "role": "assistant",
                    "content": "",
                        "finish_reason": "stop",
                        "stream": True
                    }
            else:
                # 保存到记忆 - 使用原生异步API
                if conversation_id and full_content:
                    # 创建异步任务但不等待其完成
                    asyncio.create_task(self._async_save_message_to_memory(
                        conversation_id, 
                        [{"role": "assistant", "content": full_content}, original_messages[-1]]
                    ))
                
                # 发送结束标志
                yield {
                    "role": "assistant",
                    "content": "",
                    "finish_reason": "stop",
                    "stream": True
                }
            log.debug(f"总块数: {chunk_count}, 总处理时间: {time.time() - api_start_time:.2f}秒")
        except Exception as e:
            log.error(f"Error generating streaming response: {e}")
            yield {
                "role": "assistant",
                "content": f"抱歉，我现在无法为您提供帮助。错误信息: {str(e)}",
                "finish_reason": "error",
                "stream": True
            }
    
    async def _handle_tool_calls(
        self,
        tool_calls: list,
        conversation_id: str,
        original_messages: List[Dict[str, str]],
        personality_id: Optional[str] = None
    ) -> Dict[str, Any]:
        # 使用新的工具适配器规范化工具调用
        normalized_calls = normalize_tool_calls(tool_calls)
        
        # 准备工具调用列表
        calls_to_execute = []
        for call in normalized_calls:
            # 安全地解析 JSON 参数
            args_str = call["function"]["arguments"]
            try:
                parameters = json.loads(args_str) if args_str else {}
            except json.JSONDecodeError as e:
                log.error(f"工具参数 JSON 解析失败: {args_str}, 错误: {e}")
                parameters = {}
            
            calls_to_execute.append({
                "name": call["function"]["name"],
                "parameters": parameters
            })
        
        # 并行执行所有工具调用
        tool_results = await self.tool_manager.execute_tools_concurrently(calls_to_execute)
        
        # 使用新的工具适配器构建工具响应消息
        tool_response_messages = build_tool_response_messages(normalized_calls, tool_results)
        
        # 将工具调用结果添加到消息历史中，再次调用模型
        new_messages = original_messages.copy()
        new_messages.append({"role": "assistant", "tool_calls": normalized_calls})
        new_messages.extend(tool_response_messages)
        
        # 重新生成响应 - 明确设置stream=False，传递personality_id避免重复应用
        return await self.generate_response(new_messages, conversation_id, personality_id=personality_id, use_tools=False, stream=False)
    
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
            result = get_mcp_manager().call_tool(tool_name, params, mcp_server)
            
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

    # 清除会话记忆
    def clear_conversation_memory(self, conversation_id: str):
        self.chat_memory.delete_memory(conversation_id)
    
    # 获取会话记忆 - 同步版本
    def get_conversation_memory(self, conversation_id: str = "default") -> list:
        """获取对话的所有记忆，使用同步方法直接获取"""
        try:
            # 直接使用同步版本的chat_memory实例获取记忆
            memories = self.chat_memory.get_all_memory(conversation_id)
            log.debug(f"Successfully retrieved {len(memories)} memories for conversation {conversation_id}")
            return memories
        except Exception as e:
            log.error(f"Failed to get conversation memory: {e}")
            return []

    # 获取会话记忆 - 异步版本
    async def aget_conversation_memory(self, conversation_id: str) -> list:
        """获取会话记忆（异步版本）"""
        try:
            # 直接调用异步记忆实例的方法
            return await self.async_chat_memory.get_all_memory(conversation_id)
        except Exception as e:
            log.error(f"异步获取会话记忆时出错: {e}")
            return []

    # 异步保存消息到记忆 - 使用原生异步API
    async def _async_save_message_to_memory(self, conversation_id: str, messages: list):
        """异步保存消息到记忆，使用mem0的原生AsyncMemory API"""
        try:
            # 根据配置决定保存哪些消息
            messages_to_save = []
            
            if config.MEMORY_SAVE_MODE == "both":
                # 保存所有消息（助手回复和用户输入）
                messages_to_save = messages
            elif config.MEMORY_SAVE_MODE == "user_only":
                # 只保存用户输入的消息
                messages_to_save = [msg for msg in messages if msg.get("role") == "user"]
            elif config.MEMORY_SAVE_MODE == "assistant_only":
                # 只保存助手回复的消息
                messages_to_save = [msg for msg in messages if msg.get("role") == "assistant"]
            else:
                # 默认保存所有消息
                messages_to_save = messages
                log.warning(f"未知的MEMORY_SAVE_MODE配置值: {config.MEMORY_SAVE_MODE}，默认保存所有消息")
            
            if messages_to_save:
                log.debug(f"使用原生异步API保存消息到记忆: 模式={config.MEMORY_SAVE_MODE}, 消息数量={len(messages_to_save)}, conversation_id={conversation_id}")
                
                # 记录将要保存的消息内容（为了避免日志过大，可以只记录第一条和最后一条）
                if len(messages_to_save) > 0:
                    log.debug(f"第一条消息内容预览: {messages_to_save[0].get('content', '')[:100]}...")
                    if len(messages_to_save) > 1:
                        log.debug(f"最后一条消息内容预览: {messages_to_save[-1].get('content', '')[:100]}...")
                
                # 批量保存消息
                await self.async_chat_memory.add_messages_batch(conversation_id, messages_to_save)
                log.debug("使用原生异步API保存消息到记忆完成")
            else:
                log.debug(f"根据配置 MEMORY_SAVE_MODE={config.MEMORY_SAVE_MODE}，没有消息需要保存到记忆")
        except Exception as e:
            log.error(f"使用原生异步API保存消息到记忆失败: {e}", exc_info=True)

    # 保留原有的_save_message_to_memory_async方法以保持向后兼容
    async def _save_message_to_memory_async(self, conversation_id: str, message: dict):
        """异步保存消息到记忆，不阻塞主线程 - 为保持向后兼容性保留"""
        try:
            # 直接调用新的异步方法
            await self._async_save_message_to_memory(conversation_id, [message])
        except Exception as e:
            log.error(f"异步保存消息到记忆失败: {e}")
    
    # ========== BaseEngine接口实现 ==========
    
    async def get_engine_info(self) -> Dict[str, Any]:
        """获取引擎信息"""
        return {
            "name": "chat_engine",
            "version": "2.0.0",
            "features": [
                EngineCapabilities.MEMORY,
                EngineCapabilities.TOOLS,
                EngineCapabilities.PERSONALITY,
                EngineCapabilities.STREAMING,
                EngineCapabilities.PERFORMANCE_MONITORING,
                EngineCapabilities.CACHE,
                EngineCapabilities.MCP_INTEGRATION
            ],
            "status": EngineStatus.HEALTHY,
            "description": "主聊天引擎，集成Memory缓存、性能监控、工具调用和MCP"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        timestamp = time.time()
        errors = []
        
        # 检查OpenAI API
        openai_healthy = True
        try:
            # 简单测试，不实际调用API
            if not self.sync_client or not config.OPENAI_API_KEY:
                openai_healthy = False
                errors.append("OpenAI API配置不完整")
        except Exception as e:
            openai_healthy = False
            errors.append(f"OpenAI API检查失败: {str(e)}")
        
        # 检查Memory系统
        memory_healthy = True
        try:
            if not self.async_chat_memory:
                memory_healthy = False
                errors.append("Memory系统未初始化")
        except Exception as e:
            memory_healthy = False
            errors.append(f"Memory系统检查失败: {str(e)}")
        
        # 检查工具系统
        tool_healthy = True
        try:
            tool_count = len(tool_registry.list_tools())
            if tool_count == 0:
                log.warning("工具系统无可用工具")
        except Exception as e:
            tool_healthy = False
            errors.append(f"工具系统检查失败: {str(e)}")
        
        # 检查人格系统
        personality_healthy = True
        try:
            personalities = self.personality_manager.get_all_personalities()
            if not personalities:
                log.warning("人格系统无可用人格")
        except Exception as e:
            personality_healthy = False
            errors.append(f"人格系统检查失败: {str(e)}")
        
        # 综合判断
        all_healthy = openai_healthy and memory_healthy and tool_healthy and personality_healthy
        
        return {
            "healthy": all_healthy,
            "timestamp": timestamp,
            "details": {
                "openai_api": openai_healthy,
                "memory_system": memory_healthy,
                "tool_system": tool_healthy,
                "personality_system": personality_healthy
            },
            "errors": errors
        }
    
    async def clear_conversation_memory(self, conversation_id: str) -> Dict[str, Any]:
        """清除指定会话的记忆"""
        try:
            # 获取当前记忆数量
            current_memories = await self.async_chat_memory.get_all_memory(conversation_id)
            count_before = len(current_memories) if current_memories else 0
            
            # 清除记忆
            await self.async_chat_memory.delete_memory(conversation_id)
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "deleted_count": count_before,
                "message": f"已清除会话 {conversation_id} 的 {count_before} 条记忆"
            }
        except Exception as e:
            log.error(f"清除会话记忆失败: {e}")
            return {
                "success": False,
                "conversation_id": conversation_id,
                "deleted_count": 0,
                "message": f"清除失败: {str(e)}"
            }
    
    async def get_conversation_memory(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取指定会话的记忆"""
        try:
            # 获取所有记忆
            all_memories = await self.async_chat_memory.get_all_memory(conversation_id)
            
            if not all_memories:
                return {
                    "success": True,
                    "conversation_id": conversation_id,
                    "memories": [],
                    "total_count": 0,
                    "returned_count": 0
                }
            
            total_count = len(all_memories)
            
            # 应用limit
            if limit and limit > 0:
                memories = all_memories[:limit]
            else:
                memories = all_memories
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "memories": memories,
                "total_count": total_count,
                "returned_count": len(memories)
            }
        except Exception as e:
            log.error(f"获取会话记忆失败: {e}")
            return {
                "success": False,
                "conversation_id": conversation_id,
                "memories": [],
                "total_count": 0,
                "returned_count": 0,
                "error": str(e)
            }
    
    async def get_supported_personalities(self) -> List[Dict[str, Any]]:
        """获取支持的人格列表"""
        try:
            personalities = self.personality_manager.get_all_personalities()
            result = []
            
            for pid, pdata in personalities.items():
                result.append({
                    "id": pid,
                    "name": pdata.get("name", pid),
                    "description": pdata.get("system_prompt", "")[:100] + "...",  # 截取前100字符
                    "allowed_tools": [tool.get("tool_name") for tool in pdata.get("allowed_tools", [])]
                })
            
            return result
        except Exception as e:
            log.error(f"获取人格列表失败: {e}")
            return []
    
    async def get_available_tools(self, personality_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取可用的工具列表"""
        try:
            # 获取所有工具
            all_tools = tool_registry.list_tools()
            
            # 如果指定了人格，过滤工具
            if personality_id:
                personality = self.personality_manager.get_personality(personality_id)
                if personality and personality.get("allowed_tools"):
                    allowed_tool_names = [tool["tool_name"] for tool in personality["allowed_tools"]]
                    # 过滤工具
                    all_tools = {name: tool for name, tool in all_tools.items() if name in allowed_tool_names}
            
            # 转换为列表格式
            result = []
            for name, tool_class in all_tools.items():
                tool_instance = tool_class()
                result.append({
                    "name": tool_instance.name,
                    "description": tool_instance.description,
                    "parameters": tool_instance.parameters
                })
            
            return result
        except Exception as e:
            log.error(f"获取工具列表失败: {e}")
            return []
    
    async def get_allowed_tools_schema(self, personality_id: Optional[str] = None) -> List[Dict]:
        """根据personality获取允许的工具（OpenAI schema格式）
        
        Args:
            personality_id: 人格ID，如果为None则返回所有工具
            
        Returns:
            List[Dict]: OpenAI函数schema格式的工具列表
        """
        try:
            # 获取所有工具的OpenAI函数schema
            all_tools_schema = tool_registry.get_functions_schema()
            
            # 如果没有指定personality，返回所有工具
            if not personality_id:
                log.info(f"未指定personality，返回所有工具，共 {len(all_tools_schema)} 个")
                return all_tools_schema
            
            # 获取personality配置
            personality = self.personality_manager.get_personality(personality_id)
            if not personality or not personality.allowed_tools:
                # 如果personality没有工具限制，返回所有工具
                log.info(f"personality {personality_id} 没有工具限制，返回所有工具，共 {len(all_tools_schema)} 个")
                return all_tools_schema
            
            # 提取允许的工具名称（兼容tool_name和name两种字段）
            allowed_tool_names = []
            for tool in personality.allowed_tools:
                if 'tool_name' in tool:
                    allowed_tool_names.append(tool['tool_name'])
                elif 'name' in tool:
                    allowed_tool_names.append(tool['name'])
            
            if not allowed_tool_names:
                log.warning(f"personality {personality_id} 的allowed_tools格式不正确，使用所有可用工具")
                return all_tools_schema
            
            # 根据allowed_tools过滤工具schema
            filtered_tools = [
                tool for tool in all_tools_schema 
                if tool.get('function', {}).get('name') in allowed_tool_names
            ]
            
            log.info(f"应用personality {personality_id} 的工具限制，允许的工具: {allowed_tool_names}, 过滤后数量: {len(filtered_tools)}/{len(all_tools_schema)}")
            
            return filtered_tools
            
        except Exception as e:
            log.error(f"获取允许的工具schema失败: {e}")
            # 出错时返回空列表，避免暴露所有工具
            return []


# 创建全局聊天引擎实例
chat_engine = ChatEngine()
