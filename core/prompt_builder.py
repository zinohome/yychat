from typing import List, Dict


def compose_system_prompt(existing_messages: List[Dict], personality_system: str, memory_section: str) -> List[Dict]:
    """
    将人格与记忆合成一个 system 提示，放在队首；避免重复 system 叠加。
    """
    messages = [m.copy() for m in existing_messages]
    system_blocks = []
    if personality_system:
        system_blocks.append(personality_system.strip())
    if memory_section:
        system_blocks.append(memory_section.strip())
    if system_blocks:
        merged = "\n\n".join(system_blocks)
        # 去除已有的开头 system，避免重复注入
        while messages and messages[0].get("role") == "system":
            messages.pop(0)
        messages.insert(0, {"role": "system", "content": merged})
    return messages
