import json
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from typing import List, Dict, Any, Optional, Union
import uvicorn
import os
# 修改导入路径
from config.config import get_config
from utils.log import log
from core.chat_memory import get_async_chat_memory
from utils.performance import get_performance_monitor, performance_monitor
from core.personality_manager import PersonalityManager
from services.tools.registry import tool_registry
# 添加工具自动发现导入
from services.tools.discovery import ToolDiscoverer
from services.mcp.discovery import discover_and_register_mcp_tools
# 添加mcp_manager导入用于列出MCP工具
from services.mcp.manager import mcp_manager
# 添加ToolManager导入用于工具调用
from services.tools.manager import ToolManager
# 添加引擎管理器导入
from core.engine_manager import get_engine_manager, get_current_engine
from core.chat_engine import ChatEngine

# 导入Pydantic模型
from schemas.api_schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatCompletionResponseUsage,
    ToolCallRequest,
    MCPServiceCallRequest
)

import warnings
# 忽略Pydantic的model_fields弃用警告
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*model_fields.*")
# 忽略FastAPI的on_event弃用警告
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*on_event.*")
config = get_config()

# 使用引擎管理器（统一入口）
engine_manager = get_engine_manager()

# 根据配置选择使用的聊天引擎
if config.CHAT_ENGINE == "mem0_proxy":
    from core.mem0_proxy import get_mem0_proxy
    # 初始化Mem0代理引擎（单例）
    mem0_engine = get_mem0_proxy()
    engine_manager.register_engine("mem0_proxy", mem0_engine)
    log.info("✅ Mem0 Proxy engine registered")
    chat_engine = mem0_engine  # 保持向后兼容
else:
    # 默认使用chat_engine
    chat_engine_instance = ChatEngine()
    engine_manager.register_engine("chat_engine", chat_engine_instance)
    log.info("✅ Chat Engine registered")
    chat_engine = chat_engine_instance  # 保持向后兼容

# 创建HTTPBearer安全方案
bearer_scheme = HTTPBearer()

# 创建FastAPI应用
app = FastAPI(
    title=config.API_TITLE,
    description=config.API_DESCRIPTION,
    version=config.API_VERSION,
    # 添加安全方案
    openapi_security=[
        {
            "Bearer Auth": {}
        }
    ],
    openapi_components={
        "securitySchemes": {
            "Bearer Auth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "API Key"
            }
        }
    }
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 初始化人格管理器
personality_manager = PersonalityManager()
# 初始化工具管理器
tool_manager = ToolManager()

# 认证依赖函数 - 更新为使用HTTPBearer
def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """验证API密钥，兼容OpenAI的认证方式"""
    # 从credentials中获取API密钥
    api_key = credentials.credentials
    
    # 验证API密钥是否匹配
    if api_key != config.YYCHAT_API_KEY:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "message": "Incorrect API key provided",
                    "type": "invalid_request_error",
                    "param": None,
                    "code": "invalid_api_key"
                }
            }
        )
    
    return api_key

# 在应用初始化时自动注册所有工具
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的初始化操作"""
    # 自动发现并注册所有工具
    registered_count = ToolDiscoverer.register_discovered_tools()
    log.debug(f"自动注册了 {registered_count} 个工具")
    
    # 初始化性能监控
    if config.ENABLE_PERFORMANCE_MONITOR:
        log.info(f"✅ 性能监控已启用 (采样率: {config.PERFORMANCE_SAMPLING_RATE*100:.0f}%, 历史记录: {config.PERFORMANCE_MAX_HISTORY}条)")
        # 设置监控器的最大历史记录数
        performance_monitor._max_history = config.PERFORMANCE_MAX_HISTORY
    else:
        log.info("⚪ 性能监控已禁用")
    
    # 初始化并注册MCP工具
    try:
        discover_and_register_mcp_tools()
    except Exception as e:
        log.error(f"Failed to initialize MCP tools: {str(e)}")

# 自定义异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error(f"API Error: {exc}", exc_info=True)
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
async def create_chat_completion(request: ChatCompletionRequest, api_key: str = Depends(verify_api_key)):
    try:
        # 打印完整的request内容，用于调试conversation_id问题
        log.debug(f"完整的请求内容: {request.model_dump()}")
        log.debug(f"request.conversation_id: {request.conversation_id}, type: {type(request.conversation_id)}")
        log.debug(f"request.user: {request.user}, type: {type(request.user)}")
        
        # 验证conversation_id，如果没有则使用user作为会话标识
        conversation_id = request.conversation_id or request.user
        
        # 如果仍然没有有效的conversation_id，设置一个默认值
        if not conversation_id:
            conversation_id = "default_conversation"
            log.warning(f"未提供有效的conversation_id和user，使用默认值: {conversation_id}")
            
        # 记录请求日志
        log.debug(f"Chat completion request: model={request.model}, conversation_id={conversation_id}")
        
        if request.stream:
            # 流式响应处理
            async def stream_generator():
                try:
                    generator = await chat_engine.generate_response(
                        request.messages,
                        conversation_id,
                        request.personality_id,
                        request.use_tools,
                        stream=True
                    )
                except Exception as gen_err:
                    log.error(f"Error creating stream generator: {gen_err}")
                    error_message = f"发生错误: {str(gen_err)}"
                    error_data = {
                        "id": f"chatcmpl-{conversation_id}",
                        "object": "chat.completion.chunk",
                        "created": int(asyncio.get_event_loop().time()),
                        "model": request.model,
                        "choices": [{"index": 0, "delta": {"content": error_message}, "finish_reason": "error"}]
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    yield 'data: [DONE]\n\n'
                    return
                
                try:
                    async for chunk in generator:
                        if chunk.get("stream", False):
                            response_data = {
                                "id": f"chatcmpl-{conversation_id}",
                                "object": "chat.completion.chunk",
                                "created": int(asyncio.get_event_loop().time()),
                                "model": request.model,
                                "choices": [{"index": 0, "delta": {"content": chunk["content"]}, "finish_reason": chunk["finish_reason"]}]
                            }
                            yield f"data: {json.dumps(response_data)}\n\n"
                            if chunk["finish_reason"] is not None:
                                break
                except Exception as iter_err:
                    log.error(f"Error in stream iteration: {iter_err}")
                    error_message = f"发生错误: {str(iter_err)}"
                    error_data = {
                        "id": f"chatcmpl-{conversation_id}",
                        "object": "chat.completion.chunk",
                        "created": int(asyncio.get_event_loop().time()),
                        "model": request.model,
                        "choices": [{"index": 0, "delta": {"content": error_message}, "finish_reason": "error"}]
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    yield 'data: [DONE]\n\n'
            
            return StreamingResponse(stream_generator(), media_type="text/event-stream")
        else:
            # 非流式响应处理
            response = await chat_engine.generate_response(
                request.messages,
                conversation_id,
                request.personality_id,
                request.use_tools,
                stream=False
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
        log.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail={"error": {"message": str(e), "type": "validation_error"}})
    except Exception as e:
        log.error(f"Chat completion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})

# 模型列表API
@app.get("/v1/models")
async def list_models(api_key: str = Depends(verify_api_key)):
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
async def get_model(model_id: str, api_key: str = Depends(verify_api_key)):
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
async def list_personalities(api_key: str = Depends(verify_api_key)):
    return {
        "object": "list",
        "data": personality_manager.list_personalities()
    }

# 清除会话记忆API
@app.delete("/v1/conversations/{conversation_id}/memory", tags=["Services"])
async def clear_conversation_memory(conversation_id: str, api_key: str = Depends(verify_api_key)):
    chat_engine.clear_conversation_memory(conversation_id)
    return {
        "success": True,
        "message": f"Memory for conversation {conversation_id} cleared"
    }

# 获取会话记忆API
@app.get("/v1/conversations/{conversation_id}/memory", tags=["Services"])
async def get_conversation_memory(conversation_id: str, api_key: str = Depends(verify_api_key)):
    memories = chat_engine.get_conversation_memory(conversation_id)
    return {
        "object": "list",
        "data": memories,
        "total": len(memories)
    }

@app.get("/api/verify-memory/{conversation_id}", tags=["Services"])
async def verify_memory(conversation_id: str, api_key: str = Depends(verify_api_key)):
    """验证指定会话ID的记忆是否存在"""
    try:
        memories = chat_engine.get_conversation_memory(conversation_id)
        return {
            "success": True,
            "conversation_id": conversation_id,
            "memory_count": len(memories),
            "memories": memories[:5]  # 只返回前5条避免响应过大
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# MCP服务调用API
@app.post("/v1/mcp/call", tags=["Services"])
async def call_mcp_service(request: MCPServiceCallRequest, api_key: str = Depends(verify_api_key)):
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
        result = chat_engine.call_mcp_service(
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
        log.error(f"MCP service call error: {e}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})
        
# 根路径API - 可以不需要认证
@app.get("/")
async def root():
    return {
        "message": f"Welcome to the YYChat OpenAI Compatible API",
        "version": config.API_VERSION,
        "api_endpoints": ["/v1/chat/completions", "/v1/models", "/v1/personalities"]
    }

# 列出所有工具
@app.get("/v1/tools", tags=["Services"])
async def list_available_tools(api_key: str = Depends(verify_api_key)):
    """列出所有已注册的非MCP工具"""
    try:
        # 获取所有工具
        all_tools = tool_registry.list_tools()
        
        # 尝试获取MCP工具名称，如果失败则忽略MCP工具
        mcp_tool_names = set()
        try:
            mcp_tools = mcp_manager.list_tools()
            mcp_tool_names = {tool["name"] for tool in mcp_tools}
        except Exception as mcp_error:
            log.warning(f"MCP service unavailable, listing all tools without MCP filtering: {str(mcp_error)}")
        
        # 过滤掉MCP工具，只保留非MCP工具
        non_mcp_tools = {name: tool for name, tool in all_tools.items() if name not in mcp_tool_names}
        
        return {
            "tools": [{
                "name": tool.name,
                "description": tool.description
            } for tool in non_mcp_tools.values()]
        }
    except Exception as e:
        log.error(f"Failed to list tools: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})

# 列出所有MCP工具
@app.get("/v1/mcp/tools", tags=["Services"])
async def list_available_mcp_tools(api_key: str = Depends(verify_api_key)):
    """列出所有已注册的MCP工具"""
    try:
        # 使用mcp_manager获取MCP工具列表
        mcp_tools = mcp_manager.list_tools()
        
        # 格式化返回结果，保持与现有工具API一致的格式
        return {
            "tools": [{k: v for k, v in tool.items() if k in ["name", "description"]} for tool in mcp_tools]
        }
    except Exception as e:
        log.error(f"Failed to list MCP tools: {str(e)}")
        # 返回空列表而不是抛出异常，这样客户端可以知道MCP服务不可用但仍然可以继续工作
        return {
            "tools": [],
            "error": {
                "message": f"MCP service temporarily unavailable: {str(e)}",
                "type": "mcp_service_error"
            }
        }

# 工具调用API - 用于调用非MCP工具
@app.post("/v1/tools/call", tags=["Services"])
async def call_tool(request: ToolCallRequest, api_key: str = Depends(verify_api_key)):
    """调用指定的非MCP工具"""
    try:
        # 提取参数
        tool_name = request.tool_name
        params = request.params
        
        if not tool_name:
            raise HTTPException(status_code=400, detail={"error": {"message": "Missing tool_name", "type": "validation_error"}})
        
        # 调用工具
        log.debug(f"Calling tool: {tool_name} with params: {params}")
        result = await tool_manager.execute_tool(tool_name, params)
        
        # 格式化返回结果
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        log.error(f"Tool call error: {e}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})

# 性能监控API
@app.get("/v1/performance/stats", tags=["Monitoring"])
async def get_performance_stats(api_key: str = Depends(verify_api_key)):
    """获取性能统计信息"""
    try:
        monitor = get_performance_monitor()
        stats = monitor.get_statistics()
        return stats
    except Exception as e:
        log.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})

# Dashboard专用API（无需认证，仅用于Dashboard）
@app.get("/api/dashboard/stats", tags=["Dashboard"])
async def get_dashboard_stats():
    """获取Dashboard性能统计信息（无需认证）"""
    try:
        monitor = get_performance_monitor()
        stats = monitor.get_statistics()
        return stats
    except Exception as e:
        log.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})

@app.get("/v1/performance/recent", tags=["Monitoring"])
async def get_recent_performance(count: int = 10, api_key: str = Depends(verify_api_key)):
    """获取最近的性能指标"""
    try:
        monitor = get_performance_monitor()
        recent = monitor.get_recent_metrics(count)
        return {"count": len(recent), "metrics": recent}
    except Exception as e:
        log.error(f"Failed to get recent performance: {e}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})

@app.delete("/v1/performance/clear", tags=["Monitoring"])
async def clear_performance_data(api_key: str = Depends(verify_api_key)):
    """清除性能监控数据"""
    try:
        monitor = get_performance_monitor()
        monitor.clear()
        return {"success": True, "message": "性能监控数据已清除"}
    except Exception as e:
        log.error(f"Failed to clear performance data: {e}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})

# 引擎管理API
@app.get("/v1/engines/list", tags=["Engine"])
async def list_engines(api_key: str = Depends(verify_api_key)):
    """列出所有已注册的引擎"""
    try:
        engines = await engine_manager.list_engines()
        return {
            "success": True,
            "current_engine": engine_manager.current_engine_name,
            "engines": engines,
            "count": len(engines)
        }
    except Exception as e:
        log.error(f"Failed to list engines: {e}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})

@app.get("/v1/engines/current", tags=["Engine"])
async def get_current_engine_info(api_key: str = Depends(verify_api_key)):
    """获取当前引擎信息"""
    try:
        current_engine = get_current_engine()
        if not current_engine:
            raise HTTPException(status_code=404, detail={"error": {"message": "No engine is currently active", "type": "not_found"}})
        
        info = await current_engine.get_engine_info()
        return {
            "success": True,
            "engine": info
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to get current engine info: {e}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})

@app.post("/v1/engines/switch", tags=["Engine"])
async def switch_engine(engine_name: str, api_key: str = Depends(verify_api_key)):
    """切换引擎"""
    try:
        result = await engine_manager.switch_engine(engine_name)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail={"error": {"message": result["message"], "type": "validation_error"}})
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to switch engine: {e}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})

@app.get("/v1/engines/health", tags=["Engine"])
async def check_engines_health(api_key: str = Depends(verify_api_key)):
    """检查所有引擎的健康状态"""
    try:
        health_status = await engine_manager.health_check_all()
        return {
            "success": True,
            **health_status
        }
    except Exception as e:
        log.error(f"Failed to check engines health: {e}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "server_error"}})

# Dashboard路由
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
async def get_dashboard():
    """访问性能监控Dashboard"""
    dashboard_path = os.path.join("static", "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    else:
        raise HTTPException(status_code=404, detail={"error": {"message": "Dashboard not found", "type": "not_found"}})

# 启动服务器
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=True
    )
