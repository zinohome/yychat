"""
实时语音API请求/响应Schema
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class MemoryRequest(BaseModel):
    """记忆请求Schema"""
    conversation_id: str = Field(..., description="对话ID")
    query: str = Field(..., description="查询内容")


class MemoryResponse(BaseModel):
    """记忆响应Schema"""
    status: str = Field(..., description="状态")
    data: List[str] = Field(..., description="记忆列表")
    conversation_id: str = Field(..., description="对话ID")
    query: str = Field(..., description="查询内容")


class PersonalityRequest(BaseModel):
    """人格请求Schema"""
    personality_id: str = Field(..., description="人格ID")


class PersonalityResponse(BaseModel):
    """人格响应Schema"""
    status: str = Field(..., description="状态")
    data: Dict[str, Any] = Field(..., description="人格配置")
    personality_id: str = Field(..., description="人格ID")


class ToolsRequest(BaseModel):
    """工具请求Schema"""
    personality_id: Optional[str] = Field(None, description="人格ID")


class ToolsResponse(BaseModel):
    """工具响应Schema"""
    status: str = Field(..., description="状态")
    data: List[Dict[str, Any]] = Field(..., description="工具列表")
    personality_id: Optional[str] = Field(None, description="人格ID")


class ToolExecuteRequest(BaseModel):
    """工具执行请求Schema"""
    tool_name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(..., description="工具参数")


class ToolExecuteResponse(BaseModel):
    """工具执行响应Schema"""
    status: str = Field(..., description="状态")
    data: Dict[str, Any] = Field(..., description="执行结果")
    tool_name: str = Field(..., description="工具名称")


class SaveMemoryRequest(BaseModel):
    """保存记忆请求Schema"""
    conversation_id: str = Field(..., description="对话ID")
    content: str = Field(..., description="记忆内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class SaveMemoryResponse(BaseModel):
    """保存记忆响应Schema"""
    status: str = Field(..., description="状态")
    data: Dict[str, Any] = Field(..., description="保存结果")
    conversation_id: str = Field(..., description="对话ID")


class RealtimeSessionRequest(BaseModel):
    """实时语音会话请求Schema"""
    conversation_id: str = Field(..., description="对话ID")
    personality_id: Optional[str] = Field(None, description="人格ID")
    session_config: Optional[Dict[str, Any]] = Field(None, description="会话配置")


class RealtimeSessionResponse(BaseModel):
    """实时语音会话响应Schema"""
    status: str = Field(..., description="状态")
    data: Dict[str, Any] = Field(..., description="会话信息")
    conversation_id: str = Field(..., description="对话ID")


class ErrorResponse(BaseModel):
    """错误响应Schema"""
    status: str = Field(..., description="状态")
    error: str = Field(..., description="错误信息")
    error_type: str = Field(..., description="错误类型")
