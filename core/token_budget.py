from typing import List, Dict, Any


def estimate_tokens(messages: List[Dict[str, Any]]) -> int:
    """
    粗略估算 token 数。若无 tiktoken 依赖，回退到 char/4。
    """
    try:
        import tiktoken  # type: ignore
        enc = tiktoken.get_encoding("cl100k_base")
        text = "\n".join([(m.get("content") or "") for m in messages])
        return len(enc.encode(text))
    except Exception:
        return sum(len(m.get("content", "")) for m in messages) // 4


def should_include_memory(messages: List[Dict[str, Any]], memory_section: str, max_tokens: int, safety_ratio: float = 0.8) -> bool:
    memory_tokens = len(memory_section) // 4
    user_tokens = estimate_tokens(messages)
    return (memory_tokens + user_tokens) < int(max_tokens * safety_ratio)
