from dotenv import load_dotenv, find_dotenv
import os
import sys


# 获取当前文件所在目录的绝对路径
base_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(base_dir)
# 构造.env文件的绝对路径
env_path = os.path.join(project_root, '.env')

# 加载环境变量，并处理可能的错误
try:
    # find_dotenv会尝试定位.env文件，fallback到我们指定的路径
    env_file = find_dotenv(usecwd=True) or env_path
    
    # 加载.env文件，如果不存在则尝试创建
    if os.path.exists(env_file):
        load_dotenv(dotenv_path=env_file, override=True)
        print(f"成功加载.env文件: {env_file}")
    else:
        # 如果.env文件不存在，可以选择创建一个默认的
        print(f".env文件不存在: {env_file}")
        # 注意：如果要自动创建.env文件，可以取消下面的注释
        # with open(env_file, 'w') as f:
        #     f.write("# 默认环境变量配置\n")
except Exception as e:
    print(f"加载.env文件时出错: {str(e)}")

# 添加以下配置项
# 在Config类中添加
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
    MEM0_BASE_URL = os.getenv("MEM0_BASE_URL", "http://192.168.66.163:8765")
    MEMO_USE_LOCAL = os.getenv("MEMO_USE_LOCAL", "false").lower() == "true"
    MEM0_LLM_PROVIDER = os.getenv("MEM0_LLM_PROVIDER", "openai")
    MEM0_LLM_CONFIG_MODEL = os.getenv("MEM0_LLM_CONFIG_MODEL", "gpt-4.1")
    MEM0_LLM_CONFIG_MAX_TOKENS = int(os.getenv("MEM0_LLM_CONFIG_MAX_TOKENS", "32768"))
    
    # ChromaDB配置
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "chat_history")
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE_NAME = os.getenv("LOG_FILE_NAME", "app.log")
    
    # 服务器配置
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
    
    # 聊天引擎配置
    # 可选值: chat_engine, mem0_proxy
    # 默认值: chat_engine
    CHAT_ENGINE = os.getenv("CHAT_ENGINE", "chat_engine")
    
    # 默认人格配置
    DEFAULT_PERSONALITY = os.getenv("DEFAULT_PERSONALITY", "health_assistant")
    
    # 响应流和工具使用默认配置
    STREAM_DEFAULT = os.getenv("STREAM_DEFAULT", "True").lower() == "true"
    USE_TOOLS_DEFAULT = os.getenv("USE_TOOLS_DEFAULT", "True").lower() == "true"
    
    # API元数据配置
    API_TITLE = os.getenv("API_TITLE", "YYChat OpenAI兼容API")
    API_DESCRIPTION = os.getenv("API_DESCRIPTION", "YYChat是一个基于OpenAI API的聊天机器人，使用Mem0和ChromaDB进行记忆管理。")
    API_VERSION = os.getenv("API_VERSION", "0.1.1")
    
    # API性能相关配置 - 从环境变量读取，设置当前值为默认值
    # OpenAI API性能配置
    OPENAI_API_TIMEOUT = float(os.getenv("OPENAI_API_TIMEOUT", "30.0"))
    OPENAI_CONNECT_TIMEOUT = float(os.getenv("OPENAI_CONNECT_TIMEOUT", "10.0"))
    OPENAI_READ_TIMEOUT = float(os.getenv("OPENAI_READ_TIMEOUT", "30.0"))
    OPENAI_WRITE_TIMEOUT = float(os.getenv("OPENAI_WRITE_TIMEOUT", "10.0"))
    OPENAI_POOL_TIMEOUT = float(os.getenv("OPENAI_POOL_TIMEOUT", "30.0"))
    OPENAI_API_RETRIES = int(os.getenv("OPENAI_API_RETRIES", "2"))
    
    # HTTP客户端配置
    MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS", "100"))
    MAX_KEEPALIVE_CONNECTIONS = int(os.getenv("MAX_KEEPALIVE_CONNECTIONS", "20"))
    KEEPALIVE_EXPIRY = int(os.getenv("KEEPALIVE_EXPIRY", "30"))
    VERIFY_SSL = os.getenv("VERIFY_SSL", "false").lower() == "true"
    
    # 记忆管理配置
    MEMORY_RETRIEVAL_LIMIT = int(os.getenv("MEMORY_RETRIEVAL_LIMIT", "5"))
    MEMORY_RETRIEVAL_TIMEOUT = float(os.getenv("MEMORY_RETRIEVAL_TIMEOUT", "2.0"))
    
    # 流式响应优化配置
    CHUNK_SPLIT_THRESHOLD = int(os.getenv("CHUNK_SPLIT_THRESHOLD", "100"))
    # Memory配置
    # 控制会话中写入memory的时机
    # 可选值: both(同时保存用户输入和助手回复), user_only(只保存用户输入), assistant_only(只保存助手回复)
    MEMORY_SAVE_MODE = os.getenv("MEMORY_SAVE_MODE", "both")
    
# 创建配置实例
def get_config():
    return Config()