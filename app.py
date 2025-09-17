import json
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from typing import List, Dict, Any, Optional, Union
import uvicorn
# 修改导入路径
from config.config import get_config
from config.log_config import get_logger
from core.chat_engine import chat_engine
from core.personality_manager import PersonalityManager
from services.tools.registry import tool_registry
# 添加工具自动发现导入
from services.tools.discovery import ToolDiscoverer
from services.mcp.discovery import discover_and_register_mcp_tools
# 添加mcp_manager导入用于列出MCP工具
from services.mcp.manager import mcp_manager
# 添加ToolManager导入用于工具调用
from services.tools.manager import ToolManager

# 导入Pydantic模型
from schemas.api_schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatCompletionResponseUsage,
    ToolCallRequest,
    MCPServiceCallRequest
)


logger = get_logger(__name__)
config = get_config()

# 创建FastAPI应用
app = FastAPI(
    title="OpenAI兼容聊天机器人API",
    description="使用Mem0和ChromaDB进行记忆管理的聊天机器人API",
    version="1.0.0"
)

# 初始化人格管理器
personality_manager = PersonalityManager()
# 初始化工具管理器
tool_manager = ToolManager()


# 在应用初始化时自动注册所有工具
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的初始化操作"""
    # 自动发现并注册所有工具
    registered_count = ToolDiscoverer.register_discovered_tools()
    logger.info(f"自动注册了 {registered_count} 个工具")
    
    # 初始化并注册MCP工具
    try:
        discover_and_register_mcp_tools()
    except Exception as e:
        logger.error(f"Failed to initialize MCP tools: {str(e)}")

# 自定义异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"API Error: {exc}", exc_info=True)
    return {
        "error": {
            "message": "处理您的请求时发生错误",
            "type": "server_error",
            "param": None,
            "code": "internal_error"
        }
    }

# 聊天完成API
@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    try:
        # 验证conversation_id，如果没有则使用user作为会话标识
        conversation_id = request.conversation_id or request.user
        
        # 记录请求日志
        logger.info(f"Chat completion request: model={request.model}, conversation_id={conversation_id}")
        
        if request.stream:
            # 流式响应处理
            async def stream_generator():
                try:
                    # 确保正确调用chat_engine.generate_response并等待协程解析
                    generator = await chat_engine.generate_response(
                        request.messages,
                        conversation_id,
                        request.personality_id,
                        request.use_tools,
                        stream=True
                    )
                    # 异步迭代生成器
                    async for chunk in generator:
                        if chunk.get("stream", False):
                            # 构建SSE格式的响应
                            response_data = {
                                "id": f"chatcmpl-{conversation_id}",
                                "object": "chat.completion.chunk",
                                "created": int(asyncio.get_event_loop().time()),
                                "model": request.model,
                                "choices": [{"index": 0, "delta": {"content": chunk["content"]}, "finish_reason": chunk["finish_reason"]}]
                            }
                            yield f"data: {json.dumps(response_data)}\n\n"
                              
                            # 如果是结束标志，退出循环
                            if chunk["finish_reason"] is not None:
                                break
                except Exception as e:
                    logger.error(f"Error in stream generator: {e}")
                    # 发送错误消息
                    error_data = {
                        "id": f"chatcmpl-{conversation_id}",
                        "object": "chat.completion.chunk",
                        "created": int(asyncio.get_event_loop().time()),
                        "model": request.model,
                        "choices": [{"index": 0, "delta": {"content": f"发生错误: {str(e)}"}, "finish_reason": "error"}]
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    # 确保发送DONE标记
                    yield 'data: [DONE]\n\n'
            
            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        else:
            # 非流式响应处理
            response = await chat_engine.generate_response(
                request.messages,
                conversation_id,
                request.personality_id,
                request.use_tools
            )
            
            # 构建响应
            result = ChatCompletionResponse(
                id=f"chatcmpl-{conversation_id}",
                object="chat.completion",
                created=int(asyncio.get_event_loop().time()),
                model=response.get("model", request.model),
                choices=[ChatCompletionResponseChoice(
                    index=0,
                    message=response,
                    finish_reason="stop"
                )]
            )
            
            # 添加usage信息
            if "usage" in response:
                result.usage = ChatCompletionResponseUsage(**response["usage"])
            
            return result
            
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail={"error": {"message": str(e), "type": "validation_error"}})
    except Exception as e:
        logger.error(f"Chat completion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})

# 模型列表API
@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": config.OPENAI_MODEL,
                "object": "model",
                "created": int(asyncio.get_event_loop().time()),
                "owned_by": "openai"
            }
        ]
    }

# 获取模型详情API
@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    if model_id != config.OPENAI_MODEL:
        raise HTTPException(status_code=404, detail={"error": {"message": "Model not found", "type": "invalid_request_error"}})
    
    return {
        "id": model_id,
        "object": "model",
        "created": int(asyncio.get_event_loop().time()),
        "owned_by": "openai"
    }

# 人格管理API
@app.get("/v1/personalities")
async def list_personalities():
    return {
        "object": "list",
        "data": personality_manager.list_personalities()
    }

# 清除会话记忆API
@app.delete("/v1/conversations/{conversation_id}/memory", tags=["Services"])
async def clear_conversation_memory(conversation_id: str):
    chat_engine.clear_conversation_memory(conversation_id)
    return {
        "success": True,
        "message": f"Memory for conversation {conversation_id} cleared"
    }

# 获取会话记忆API
@app.get("/v1/conversations/{conversation_id}/memory", tags=["Services"])
async def get_conversation_memory(conversation_id: str):
    memories = chat_engine.get_conversation_memory(conversation_id)
    return {
        "object": "list",
        "data": memories,
        "total": len(memories)
    }

# MCP服务调用API
@app.post("/v1/mcp/call", tags=["Services"])
async def call_mcp_service(request: MCPServiceCallRequest):
    try:
        # 提取参数，增加对mcp_server的支持
        tool_name = request.tool_name
        mcp_server = request.mcp_server  # 可选，指定MCP服务器
        params = request.params
        
        # 向后兼容：如果没有提供tool_name但提供了service_name和method_name，则构建tool_name
        if not tool_name:
            service_name = request.service_name
            method_name = request.method_name
            
            if not service_name or not method_name:
                raise HTTPException(status_code=400, detail={"error": {"message": "Missing tool_name or both service_name and method_name", "type": "validation_error"}})
        
        # 调用MCP服务，传递所有必要参数
        result = await chat_engine.call_mcp_service(
            tool_name=tool_name,
            params=params,
            service_name=request.service_name,
            method_name=request.method_name,
            mcp_server=mcp_server
        )
        
        # 检查result是否为字典且包含success字段
        if not isinstance(result, dict) or "success" not in result:
            raise HTTPException(status_code=500, detail={"error": {"message": "Invalid MCP service response format", "type": "mcp_service_error"}})
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail={"error": {"message": result.get("error", "Unknown MCP service error"), "type": "mcp_service_error"}})
        
        return result
        
    except HTTPException:
        # 重新抛出HTTP异常，避免重复记录日志
        raise
    except Exception as e:
        logger.error(f"MCP service call error: {e}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})
        
# 根路径API
@app.get("/")
async def root():
    return {
        "message": "Welcome to the OpenAI compatible Chat API",
        "version": "1.0.0",
        "api_endpoints": ["/v1/chat/completions", "/v1/models", "/v1/personalities"]
    }

# 列出所有工具
@app.get("/v1/tools", tags=["Services"])
async def list_available_tools():
    """列出所有已注册的非MCP工具"""
    try:
        # 获取所有工具
        all_tools = tool_registry.list_tools()
        
        # 获取所有MCP工具名称
        mcp_tools = mcp_manager.list_tools()
        mcp_tool_names = {tool["name"] for tool in mcp_tools}
        
        # 过滤掉MCP工具，只保留非MCP工具
        non_mcp_tools = {name: tool for name, tool in all_tools.items() if name not in mcp_tool_names}
        
        return {
            "tools": [{
                "name": tool.name,
                "description": tool.description
            } for tool in non_mcp_tools.values()]
        }
    except Exception as e:
        logger.error(f"Failed to list tools: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})

# 列出所有MCP工具
@app.get("/v1/mcp/tools", tags=["Services"])
async def list_available_mcp_tools():
    """列出所有已注册的MCP工具"""
    try:
        # 使用mcp_manager获取MCP工具列表
        mcp_tools = mcp_manager.list_tools()
        
        # 格式化返回结果，保持与现有工具API一致的格式
        return {
            "tools": [{k: v for k, v in tool.items() if k in ["name", "description"]} for tool in mcp_tools]
        }
    except Exception as e:
        logger.error(f"Failed to list MCP tools: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "mcp_service_error"}})

# 工具调用API - 用于调用非MCP工具
@app.post("/v1/tools/call", tags=["Services"])
async def call_tool(request: ToolCallRequest):
    """调用指定的非MCP工具"""
    try:
        # 提取参数
        tool_name = request.tool_name
        params = request.params
        
        if not tool_name:
            raise HTTPException(status_code=400, detail={"error": {"message": "Missing tool_name", "type": "validation_error"}})
        
        # 调用工具
        logger.info(f"Calling tool: {tool_name} with params: {params}")
        result = await tool_manager.execute_tool(tool_name, params)
        
        # 格式化返回结果
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Tool call error: {e}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})

# 启动服务器
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=True
    )
