import time
from typing import List, Dict, Any, Optional, AsyncGenerator
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
            def chat(self):
                class MockChat:
                    def completions(self):
                        class MockCompletions:
                            def create(self, **kwargs):
                                # 直接调用OpenAI API作为降级方案
                                client = OpenAI(
                                    api_key=config.OPENAI_API_KEY,
                                    base_url=config.OPENAI_BASE_URL
                                )
                                return client.chat.completions.create(**kwargs)
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
    
    async def generate_response(self, messages: List[Dict[str, str]], conversation_id: str = "default",
                               personality_id: Optional[str] = None, use_tools: Optional[bool] = None,
                               stream: Optional[bool] = None) -> Any:
        """
        生成聊天响应，支持personality、conversation_id、use_tools、stream等参数
        与app.py中的create_chat_completion API完全兼容
        """
        start_time = time.time()
        try:
            # 使用默认值
            if use_tools is None:
                use_tools = self.config.USE_TOOLS_DEFAULT
            if stream is None:
                stream = self.config.STREAM_DEFAULT
            
            # 创建消息副本，避免修改原始消息
            messages_copy = messages.copy()
            
            # 应用人格
            allowed_tool_names = None
            if personality_id:
                messages_copy = self.personality_manager.apply_personality(messages_copy, personality_id)
                log.debug(f"Applied personality: {personality_id}")
                
                # 获取人格的allowed_tools信息，用于工具过滤
                try:
                    personality = self.personality_manager.get_personality(personality_id)
                    if personality and personality.allowed_tools:
                        allowed_tool_names = [tool["tool_name"] for tool in personality.allowed_tools]
                        log.debug(f"Allowed tools for personality {personality_id}: {allowed_tool_names}")
                except Exception as e:
                    log.warning(f"获取人格工具配置时出错: {e}")
            
            # 准备调用参数
            call_params = {
                "messages": messages_copy,
                "model": self.config.OPENAI_MODEL,
                "user_id": conversation_id,
                "stream": stream,
                "temperature": float(self.config.OPENAI_TEMPERATURE),
                "limit": self.config.MEMORY_RETRIEVAL_LIMIT
            }
            
            # 添加工具相关配置
            if use_tools:
                # 使用tool_registry获取工具的函数调用模式
                from services.tools.registry import tool_registry
                all_tools_schema = tool_registry.get_functions_schema()
                log.debug(f"原始工具数量: {len(all_tools_schema)}")
                log.debug(f"允许的工具名称: {allowed_tool_names}")
                
                # 根据allowed_tool_names过滤工具
                if allowed_tool_names:
                    # 只保留allowed_tools中列出的工具
                    tools = []
                    for tool in all_tools_schema:
                        tool_name = tool.get("function", {}).get("name")
                        if tool_name in allowed_tool_names:
                            tools.append(tool)
                    log.info(f"已根据人格配置过滤工具，剩余工具数量: {len(tools)}")
                else:
                    # 如果没有allowed_tools配置，则使用所有工具
                    tools = all_tools_schema
                    log.info(f"未设置人格工具过滤，使用所有工具，工具数量: {len(tools)}")
                
                if tools:
                    call_params["tools"] = tools
                    call_params["tool_choice"] = "auto"
                    
                    # 对于时间相关问题，强制使用工具
                    last_message = messages_copy[-1]["content"].lower() if messages_copy else ""
                    if any(keyword in last_message for keyword in ["几点", "时间", "现在", "几点钟", "时刻"]):
                        # 只有当gettime工具在allowed_tools中时才强制使用
                        if not allowed_tool_names or "gettime" in allowed_tool_names:
                            call_params["tool_choice"] = {"type": "function", "function": {"name": "gettime"}}
                            log.info("检测到时间相关问题，强制使用gettime工具")
                        else:
                            log.info("检测到时间相关问题，但gettime工具不在允许使用的工具列表中")
                    
                    log.debug(f"Added {len(tools)} tools to the request")
            
            # 获取客户端
            client = self.get_client(conversation_id)
            
            # 调用Mem0客户端生成响应
            response = client.chat.completions.create(**call_params)
            
            if stream:
                # 处理流式响应
                return self._handle_streaming_response(response, conversation_id)
            else:
                # 处理非流式响应
                result = await self._handle_non_streaming_response(response, messages, conversation_id)
                # 确保返回的是字典而不是异步生成器
                if hasattr(result, '__aiter__'):
                    # 如果是异步生成器，获取第一个结果
                    async for chunk in result:
                        return chunk
                return result
                
        except Exception as e:
            log.error(f"使用Mem0代理生成响应失败: {e}")
            # 降级到直接调用OpenAI API
            return await self._fallback_to_openai(messages, conversation_id, personality_id, use_tools, stream)
        finally:
            log.debug(f"Mem0代理响应生成耗时: {time.time() - start_time:.3f}秒")
            
    async def _handle_streaming_response(self, response, conversation_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """处理流式响应"""
        try:
            # 从流式响应中提取内容
            async for chunk in response:
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta') and hasattr(choice.delta, 'content') and choice.delta.content is not None:
                        yield {
                            "stream": True,
                            "content": choice.delta.content,
                            "finish_reason": choice.finish_reason
                        }
                    elif choice.finish_reason is not None:
                        yield {
                            "stream": True,
                            "content": "",
                            "finish_reason": choice.finish_reason
                        }
        except Exception as e:
            log.error(f"处理流式响应时出错: {e}")
            yield {
                "stream": True,
                "content": f"发生错误: {str(e)}",
                "finish_reason": "error"
            }
    
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
                # 处理流式响应
                return self._handle_streaming_response(response, conversation_id)
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
                asyncio.create_task(self.async_chat_memory.save_message(
                    conversation_id=conversation_id,
                    role="user",
                    content=user_message.get("content", "")
                ))
                
                asyncio.create_task(self.async_chat_memory.save_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response.get("content", "")
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
            
    async def call_mcp_service(self, tool_name: str, params: Dict[str, Any], 
                             service_name: Optional[str] = None, method_name: Optional[str] = None, 
                             mcp_server: Optional[str] = None) -> Dict[str, Any]:
        """调用MCP服务"""
        try:
            # 使用mcp_manager调用MCP服务
            # 注意：mcp_manager实际上是同步的call_tool方法，不是异步的call_service
            result = mcp_manager.call_tool(
                tool_name=tool_name,
                arguments=params,
                mcp_server=mcp_server
            )
            return result
        except Exception as e:
            log.error(f"MCP service call failed: {e}")
            return {"success": False, "error": str(e)}

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