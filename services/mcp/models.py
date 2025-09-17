from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class MCPRequest(BaseModel):
    service_name: str = Field(..., description="MCP服务名称")
    method_name: str = Field(..., description="方法名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="方法参数")
    timeout: int = Field(default=30, description="请求超时时间（秒）")

class MCPResponse(BaseModel):
    success: bool = Field(..., description="请求是否成功")
    result: Optional[Any] = Field(default=None, description="请求结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    request_id: Optional[str] = Field(default=None, description="请求ID")