
from typing import Dict, Any, Optional
import asyncio  # 添加asyncio模块导入
from .registry import tool_registry
from utils.log import log


class ToolManager:
    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            log.warning(f"Tool {tool_name} not found")
            return {
                "success": False, 
                "error": f"工具 '{tool_name}' 未找到",
                "tool_name": tool_name
            }
        
        try:
            # 异步执行工具
            log.debug(f"Executing tool: {tool_name} with params: {params}")
            result = await tool.execute(params)
            log.debug(f"Tool {tool_name} execution finished. Success: True")
            return {"success": True, "result": result, "tool_name": tool_name}
        except Exception as e:
            log.error(f"Error executing tool {tool_name}: {e}")
            return {"success": False, "error": str(e), "tool_name": tool_name}
    
    async def execute_tools_concurrently(self, tool_calls: list) -> list:
        # 并行执行多个工具
        tasks = []
        for call in tool_calls:
            task = self.execute_tool(call["name"], call["parameters"])
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 异常情况：返回错误信息
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "tool_name": tool_calls[i]["name"]
                })
            else:
                # 正常情况：execute_tool 已经返回完整的字典
                processed_results.append(result)
        
        return processed_results