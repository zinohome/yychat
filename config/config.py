from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

class Config:
    # OpenAI配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.75")) # 在配置中直接转换为浮点数
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "16384"))  # 在配置中直接转换为整数
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    
    # 本服务的API密钥配置
    YYCHAT_API_KEY = os.getenv("YYCHAT_API_KEY", "yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4")
    
    # Mem0配置
    MEM0_API_KEY = os.getenv("MEM0_API_KEY")
    MEM0_LLM_PROVIDER = os.getenv("MEM0_LLM_PROVIDER", "openai")
    MEM0_LLM_CONFIG_MODEL = os.getenv("MEM0_LLM_CONFIG_MODEL", "gpt-4.1")
    MEM0_LLM_CONFIG_MAX_TOKENS = int(os.getenv("MEM0_LLM_CONFIG_MAX_TOKENS", "32768"))
    
    # ChromaDB配置
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "chat_history")
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Memory配置
    # 控制会话中写入memory的时机
    # 可选值: both(同时保存用户输入和助手回复), user_only(只保存用户输入), assistant_only(只保存助手回复)
    MEMORY_SAVE_MODE = os.getenv("MEMORY_SAVE_MODE", "both")
    
    # 服务器配置
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
    
    # 默认人格配置
    DEFAULT_PERSONALITY = os.getenv("DEFAULT_PERSONALITY", "health_assistant")
    
    # 响应流和工具使用默认配置
    STREAM_DEFAULT = os.getenv("STREAM_DEFAULT", "True").lower() == "true"
    USE_TOOLS_DEFAULT = os.getenv("USE_TOOLS_DEFAULT", "True").lower() == "true"
    
    # API元数据配置
    API_TITLE = os.getenv("API_TITLE", "YYChat OpenAI兼容API")
    API_DESCRIPTION = os.getenv("API_DESCRIPTION", "YYChat是一个基于OpenAI API的聊天机器人，使用Mem0和ChromaDB进行记忆管理。")
    API_VERSION = os.getenv("API_VERSION", "0.1.1")

# 创建配置实例
def get_config():
    return Config()