from typing import List, Dict, Any, Optional


TIME_TOOL_NAME = "gettime"

TIME_KEYWORDS = [
    # 中文
    "几点", "时间", "现在", "几点钟", "时刻", "日期", "今天", "当前时间",
    # 英文
    "time", "what time", "current time", "date", "today", "now",
]


def filter_tools_schema(all_tools_schema: List[Dict[str, Any]],
                        allowed_tool_names: Optional[List[str]]) -> List[Dict[str, Any]]:
    if not all_tools_schema:
        return []
    if not allowed_tool_names:
        return all_tools_schema
    allowed = set(allowed_tool_names)
    return [
        t for t in all_tools_schema
        if t.get("function", {}).get("name") in allowed
    ]


def select_tool_choice(last_message: str,
                       allowed_tool_names: Optional[List[str]]) -> Optional[Dict[str, Any]]:
    if not last_message:
        return None
    msg = last_message.lower()
    if any(k in msg for k in TIME_KEYWORDS):
        if (not allowed_tool_names) or (TIME_TOOL_NAME in allowed_tool_names):
            return {"type": "function", "function": {"name": TIME_TOOL_NAME}}
    return None


def normalize_tool_calls(sdk_tool_calls: List[Any]) -> List[Dict[str, Any]]:
    """
    将 SDK 的工具调用对象转换为 OpenAI 消息协议期望的可序列化 dict：
    [{"id": "...","type": "function","function": {"name": "...","arguments": "..."}}]
    """
    if not sdk_tool_calls:
        return []
    normalized: List[Dict[str, Any]] = []
    for call in sdk_tool_calls:
        # 兼容 Streaming/Non-streaming 不同字段
        call_id = getattr(call, "id", None) or getattr(call, "tool_call_id", None)
        fn = getattr(call, "function", None) or {}
        name = getattr(fn, "name", None) or (fn.get("name") if isinstance(fn, dict) else None)
        args = getattr(fn, "arguments", None) or (fn.get("arguments") if isinstance(fn, dict) else None)
        normalized.append({
            "id": call_id,
            "type": "function",
            "function": {
                "name": name,
                "arguments": args if isinstance(args, str) else (args or ""),
            }
        })
    return normalized


def build_tool_response_messages(normalized_calls: List[Dict[str, Any]],
                                 tool_exec_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    根据规范化 tool_calls 与执行结果构造 tool 角色消息：
    [{"tool_call_id": "...","role":"tool","name":"fn_name","content":"..."}]
    """
    msgs: List[Dict[str, Any]] = []
    for i, res in enumerate(tool_exec_results):
        call = normalized_calls[i] if i < len(normalized_calls) else None
        fn_name = res.get("tool_name")
        success = res.get("success")
        payload = res.get("result") if success else res.get("error", "未知错误")
        content = f"工具 '{fn_name}' 调用结果: {payload}" if success else f"工具 '{fn_name}' 调用失败: {payload}"
        msgs.append({
            "tool_call_id": call.get("id") if call else None,
            "role": "tool",
            "name": fn_name or (call.get("function", {}).get("name") if call else None),
            "content": content,
        })
    return msgs
