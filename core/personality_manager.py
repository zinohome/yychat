import json
import os
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Optional, List
from utils.log import log



class Personality(BaseModel):
    id: str = Field(..., description="人格ID")
    name: str = Field(..., description="人格名称")
    system_prompt: str = Field(..., description="系统提示词")
    traits: List[str] = Field(default_factory=list, description="人格特质")
    examples: List[str] = Field(default_factory=list, description="对话示例")
    allowed_tools: List[Dict[str, str]] = Field(default_factory=list, description="允许使用的工具及使用条件")

class PersonalityManager:
    def __init__(self, personalities_dir: str = "./personalities"):
        self.personalities_dir = personalities_dir
        self.personalities: Dict[str, Personality] = {}
        self._ensure_dir_exists()
        self._load_personalities()
        
        # 预定义一些默认人格
        self._load_default_personalities()
    
    def _ensure_dir_exists(self):
        if not os.path.exists(self.personalities_dir):
            os.makedirs(self.personalities_dir)
    
    def _load_default_personalities(self):
        # 如果没有人格文件，创建一些默认人格
        if not self.personalities:
            default_personalities = [
                Personality(
                    id="professional",
                    name="专业助手",
                    system_prompt="你是一个专业的AI助手，总是提供准确、详细的信息和建议。",
                    traits=["专业", "准确", "详细"],
                    examples=[
                        "用户: 什么是机器学习？\n助手: 机器学习是人工智能的一个分支..."
                    ]
                ),
                Personality(
                    id="friendly",
                    name="友好伙伴",
                    system_prompt="你是一个友好、亲切的聊天伙伴，用轻松愉快的语气交流。",
                    traits=["友好", "亲切", "幽默"],
                    examples=[
                        "用户: 今天天气怎么样？\n助手: 今天天气真不错！阳光明媚，很适合出去走走呢！"
                    ]
                )
            ]
            
            for personality in default_personalities:
                self.add_personality(personality)
                self.save_personality(personality)
    
    def _load_personalities(self):
        try:
            for filename in os.listdir(self.personalities_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(self.personalities_dir, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            personality = Personality(**data)
                            self.personalities[personality.id] = personality
                    except (json.JSONDecodeError, ValidationError) as e:
                        log.error(f"Failed to load personality from {file_path}: {e}")
        except Exception as e:
            log.error(f"Error loading personalities: {e}")
    
    def add_personality(self, personality: Personality):
        self.personalities[personality.id] = personality
    
    def get_personality(self, personality_id: str) -> Optional[Personality]:
        return self.personalities.get(personality_id)
    
    def save_personality(self, personality: Personality):
        file_path = os.path.join(self.personalities_dir, f"{personality.id}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(personality.model_dump(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(f"Failed to save personality {personality.id}: {e}")
    
    def list_personalities(self) -> List[Dict[str, str]]:
        return [
            {"id": p.id, "name": p.name}
            for p in self.personalities.values()
        ]
    
    def apply_personality(self, messages: List[Dict[str, str]], personality_id: str) -> List[Dict[str, str]]:
        personality = self.get_personality(personality_id)
        if not personality:
            log.warning(f"Personality {personality_id} not found, using default")
            return messages
        
        # 构建包含工具使用规则的系统提示词
        system_content = personality.system_prompt
        
        if personality.allowed_tools:
            tool_rules = "\n\n工具使用规则：\n"
            for tool in personality.allowed_tools:
                tool_rules += f"- {tool['description']}\n"
            system_content += tool_rules
        
        # 在消息列表最前面添加系统提示词
        result = [{"role": "system", "content": system_content}]
        result.extend(messages)
        return result