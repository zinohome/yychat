import asyncio
import json  # 添加 json 模块导入
from typing import List, Dict, Any, Optional, AsyncGenerator
import openai
from openai import OpenAI
# 修改导入路径
from config.config import get_config
from config.log_config import get_logger
from core.chat_memory import ChatMemory
from core.personality_manager import PersonalityManager
from services.tools.manager import ToolManager
from services.mcp.client import mcp_client, MCPRequest
import httpx
from services.tools.registry import tool_registry
from services.mcp.manager import mcp_manager
from services.mcp.exceptions import MCPServiceError

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
                #http2=True,   # 启用HTTP/2支持
                # 可以尝试禁用HTTP/2，如果问题持续
                http2=False,
                # 增加连接超时
                timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=30.0)
            )
        )
        self.chat_memory = ChatMemory()
        self.personality_manager = PersonalityManager()
        self.tool_manager = ToolManager()
    
    async def generate_response(self, messages: List[Dict[str, str]], conversation_id: str = "default", 
                               personality_id: Optional[str] = None, use_tools: bool = True, 
                               stream: bool = False) -> Any:
        try:
            # 创建messages的深拷贝，避免修改原始列表
            messages_copy = [msg.copy() for msg in messages]
            
            logger.debug(f"原始消息: {messages_copy}")
            
            # 首先从记忆中检索相关内容
            if conversation_id != "default":
                # 使用messages_copy的最后一条消息作为查询
                if messages_copy:
                    relevant_memories = self.chat_memory.get_relevant_memory(conversation_id, messages_copy[-1]["content"])
                    if relevant_memories:
                        # 将列表转换为字符串格式
                        memories_str = "\n".join(relevant_memories)
                        # 避免修改原始messages列表
                        messages_copy = [{"role": "system", "content": f"参考记忆：\n{memories_str}"}] + messages_copy
            
            # 应用人格 - 修复参数顺序
            if personality_id:
                try:
                    messages_copy = self.personality_manager.apply_personality(messages_copy, personality_id)
                    logger.debug(f"应用人格后消息: {messages_copy}")
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
                tools_schema = tool_registry.get_functions_schema()
                if tools_schema:
                    request_params["tools"] = tools_schema
                    logger.info(f"已添加工具schema到请求参数，工具数量: {len(tools_schema)}")
                    logger.debug(f"工具schema: {tools_schema}")
                    
                    # 对于时间相关问题，强制使用工具
                    last_message = messages_copy[-1]["content"].lower() if messages_copy else ""
                    if any(keyword in last_message for keyword in ["几点", "时间", "现在", "几点钟", "时刻"]):
                        request_params["tool_choice"] = {"type": "function", "function": {"name": "gettime"}}
                        logger.info("检测到时间相关问题，强制使用gettime工具")
                else:
                    logger.warning("未找到注册的工具，无法添加工具schema到请求参数")
            else:
                logger.debug("工具调用已禁用")
            
            logger.debug(f"最终请求参数: {request_params}")
            
            # 根据是否使用工具来决定调用哪个生成方法
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
                
                # 保存到记忆
                if conversation_id:
                    self.chat_memory.add_message(conversation_id, {"role": "assistant", "content": content})
                    self.chat_memory.add_message(conversation_id, original_messages[-1])
                
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
            
            full_content = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    yield {
                        "role": "assistant",
                        "content": content,
                        "finish_reason": None,
                        "stream": True
                    }
            
            # 保存到记忆
            if conversation_id and full_content:
                self.chat_memory.add_message(conversation_id, {"role": "assistant", "content": full_content})
                self.chat_memory.add_message(conversation_id, original_messages[-1])
            
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
    
    async def call_mcp_service(self, service_name: str, method_name: str, params: dict):
        """调用MCP服务"""
        try:
            # 构建工具名称和参数
            tool_name = f"{service_name}__{method_name}"
            logger.info(f"Calling MCP service: {tool_name}, params: {params}")
            
            # 使用MCP管理器调用服务
            result = mcp_manager.call_tool(tool_name, params)
            
            # 处理结果
            if result and len(result) > 0:
                return result[0].get('text') or str(result)
            return str(result)
        except MCPServiceError as e:
            logger.error(f"MCP service error: {str(e)}")
            return f"MCP服务调用失败: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error when calling MCP service: {str(e)}")
            return f"调用MCP服务时发生未知错误: {str(e)}"

    # 清除会话记忆
    def clear_conversation_memory(self, conversation_id: str):
        self.chat_memory.delete_memory(conversation_id)
    
    # 获取会话记忆
    def get_conversation_memory(self, conversation_id: str) -> list:
        return self.chat_memory.get_all_memory(conversation_id)

# 创建全局聊天引擎实例
chat_engine = ChatEngine()