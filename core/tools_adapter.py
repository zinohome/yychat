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
    """
    根据用户消息选择要强制使用的工具
    
    注意：只有当工具在 allowed_tool_names 中时才会返回 tool_choice
    这样可以避免 OpenAI API 报错：tool_choice 指定的工具不在 tools 列表中
    """
    if not last_message:
        return None
    msg = last_message.lower()
    if any(k in msg for k in TIME_KEYWORDS):
        # 只有当没有限制或者 gettime 在允许列表中时才强制使用
        if not allowed_tool_names:
            # 没有限制，可以使用
            return {"type": "function", "function": {"name": TIME_TOOL_NAME}}
        elif TIME_TOOL_NAME in allowed_tool_names:
            # gettime 在允许列表中，可以使用
            return {"type": "function", "function": {"name": TIME_TOOL_NAME}}
        else:
            # gettime 不在允许列表中，不强制使用（让模型自由选择或不用工具）
            return None
    return None


def normalize_tool_calls(sdk_tool_calls: List[Any]) -> List[Dict[str, Any]]:
    """
    将 SDK 的工具调用对象转换为 OpenAI 消息协议期望的可序列化 dict：
    [{"id": "...","type": "function","function": {"name": "...","arguments": "..."}}]
    
    兼容：
    1. SDK 对象（有属性）
    2. 字典（已经是我们自己收集的格式）
    """
    if not sdk_tool_calls:
        return []
    normalized: List[Dict[str, Any]] = []
    for call in sdk_tool_calls:
        # 判断是字典还是对象
        if isinstance(call, dict):
            # 已经是字典格式，直接使用
            call_id = call.get("id")
            fn = call.get("function", {})
            name = fn.get("name") if isinstance(fn, dict) else None
            args = fn.get("arguments") if isinstance(fn, dict) else None
        else:
            # SDK 对象，使用 getattr
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
