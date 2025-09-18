import asyncio
import json  # 添加 json 模块导入
from typing import List, Dict, Any, Optional, AsyncGenerator
import openai
from openai import OpenAI
# 修改导入路径
from config.config import get_config
from config.log_config import get_logger
from core.chat_memory import ChatMemory, get_async_chat_memory
from core.personality_manager import PersonalityManager
from services.tools.manager import ToolManager
import httpx
from services.tools.registry import tool_registry
from services.mcp.manager import mcp_manager
from services.mcp.exceptions import MCPServiceError
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_function_tool_call import Function
from openai.types.chat.chat_completion_message_function_tool_call import ChatCompletionMessageFunctionToolCall
from services.mcp.exceptions import MCPServiceError, MCPServerNotFoundError, MCPToolNotFoundError


logger = get_logger(__name__)
config = get_config()

class ChatEngine:
    def __init__(self):
        # 添加SSL配置和超时设置
        self.client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL,
            # 添加超时设置
            timeout=30.0,
            # 配置HTTP客户端以处理SSL问题
            http_client=httpx.Client(
                follow_redirects=True,
                verify=False,  # 不进行SSL验证
                # 可以尝试禁用HTTP/2，如果问题持续
                http2=False,
                # 增加连接超时
                timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=30.0)
            )
        )
        self.chat_memory = ChatMemory()
        # 初始化异步内存实例，用于异步操作
        self.async_chat_memory = get_async_chat_memory()
        self.personality_manager = PersonalityManager()
        self.tool_manager = ToolManager()
    
    async def generate_response(self, messages: List[Dict[str, str]], conversation_id: str = "default", 
                               personality_id: Optional[str] = None, use_tools: Optional[bool] = None, 
                               stream: Optional[bool] = None) -> Any:
        try:
            # 打印传入的参数值，用于调试
            logger.debug(f"传入参数 - personality_id: {personality_id}, use_tools: {use_tools}, stream: {stream}, type(personality_id): {type(personality_id)}, type(use_tools): {type(use_tools)}, type(stream): {type(stream)}")
            
            # 创建messages的深拷贝，避免修改原始列表
            messages_copy = [msg.copy() for msg in messages]
            
            logger.debug(f"原始消息: {messages_copy}")
            
            # 如果没有指定人格ID，使用默认人格
            if personality_id is None:
                personality_id = config.DEFAULT_PERSONALITY
                logger.info(f"未指定人格ID，使用默认人格: {personality_id}")
            
            # 如果没有指定use_tools，使用默认值
            if use_tools is None:
                use_tools = config.USE_TOOLS_DEFAULT
                logger.info(f"未指定use_tools，使用默认值: {use_tools}")
            
            # 如果没有指定stream，使用默认值
            if stream is None:
                stream = config.STREAM_DEFAULT
                logger.info(f"未指定stream，使用默认值: {stream}")
            
            # 首先从记忆中检索相关内容 - 这里使用同步版本，因为会影响响应生成
            if conversation_id != "default" and messages_copy:
                # 使用messages_copy的最后一条消息作为查询
                relevant_memories = self.chat_memory.get_relevant_memory(conversation_id, messages_copy[-1]["content"])
                if relevant_memories:
                    # 估算token数量并控制在模型限制内
                    memory_text = "\n".join(relevant_memories)
                    memory_section = f"参考记忆：\n{memory_text}"
                    
                    # 估算token数 - 使用简单的估算方法
                    # 假设每个token大约是4个字符
                    estimated_memory_tokens = len(memory_section) // 4
                    estimated_user_tokens = sum(len(msg.get('content', '')) for msg in messages_copy) // 4
                    
                    # 模型最大token限制 - 从配置中获取或使用默认值
                    max_tokens = getattr(config, 'OPENAI_MAX_TOKENS', 8192)
                    
                    # 预留部分空间给系统提示和模型输出
                    safety_margin = 0.8  # 使用80%的空间
                    
                    # 如果添加记忆不会导致超出限制，则添加记忆
                    if estimated_memory_tokens + estimated_user_tokens < max_tokens * safety_margin:
                        # 将记忆添加到消息列表开头
                        messages_copy = [{"role": "system", "content": memory_section}] + messages_copy
                        logger.debug(f"添加了记忆到系统提示，估算token数: {estimated_memory_tokens}")
                    else:
                        # 如果记忆太多，选择不添加
                        logger.warning(f"避免超出模型token限制，不添加记忆到系统提示。\n估算记忆token: {estimated_memory_tokens}, 用户消息token: {estimated_user_tokens}, 限制: {max_tokens * safety_margin}")
            
            # 初始化allowed_tool_names为None
            allowed_tool_names = None
            
            # 应用人格 - 修复参数顺序
            if personality_id:
                try:
                    messages_copy = self.personality_manager.apply_personality(messages_copy, personality_id)
                    logger.debug(f"应用人格后消息: {messages_copy}")
                    
                    # 获取人格的allowed_tools信息，用于工具过滤
                    personality = self.personality_manager.get_personality(personality_id)
                    if personality and personality.allowed_tools:
                        allowed_tool_names = [tool["tool_name"] for tool in personality.allowed_tools]
                except Exception as e:
                    logger.warning(f"应用人格时出错，忽略人格设置: {e}")
            
            # 构建请求参数
            request_params = {
                "model": config.OPENAI_MODEL,
                "messages": messages_copy,
                "temperature": float(config.OPENAI_TEMPERATURE)  # 转换为浮点数
            }
            
            # 如果启用了工具，添加工具schema到请求参数
            if use_tools:
                # 获取所有注册的工具schema
                all_tools_schema = tool_registry.get_functions_schema()
                logger.debug(f"原始工具数量: {len(all_tools_schema)}")
                logger.debug(f"允许的工具名称: {allowed_tool_names}")
                
                # 如果有allowed_tools配置，则进行过滤
                if allowed_tool_names:
                    # 只保留allowed_tools中列出的工具
                    tools_schema = []
                    for tool in all_tools_schema:
                        tool_name = tool.get("function", {}).get("name")
                        if tool_name in allowed_tool_names:
                            tools_schema.append(tool)
                    logger.info(f"已根据人格配置过滤工具，剩余工具数量: {len(tools_schema)}")
                else:
                    # 如果没有allowed_tools配置，则使用所有工具
                    tools_schema = all_tools_schema
                    logger.info(f"未设置人格工具过滤，使用所有工具，工具数量: {len(tools_schema)}")
                if tools_schema:
                    request_params["tools"] = tools_schema
                    
                    # 对于时间相关问题，强制使用工具
                    last_message = messages_copy[-1]["content"].lower() if messages_copy else ""
                    if any(keyword in last_message for keyword in ["几点", "时间", "现在", "几点钟", "时刻"]):
                        # 只有当gettime工具在allowed_tools中时才强制使用
                        if not allowed_tool_names or "gettime" in allowed_tool_names:
                            request_params["tool_choice"] = {"type": "function", "function": {"name": "gettime"}}
                            logger.info("检测到时间相关问题，强制使用gettime工具")
                        else:
                            logger.info("检测到时间相关问题，但gettime工具不在允许使用的工具列表中")
                else:
                    logger.warning("未找到允许使用的工具，无法添加工具schema到请求参数")
            else:
                logger.debug("工具调用已禁用")
            
            logger.debug(f"最终请求参数: {request_params}")

            if stream:
                # 直接返回异步生成器方法调用
                return self._generate_streaming_response(request_params, conversation_id, messages)
            else:
                return await self._generate_non_streaming_response(request_params, conversation_id, messages)
        except Exception as e:
            logger.error(f"Error in generate_response: {e}")
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
        original_messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        try:
            # 调用OpenAI API
            response = self.client.chat.completions.create(**request_params)
            logger.debug(f"OpenAI API响应: {response}")
            
            # 增加响应格式验证
            if not hasattr(response, 'choices') or not response.choices:
                logger.error(f"Invalid API response format: {dir(response)}")
                return {"role": "assistant", "content": "获取AI响应时发生格式错误，请检查API配置。"}
            
            # 处理响应
            if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                # 处理工具调用
                return await self._handle_tool_calls(
                    response.choices[0].message.tool_calls,
                    conversation_id,
                    original_messages
                )
            else:
                # 确保content存在
                if not hasattr(response.choices[0].message, 'content') or response.choices[0].message.content is None:
                    logger.error(f"Response missing content: {response}")
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
            logger.error(f"JSON解析错误: {e}. 请检查API端点是否正确且返回有效JSON格式。")
            return {"role": "assistant", "content": "API返回内容格式错误，请确认API端点配置正确。"}
        except Exception as e:
            logger.error(f"生成响应时出错: {e}")
            # 尝试获取更详细的错误信息
            detailed_error = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                detailed_error += f"\n响应内容: {e.response.text[:200]}..."
            return {"role": "assistant", "content": f"抱歉，我现在无法为您提供帮助。错误信息: {detailed_error}"}
    
    async def _generate_streaming_response(
        self,
        request_params: Dict[str, Any],
        conversation_id: str,
        original_messages: List[Dict[str, str]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            request_params["stream"] = True
            response = self.client.chat.completions.create(**request_params)
            
            # 用于检测是否有工具调用
            tool_calls = None
            full_content = ""
            
            # 流式处理响应
            async for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
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
                    
                    # 处理普通内容
                    elif choice.delta.content is not None:
                        content = choice.delta.content
                        full_content += content
                        yield {
                            "role": "assistant",
                            "content": content,
                            "finish_reason": None,
                            "stream": True
                        }
            
            # 检查是否有工具调用需要处理
            if tool_calls:
                # 转换工具调用格式为OpenAI标准格式
                  
                formatted_tool_calls = []
                for tool_call in tool_calls:
                    # 使用正确的Function类
                    function = Function(
                        name=tool_call["function"]["name"],
                        arguments=tool_call["function"]["arguments"]
                    )
                    
                    # 由于ChatCompletionMessageToolCall是一个类型别名，我们需要直接创建正确的对象
                    # 这里我们创建ChatCompletionMessageFunctionToolCall类型的对象   
                                       
                    formatted_tool_call = ChatCompletionMessageFunctionToolCall(
                        id=tool_call["id"],
                        type="function",
                        function=function
                    )
                    formatted_tool_calls.append(formatted_tool_call)
                
                # 处理工具调用并获取结果
                tool_response = await self._handle_tool_calls(
                    formatted_tool_calls,
                    conversation_id,
                    original_messages
                )
                
                # 由于_tool_calls返回的是非流式响应，我们需要模拟流式输出
                if tool_response and "content" in tool_response:
                    # 这里可以根据需要将内容分块输出
                    yield {
                        "role": "assistant",
                        "content": tool_response["content"],
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
            
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
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
        original_messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        # 准备工具调用列表
        calls_to_execute = []
        for tool_call in tool_calls:
            calls_to_execute.append({
                "name": tool_call.function.name,
                "parameters": json.loads(tool_call.function.arguments)
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
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_call.function.name,
                "content": content
            })
        
        # 将工具调用结果添加到消息历史中，再次调用模型
        new_messages = original_messages.copy()
        new_messages.append({"role": "assistant", "tool_calls": tool_calls})
        new_messages.extend(tool_response_messages)
        
        # 重新生成响应
        return await self.generate_response(new_messages, conversation_id, use_tools=False)
    
    async def call_mcp_service(self, tool_name: str = None, params: dict = None, 
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
            
            logger.info(f"Calling MCP service: {tool_name}, params: {params}, server: {mcp_server or 'auto'}")
            
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
            logger.error(f"MCP server error: {str(e)}")
            return {"success": False, "error": f"MCP服务器错误: {str(e)}"}
        except MCPToolNotFoundError as e:
            logger.error(f"MCP tool error: {str(e)}")
            return {"success": False, "error": f"MCP工具错误: {str(e)}"}
        except MCPServiceError as e:
            logger.error(f"MCP service error: {str(e)}")
            return {"success": False, "error": f"MCP服务调用失败: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error when calling MCP service: {str(e)}")
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
            logger.debug(f"Successfully retrieved {len(memories)} memories for conversation {conversation_id}")
            return memories
        except Exception as e:
            logger.error(f"Failed to get conversation memory: {e}")
            return []

    # 获取会话记忆 - 异步版本
    async def aget_conversation_memory(self, conversation_id: str) -> list:
        """获取会话记忆（异步版本）"""
        try:
            # 直接调用异步记忆实例的方法
            return await self.async_chat_memory.get_all_memory(conversation_id)
        except Exception as e:
            logger.error(f"异步获取会话记忆时出错: {e}")
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
                logger.warning(f"未知的MEMORY_SAVE_MODE配置值: {config.MEMORY_SAVE_MODE}，默认保存所有消息")
            
            if messages_to_save:
                logger.debug(f"使用原生异步API保存消息到记忆: 模式={config.MEMORY_SAVE_MODE}, 消息数量={len(messages_to_save)}, conversation_id={conversation_id}")
                
                # 记录将要保存的消息内容（为了避免日志过大，可以只记录第一条和最后一条）
                if len(messages_to_save) > 0:
                    logger.debug(f"第一条消息内容预览: {messages_to_save[0].get('content', '')[:100]}...")
                    if len(messages_to_save) > 1:
                        logger.debug(f"最后一条消息内容预览: {messages_to_save[-1].get('content', '')[:100]}...")
                
                # 批量保存消息
                await self.async_chat_memory.add_messages_batch(conversation_id, messages_to_save)
                logger.debug("使用原生异步API保存消息到记忆完成")
            else:
                logger.debug(f"根据配置 MEMORY_SAVE_MODE={config.MEMORY_SAVE_MODE}，没有消息需要保存到记忆")
        except Exception as e:
            logger.error(f"使用原生异步API保存消息到记忆失败: {e}", exc_info=True)

    # 保留原有的_save_message_to_memory_async方法以保持向后兼容
    async def _save_message_to_memory_async(self, conversation_id: str, message: dict):
        """异步保存消息到记忆，不阻塞主线程 - 为保持向后兼容性保留"""
        try:
            # 直接调用新的异步方法
            await self._async_save_message_to_memory(conversation_id, [message])
        except Exception as e:
            logger.error(f"异步保存消息到记忆失败: {e}")


# 创建全局聊天引擎实例
chat_engine = ChatEngine()
