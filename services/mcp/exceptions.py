"""MCP服务异常定义"""


class MCPServiceError(Exception):
    """MCP服务基础异常类"""
    pass


class MCPConnectionError(MCPServiceError):
    """MCP连接异常"""
    pass


class MCPServerError(MCPServiceError):
    """MCP服务器返回错误"""
    pass


class MCPClientError(MCPServiceError):
    """MCP客户端错误"""
    pass


class MCPServerNotFoundError(MCPServiceError):
    """MCP服务器未找到异常"""
    pass


class MCPToolNotFoundError(MCPServiceError):
    """MCP工具未找到异常"""
    pass