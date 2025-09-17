import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # OpenAI配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.75"))  # 在配置中直接转换为浮点数
    
    # Mem0配置
    MEM0_API_KEY = os.getenv("MEM0_API_KEY")
    
    # ChromaDB配置
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "chat_history")
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # MCP服务配置
    MCP_SERVICE_URL = os.getenv("MCP_SERVICE_URL")
    MCP_API_KEY = os.getenv("MCP_API_KEY")
    MCP_CACHE_TTL = int(os.getenv("MCP_CACHE_TTL", "300"))
    
    # 服务器配置
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# 创建配置实例
def get_config():
    return Config()