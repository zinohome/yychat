#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenMemory 适配器模块

这个模块是对 mem0 的自定义扩展，主要使用我们自己实现的 OpenMemoryClient
来与本地部署的 Mem0 服务器进行交互，同时保持与原始 mem0 接口的兼容性。
"""

from typing import List, Optional, Union

import httpx

from mem0 import Memory, MemoryClient
from mem0.configs.prompts import MEMORY_ANSWER_PROMPT

from .open_mem0_client import OpenMemoryClient, AsyncOpenMemoryClient


class Mem0:
    """OpenMemory 客户端主类，继承并扩展了原始 mem0.Mem0 的功能"""
    
    def __init__(
        self,
        config: Optional[dict] = None,
        api_key: Optional[str] = None,
        host: Optional[str] = None,
        org_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        """初始化 OpenMemory 客户端
        
        Args:
            config: 配置字典，用于本地 Memory 实例
            api_key: Mem0 API 密钥
            host: Mem0 服务器地址
            org_id: 组织 ID
            project_id: 项目 ID
        """
        if api_key:
            # 使用我们自定义的 OpenMemoryClient 连接到远程服务器
            self.mem0_client = OpenMemoryClient(
                api_key=api_key,
                host=host,
                org_id=org_id,
                project_id=project_id
            )
        else:
            # 如果没有提供 API 密钥，则使用本地 Memory 实例
            self.mem0_client = Memory.from_config(config) if config else Memory()

        # 初始化聊天接口
        self.chat = Chat(self.mem0_client)


class Chat:
    """聊天接口封装"""
    
    def __init__(self, mem0_client):
        self.completions = Completions(mem0_client)


class Completions:
    """补全接口封装"""
    
    def __init__(self, mem0_client):
        self.mem0_client = mem0_client

    def create(
        self,
        model: str,
        messages: List = [],
        # Mem0 arguments
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        filters: Optional[dict] = None,
        limit: Optional[int] = 10,
        # LLM arguments
        timeout: Optional[Union[float, str, httpx.Timeout]] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stream: Optional[bool] = None,
        stream_options: Optional[dict] = None,
        stop=None,
        max_tokens: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[dict] = None,
        user: Optional[str] = None,
        # openai v1.0+ new params
        response_format: Optional[dict] = None,
        seed: Optional[int] = None,
        tools: Optional[List] = None,
        tool_choice: Optional[Union[str, dict]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        parallel_tool_calls: Optional[bool] = None,
        deployment_id=None,
        extra_headers: Optional[dict] = None,
        # soon to be deprecated params by OpenAI
        functions: Optional[List] = None,
        function_call: Optional[str] = None,
        # set api_base, api_version, api_key
        base_url: Optional[str] = None,
        api_version: Optional[str] = None,
        api_key: Optional[str] = None,
        model_list: Optional[list] = None,  # pass in a list of api_base,keys, etc.
    ):
        """创建聊天补全请求
        
        这是对原始 mem0 接口的扩展，确保能够正确处理本地部署的 OpenAI 和 Mem0 服务。
        """
        if not any([user_id, agent_id, run_id]):
            raise ValueError("One of user_id, agent_id, run_id must be provided")

        try:
            import litellm
            if not litellm.supports_function_calling(model):
                raise ValueError(
                    f"Model '{model}' does not support function calling. Please use a model that supports function calling."
                )
        except ImportError:
            # 如果没有安装 litellm，我们假设模型支持函数调用
            pass

        prepared_messages = self._prepare_messages(messages)
        if prepared_messages[-1]["role"] == "user":
            # 异步添加到记忆
            self._async_add_to_memory(messages, user_id, agent_id, run_id, metadata, filters)
            # 获取相关记忆
            relevant_memories = self._fetch_relevant_memories(messages, user_id, agent_id, run_id, filters, limit)
            # 格式化查询内容，添加相关记忆
            prepared_messages[-1]["content"] = self._format_query_with_memories(messages, relevant_memories)

        # 使用 litellm 发送请求
        try:
            import litellm
            response = litellm.completion(
                model=model,
                messages=prepared_messages,
                temperature=temperature,
                top_p=top_p,
                n=n,
                timeout=timeout,
                stream=stream,
                stream_options=stream_options,
                stop=stop,
                max_tokens=max_tokens,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty,
                logit_bias=logit_bias,
                user=user,
                response_format=response_format,
                seed=seed,
                tools=tools,
                tool_choice=tool_choice,
                logprobs=logprobs,
                top_logprobs=top_logprobs,
                parallel_tool_calls=parallel_tool_calls,
                deployment_id=deployment_id,
                extra_headers=extra_headers,
                functions=functions,
                function_call=function_call,
                base_url=base_url,
                api_version=api_version,
                api_key=api_key,
                model_list=model_list,
            )
            return response
        except ImportError:
            # 如果没有安装 litellm，抛出更友好的错误信息
            raise ImportError("litellm is required for this functionality. Please install it using 'pip install litellm'.")

    def _prepare_messages(self, messages: List[dict]) -> List[dict]:
        """准备消息列表，确保包含系统提示词"""
        if not messages or messages[0]["role"] != "system":
            return [{"role": "system", "content": MEMORY_ANSWER_PROMPT}] + messages
        return messages

    def _async_add_to_memory(self, messages, user_id, agent_id, run_id, metadata, filters):
        """异步添加消息到记忆"""
        import threading
        
        def add_task():
            try:
                self.mem0_client.add(
                    messages=messages,
                    user_id=user_id,
                    agent_id=agent_id,
                    run_id=run_id,
                    metadata=metadata,
                    filters=filters,
                )
            except Exception as e:
                # 添加记忆失败不应影响主流程
                import logging
                logging.error(f"Failed to add to memory: {str(e)}")

        # 创建并启动异步线程
        threading.Thread(target=add_task, daemon=True).start()

    def _fetch_relevant_memories(self, messages, user_id, agent_id, run_id, filters, limit):
        """获取与当前对话相关的记忆"""
        # 只传递最近的 6 条消息到搜索 API，以防止查询过长
        message_input = [f"{message['role']}: {message['content']}" for message in messages][-6:]
        # 调用自定义的 OpenMemoryClient 进行搜索
        return self.mem0_client.search(
            query="\n".join(message_input),
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            filters=filters,
            limit=limit,
        )

    def _format_query_with_memories(self, messages, relevant_memories):
        """将查询内容与相关记忆格式化"""
        # 处理不同类型的客户端返回的记忆格式
        entities = []
        if isinstance(self.mem0_client, Memory):
            # 本地 Memory 实例的格式
            memories_text = "\n".join(memory["memory"] for memory in relevant_memories["results"])
            if relevant_memories.get("relations"):
                entities = [entity for entity in relevant_memories["relations"]]
        elif isinstance(self.mem0_client, (MemoryClient, OpenMemoryClient)):
            # 远程客户端的格式
            # 根据 OpenMemoryClient 的实现，这里可能需要调整
            if isinstance(relevant_memories, list):
                # 对于返回列表的情况
                memories_text = "\n".join(memory["memory"] for memory in relevant_memories) if relevant_memories else ""
            elif isinstance(relevant_memories, dict) and "results" in relevant_memories:
                # 对于返回字典包含 results 的情况
                memories_text = "\n".join(memory["memory"] for memory in relevant_memories["results"])
            else:
                memories_text = str(relevant_memories)
        else:
            # 默认处理
            memories_text = str(relevant_memories)
        
        return f"- Relevant Memories/Facts: {memories_text}\n\n- Entities: {entities}\n\n- User Question: {messages[-1]['content']}"


# 提供与原始 mem0 包相同的接口，方便替换使用
export = [Mem0, OpenMemoryClient, AsyncOpenMemoryClient]