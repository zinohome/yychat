
from typing import Dict, Any, Optional
import asyncio  # 添加asyncio模块导入
from .registry import tool_registry
from utils.log import log


class ToolManager:
    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            log.warning(f"Tool {tool_name} not found")
            return None
        
        try:
            # 异步执行工具
            log.debug(f"Executing tool: {tool_name} with params: {params}")
            result = await tool.execute(params)
            log.debug(f"Tool {tool_name} executed successfully. Result: {result}")
            return {"success": True, "result": result}
        except Exception as e:
            log.error(f"Error executing tool {tool_name}: {e}")
            return {"success": False, "error": str(e)}
    
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
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "tool_name": tool_calls[i]["name"]
                })
            else:
                processed_results.append(result)
                # 只有当result不是None时才添加tool_name
                if result is not None:
                    processed_results[-1]["tool_name"] = tool_calls[i]["name"]
        
        return processed_results