from typing import List, Dict, Any, Optional
import re


TIME_TOOL_NAME = "gettime"
WEATHER_TOOL_NAME = "maps_weather"

TIME_KEYWORDS = [
    # 中文
    "几点", "时间", "现在", "几点钟", "时刻", "日期", "当前时间",
    # 英文
    "time", "what time", "current time", "date", "now",
]

WEATHER_KEYWORDS = [
    # 中文 - 更精确的关键词，避免误触发
    "天气", "天气预报", "今天天气", "明天天气", "查询天气", "天气怎么样", "天气如何",
    "气温", "多少度", "温度多少", 
    "下雨", "晴天", "阴天", "多云", "降雨", "降雪", "刮风", "雾霾",
    # 英文 - 完整短语匹配，避免单词误匹配
    "what's the weather", "weather forecast", "weather today", "weather tomorrow",
    "how's the weather", "weather condition", "weather report"
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
    
    改进：使用更精确的关键词匹配，避免误触发
    """
    if not last_message:
        return None
    
    msg = last_message.lower()
    msg_cleaned = msg.strip()
    
    # 优先检查天气关键词（天气查询优先级更高）
    # 使用更精确的匹配：检查完整短语或短语边界
    weather_triggered = False
    for keyword in WEATHER_KEYWORDS:
        # 检查完整短语匹配或短语边界匹配（避免单词误匹配）
        if keyword in msg_cleaned:
            # 对于中文关键词，检查是否在句子边界或前后是标点/空格
            # 对于英文短语，直接检查是否包含
            if len(keyword) <= 2:  # 单个或两个字符的关键词
                # 检查前后是否为标点、空格或中文字符边界
                pattern = rf'(?:^|[^\w]){re.escape(keyword)}(?:[^\w]|$)'
                if re.search(pattern, msg_cleaned):
                    weather_triggered = True
                    break
            else:  # 短语关键词，直接匹配
                weather_triggered = True
                break
    
    if weather_triggered:
        # 只有当没有限制或者 maps_weather 在允许列表中时才强制使用
        if not allowed_tool_names:
            # 没有限制，可以使用
            return {"type": "function", "function": {"name": WEATHER_TOOL_NAME}}
        elif WEATHER_TOOL_NAME in allowed_tool_names:
            # maps_weather 在允许列表中，可以使用
            return {"type": "function", "function": {"name": WEATHER_TOOL_NAME}}
        else:
            # maps_weather 不在允许列表中，不强制使用（让模型自由选择或不用工具）
            return None
    
    # 然后检查时间关键词
    time_triggered = False
    for keyword in TIME_KEYWORDS:
        # 对于中文关键词，使用更精确的匹配
        if keyword in msg_cleaned:
            if len(keyword) <= 2:  # 单个或两个字符的关键词
                pattern = rf'(?:^|[^\w]){re.escape(keyword)}(?:[^\w]|$)'
                if re.search(pattern, msg_cleaned):
                    time_triggered = True
                    break
            else:
                time_triggered = True
                break
    
    if time_triggered:
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
