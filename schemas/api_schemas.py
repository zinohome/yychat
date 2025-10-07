from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from config.config import get_config

# 获取配置
config = get_config()

# 聊天完成请求模型
class ChatCompletionRequest(BaseModel):
    model: str = Field(default=config.OPENAI_MODEL, description="使用的模型名称，默认使用配置中的模型")
    messages: List[Dict[str, str]] = Field(..., description="消息历史")
    temperature: float = Field(default=0.7, description="采样温度")
    max_tokens: Optional[int] = Field(default=None, description="最大生成token数")
    top_p: float = Field(default=1.0, description="核采样")
    n: int = Field(default=1, description="生成的响应数量")
    stream: bool = Field(default=False, description="是否使用流式输出")
    stop: Optional[Union[str, List[str]]] = Field(default=None, description="停止词")
    presence_penalty: float = Field(default=0.0, description="存在惩罚")
    frequency_penalty: float = Field(default=0.0, description="频率惩罚")
    logit_bias: Optional[Dict[str, float]] = Field(default=None, description="logit偏置")
    user: Optional[str] = Field(default=None, description="用户标识")
    # 自定义字段
    conversation_id: Optional[str] = Field(default=None, description="会话ID")
    personality_id: Optional[str] = Field(default=None, description="人格ID")
    use_tools: bool = Field(default=True, description="是否使用工具")

# 聊天完成响应选择模型
class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: Dict[str, Any]  # 修改为接受任何类型值的字典
    finish_reason: Optional[str] = None

# 聊天完成响应使用统计模型
class ChatCompletionResponseUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

# 聊天完成响应模型
class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: Optional[ChatCompletionResponseUsage] = None

# 工具调用请求模型
class ToolCallRequest(BaseModel):
    tool_name: str = Field(..., description="要调用的工具名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="工具参数")

# MCP服务调用请求模型
class MCPServiceCallRequest(BaseModel):
    tool_name: Optional[str] = Field(None, description="要调用的工具名称")
    mcp_server: Optional[str] = Field(None, description="指定的MCP服务器")
    params: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    service_name: Optional[str] = Field(None, description="MCP服务名称")
    method_name: Optional[str] = Field(None, description="MCP服务方法名称")