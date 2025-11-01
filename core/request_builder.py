from typing import List, Dict, Any, Optional
from core.tools_adapter import filter_tools_schema, select_tool_choice
from services.tools.registry import tool_registry
from services.mcp.discovery import discover_and_register_mcp_tools
from utils.log import log


def build_request_params(
    *,
    model: str,
    temperature: float,
    messages: List[Dict[str, Any]],
    use_tools: bool,
    all_tools_schema: Optional[List[Dict[str, Any]]] = None,
    allowed_tool_names: Optional[List[str]] = None,
    force_tool_from_message: bool = True
) -> Dict[str, Any]:
    """
    返回可直接传入 OpenAI Chat Completions 的 dict。
    仅负责“参数组装与工具过滤/选择”，不负责插入人格/记忆。
    """
    params: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": float(temperature),
    }

    if use_tools:
        tools_schema = filter_tools_schema(all_tools_schema or [], allowed_tool_names)
        if tools_schema:
            # 预先设置 tools
            params["tools"] = tools_schema
        if force_tool_from_message and messages:
            # 只检查用户消息（role='user'），避免AI回复触发工具调用
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            if user_messages:
                last_user_msg = user_messages[-1].get("content", "")
                tool_choice = select_tool_choice(last_user_msg, allowed_tool_names)
            else:
                tool_choice = None
            if tool_choice:
                params["tool_choice"] = tool_choice
                # 安全兜底：若被选择的工具不在 tools 列表，动态补齐其 schema
                try:
                    chosen_name = tool_choice.get("function", {}).get("name") if isinstance(tool_choice, dict) else None
                    if chosen_name:
                        present = any(
                            (t.get("function", {}).get("name") == chosen_name) for t in params.get("tools", [])
                        )
                        if not present:
                            log.info(f"tools 中缺少被选择的工具 '{chosen_name}'，尝试从注册表获取并补充schema")
                            tool_obj = tool_registry.get_tool(chosen_name)
                            # 若未注册（常见于MCP动态工具还未完成发现），立即触发一次发现-注册
                            if tool_obj is None:
                                try:
                                    log.info("触发一次 MCP 工具发现与注册以补齐schema…")
                                    discover_and_register_mcp_tools()
                                except Exception as e:
                                    log.warning(f"触发MCP发现失败（忽略继续）: {e}")
                                tool_obj = tool_registry.get_tool(chosen_name)
                            if tool_obj is not None:
                                chosen_schema = tool_obj.to_function_call_schema()
                                params.setdefault("tools", []).append(chosen_schema)
                                log.info(f"已补充 tools schema: {chosen_name}")
                            else:
                                log.warning(f"未能在注册表中找到工具 '{chosen_name}' 的实现，继续无工具回退")
                except Exception:
                    # 静默忽略，保持稳健
                    pass
    return params
