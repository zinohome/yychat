from typing import List, Dict, Any, Optional
from core.tools_adapter import filter_tools_schema, select_tool_choice


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
            params["tools"] = tools_schema
            if force_tool_from_message and messages:
                last_msg = messages[-1].get("content", "")
                tool_choice = select_tool_choice(last_msg, allowed_tool_names)
                if tool_choice:
                    params["tool_choice"] = tool_choice
    return params
