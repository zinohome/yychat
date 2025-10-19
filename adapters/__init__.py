"""
实时语音适配器模块
提供记忆、人格、工具适配器，用于实时语音功能
"""

from .memory_adapter import MemoryAdapter, memory_adapter
from .personality_adapter import PersonalityAdapter, personality_adapter
from .tool_adapter import ToolAdapter, tool_adapter

__all__ = [
    'MemoryAdapter',
    'memory_adapter',
    'PersonalityAdapter', 
    'personality_adapter',
    'ToolAdapter',
    'tool_adapter'
]
