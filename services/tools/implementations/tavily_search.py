from ..base import Tool
from ..registry import tool_registry
from tavily import TavilyClient
import os
from config.config import get_config
from typing import Dict, Any  # 添加缺失的类型导入

config = get_config()
class TavilySearchTool(Tool):
    @property
    def name(self) -> str:
        return "tavily_search"
    
    @property
    def description(self) -> str:
        return "用于在互联网上搜索信息的工具，可以获取关于特定问题的答案和相关搜索结果"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "query": {
                "type": "string",
                "description": "要搜索的查询语句，例如'谁是梅西？'或'2024年奥运会在哪里举行？'"
            },
            "search_depth": {
                "type": "string",
                "enum": ["basic", "advanced"],
                "description": "搜索深度，basic为基本搜索，advanced为高级搜索，默认为basic",
                "default": "basic"
            }
        }
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # 处理不同格式的参数
        # 尝试直接获取query参数
        query = params.get("query")
        
        # 如果没有直接获取到query，检查是否是嵌套格式
        if not query:
            # 检查params中是否有嵌套的查询参数
            if isinstance(params, dict):
                # 处理可能的嵌套情况
                for key, value in params.items():
                    if isinstance(value, dict) and "query" in value:
                        query = value["query"]
                        break
        
        if not query:
            raise ValueError("搜索查询不能为空")
        
        # 获取搜索深度参数，如果没有提供则使用默认值
        search_depth = params.get("search_depth", "basic")
        
        # 从环境变量获取API密钥
        api_key=config.TAVILY_API_KEY
        if not api_key:
            raise ValueError("未配置Tavily API密钥，请设置环境变量TAVILY_API_KEY")
        
        # 创建Tavily客户端并执行搜索
        try:
            tavily_client = TavilyClient(api_key=api_key)
            response = tavily_client.search(
                query=query,
                search_depth=search_depth,
                topic="general",  # 默认添加topic参数
                country="china"   # 默认添加country参数
            )
            
            # 组织返回结果
            return {
                "query": response.get("query"),
                "answer": response.get("answer"),
                "images": response.get("images", []),
                "results": [
                    {
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "content": item.get("content"),
                        "score": item.get("score")
                    } for item in response.get("results", [])
                ],
                "response_time": response.get("response_time"),
                "request_id": response.get("request_id")
            }
        except Exception as e:
            raise Exception(f"Tavily搜索执行失败: {str(e)}")

# 注册工具（传入类，不是实例）
tool_registry.register(TavilySearchTool)