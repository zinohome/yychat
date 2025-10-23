from dotenv import load_dotenv, find_dotenv
import os
import sys


# 获取当前文件所在目录的绝对路径
base_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(base_dir)
# 构造.env文件的绝对路径
env_path = os.path.join(project_root, '.env')

# 延迟加载环境变量，避免重复加载
_env_loaded = False

def load_env_file():
    """加载.env文件（延迟初始化，避免重复加载）"""
    global _env_loaded
    if _env_loaded:
        return
    
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
        
        _env_loaded = True
    except Exception as e:
        print(f"加载.env文件时出错: {str(e)}")

# 在首次导入时加载环境变量
load_env_file()

# 添加以下配置项
# 在Config类中添加
class Config:
    # ============================================
    # 🔑 核心API密钥配置
    # ============================================
    # OpenAI API密钥
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # YYChat API密钥
    YYCHAT_API_KEY = os.getenv("YYCHAT_API_KEY", "yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4")
    # 外部服务API密钥
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    
    # ============================================
    # 🤖 AI模型配置
    # ============================================
    # OpenAI模型配置
    # OpenAI模型名称
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")
    # OpenAI API基础URL
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    # 模型温度参数 (0.0-2.0)
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.75"))
    # 最大token数量
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "16384"))
    
    # ============================================
    # 🧠 记忆管理配置
    # ============================================
    # Mem0配置
    # Mem0 API密钥
    MEM0_API_KEY = os.getenv("MEM0_API_KEY")
    # Mem0服务地址
    MEM0_BASE_URL = os.getenv("MEM0_BASE_URL", "http://192.168.66.163:8765")
    # 是否使用本地Mem0
    MEMO_USE_LOCAL = os.getenv("MEMO_USE_LOCAL", "false").lower() == "true"
    # Mem0 LLM提供商
    MEM0_LLM_PROVIDER = os.getenv("MEM0_LLM_PROVIDER", "openai")
    # Mem0 LLM模型
    MEM0_LLM_CONFIG_MODEL = os.getenv("MEM0_LLM_CONFIG_MODEL", "gpt-4.1")
    # Mem0 LLM最大token数
    MEM0_LLM_CONFIG_MAX_TOKENS = int(os.getenv("MEM0_LLM_CONFIG_MAX_TOKENS", "32768"))
    # Mem0嵌入模型
    MEM0_EMBEDDER_MODEL = os.getenv("MEM0_EMBEDDER_MODEL", "text-embedding-3-small")
    
    # 记忆检索配置
    # 记忆检索数量限制
    MEMORY_RETRIEVAL_LIMIT = int(os.getenv("MEMORY_RETRIEVAL_LIMIT", "5"))
    # 记忆检索超时时间 (秒)
    MEMORY_RETRIEVAL_TIMEOUT = float(os.getenv("MEMORY_RETRIEVAL_TIMEOUT", "0.5"))
    # 是否启用记忆检索
    ENABLE_MEMORY_RETRIEVAL = os.getenv("ENABLE_MEMORY_RETRIEVAL", "true").lower() == "true"
    # 控制会话中写入memory的时机
    # 可选值: both(同时保存用户输入和助手回复), user_only(只保存用户输入), assistant_only(只保存助手回复)
    MEMORY_SAVE_MODE = os.getenv("MEMORY_SAVE_MODE", "both")
    
    # ============================================
    # 💾 数据存储配置
    # ============================================
    # 向量数据库配置
    # 向量存储提供商 (chroma, qdrant)
    VECTOR_STORE_PROVIDER = os.getenv("VECTOR_STORE_PROVIDER", "chroma")
    # ChromaDB持久化目录
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    # ChromaDB集合名称
    CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "chat_history")
    
    # Qdrant配置 (当VECTOR_STORE_PROVIDER=qdrant时使用)
    # Qdrant服务器地址
    QDRANT_HOST = os.getenv("QDRANT_HOST", "192.168.66.163")
    # Qdrant服务器端口
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    # Qdrant API密钥
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    # Qdrant集合名称
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", CHROMA_COLLECTION_NAME)
    
    # ============================================
    # 🚀 服务器配置
    # ============================================
    # 服务器监听配置
    # 服务器监听地址
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    # 服务器监听端口
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
    
    # ============================================
    # 💬 聊天引擎配置
    # ============================================
    # 聊天引擎类型: chat_engine, mem0_proxy
    CHAT_ENGINE = os.getenv("CHAT_ENGINE", "chat_engine")
    # 默认人格配置
    DEFAULT_PERSONALITY = os.getenv("DEFAULT_PERSONALITY", "health_assistant")
    # 是否默认启用流式响应
    STREAM_DEFAULT = os.getenv("STREAM_DEFAULT", "True").lower() == "true"
    # 是否默认启用工具调用
    USE_TOOLS_DEFAULT = os.getenv("USE_TOOLS_DEFAULT", "True").lower() == "true"
    
    # ============================================
    # 🎤 实时语音配置
    # ============================================
    # 实时语音功能开关
    REALTIME_VOICE_ENABLED = os.getenv("REALTIME_VOICE_ENABLED", "true").lower() == "true"
    # 实时语音模型
    REALTIME_VOICE_MODEL = os.getenv("REALTIME_VOICE_MODEL", "gpt-4o-realtime-preview-2024-12-17")
    # Token过期时间（秒）
    REALTIME_VOICE_TOKEN_EXPIRY = int(os.getenv("REALTIME_VOICE_TOKEN_EXPIRY", "3600"))
    # 音频采样率
    REALTIME_VOICE_SAMPLE_RATE = int(os.getenv("REALTIME_VOICE_SAMPLE_RATE", "24000"))
    # 音频声道数
    REALTIME_VOICE_CHANNELS = int(os.getenv("REALTIME_VOICE_CHANNELS", "1"))
    
    # ============================================
    # ⚡ 性能优化配置
    # ============================================
    # OpenAI API性能配置
    # OpenAI API总超时时间 (秒)
    OPENAI_API_TIMEOUT = float(os.getenv("OPENAI_API_TIMEOUT", "30.0"))
    # OpenAI连接超时时间 (秒)
    OPENAI_CONNECT_TIMEOUT = float(os.getenv("OPENAI_CONNECT_TIMEOUT", "10.0"))
    # OpenAI读取超时时间 (秒)
    OPENAI_READ_TIMEOUT = float(os.getenv("OPENAI_READ_TIMEOUT", "30.0"))
    # OpenAI写入超时时间 (秒)
    OPENAI_WRITE_TIMEOUT = float(os.getenv("OPENAI_WRITE_TIMEOUT", "10.0"))
    # OpenAI连接池超时时间 (秒)
    OPENAI_POOL_TIMEOUT = float(os.getenv("OPENAI_POOL_TIMEOUT", "30.0"))
    # OpenAI API重试次数
    OPENAI_API_RETRIES = int(os.getenv("OPENAI_API_RETRIES", "2"))
    
    # HTTP客户端配置
    # 最大连接数
    MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS", "100"))
    # 最大保持连接数
    MAX_KEEPALIVE_CONNECTIONS = int(os.getenv("MAX_KEEPALIVE_CONNECTIONS", "20"))
    # 连接保持时间 (秒)
    KEEPALIVE_EXPIRY = int(os.getenv("KEEPALIVE_EXPIRY", "30"))
    # 是否验证SSL证书
    VERIFY_SSL = os.getenv("VERIFY_SSL", "false").lower() == "true"
    
    # 流式响应配置
    # 流式响应分块阈值
    CHUNK_SPLIT_THRESHOLD = int(os.getenv("CHUNK_SPLIT_THRESHOLD", "100"))
    
    # ============================================
    # 📊 缓存配置
    # ============================================
    # Redis缓存配置
    # 是否启用Redis缓存
    USE_REDIS_CACHE = os.getenv("USE_REDIS_CACHE", "false").lower() == "true"
    # Redis服务器地址
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    # Redis服务器端口
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    # Redis数据库编号
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    # Redis密码
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    # Redis缓存TTL (秒)
    REDIS_TTL = int(os.getenv("REDIS_TTL", "1800"))
    
    # 内存缓存配置（作为Redis的降级方案）
    # 内存缓存最大条目数
    MEMORY_CACHE_MAXSIZE = int(os.getenv("MEMORY_CACHE_MAXSIZE", "1000"))
    # 内存缓存TTL (秒)
    MEMORY_CACHE_TTL = int(os.getenv("MEMORY_CACHE_TTL", "1800"))
    
    # ============================================
    # 📈 监控和日志配置
    # ============================================
    # 性能监控配置
    # 是否启用性能监控
    ENABLE_PERFORMANCE_MONITOR = os.getenv("ENABLE_PERFORMANCE_MONITOR", "true").lower() == "true"
    # 是否启用性能日志
    PERFORMANCE_LOG_ENABLED = os.getenv("PERFORMANCE_LOG_ENABLED", "true").lower() == "true"
    # 性能监控最大历史记录数
    PERFORMANCE_MAX_HISTORY = int(os.getenv("PERFORMANCE_MAX_HISTORY", "1000"))
    # 性能监控采样率 (1.0 = 100%采样)
    PERFORMANCE_SAMPLING_RATE = float(os.getenv("PERFORMANCE_SAMPLING_RATE", "1.0"))
    
    # 日志配置
    # 日志级别
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    # 日志文件名
    LOG_FILE_NAME = os.getenv("LOG_FILE_NAME", "app.log")
    
    # ============================================
    # 📋 API元数据配置
    # ============================================
    # API文档和版本信息
    # API标题
    API_TITLE = os.getenv("API_TITLE", "YYChat OpenAI兼容API")
    # API描述
    API_DESCRIPTION = os.getenv("API_DESCRIPTION", "YYChat是一个基于OpenAI API的聊天机器人，使用Mem0和ChromaDB进行记忆管理。")
    # API版本
    API_VERSION = os.getenv("API_VERSION", "0.1.1")
    
    # ============================================
    # 🎵 音频处理配置
    # ============================================
    # 音频文件大小限制 (MB)
    AUDIO_MAX_SIZE_MB = int(os.getenv("AUDIO_MAX_SIZE_MB", "25"))
    # 文本长度限制 (字符)
    TEXT_MAX_LENGTH = int(os.getenv("TEXT_MAX_LENGTH", "4096"))
    # 语速范围
    # 最小语速
    VOICE_SPEED_MIN = float(os.getenv("VOICE_SPEED_MIN", "0.25"))
    # 最大语速
    VOICE_SPEED_MAX = float(os.getenv("VOICE_SPEED_MAX", "4.0"))
    # 音频块大小 (KB)
    AUDIO_CHUNK_SIZE_KB = int(os.getenv("AUDIO_CHUNK_SIZE_KB", "32"))
    # 音频压缩质量 (1-100)
    AUDIO_COMPRESSION_QUALITY = int(os.getenv("AUDIO_COMPRESSION_QUALITY", "70"))
    
    # ============================================
    # 🎤 语音和模型默认配置
    # ============================================
    # 默认语音模型
    # 默认语音转文本模型
    DEFAULT_WHISPER_MODEL = os.getenv("DEFAULT_WHISPER_MODEL", "whisper-1")
    # 默认文本转语音模型
    DEFAULT_TTS_MODEL = os.getenv("DEFAULT_TTS_MODEL", "tts-1")
    # 默认语音
    DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "shimmer")
    # 默认聊天模型
    DEFAULT_CHAT_MODEL = os.getenv("DEFAULT_CHAT_MODEL", "gpt-4o-mini")
    
    # ============================================
    # ⏱️ 超时和重试配置
    # ============================================
    # 连接超时 (秒)
    CONNECTION_TIMEOUT = int(os.getenv("CONNECTION_TIMEOUT", "30"))
    # 重试次数
    MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    # 语音活动检测阈值
    VAD_SILENCE_THRESHOLD = int(os.getenv("VAD_SILENCE_THRESHOLD", "10"))
    # 音频缓冲区大小
    AUDIO_BUFFER_SIZE = int(os.getenv("AUDIO_BUFFER_SIZE", "100"))
    # 音频处理器超时 (秒)
    AUDIO_PROCESSOR_TIMEOUT = float(os.getenv("AUDIO_PROCESSOR_TIMEOUT", "30.0"))
    # 音频处理器最大工作线程数
    AUDIO_PROCESSOR_MAX_WORKERS = int(os.getenv("AUDIO_PROCESSOR_MAX_WORKERS", "4"))
    
    # ============================================
    # 🌐 WebSocket和网络配置
    # ============================================
    # WebSocket接收超时 (秒)
    WEBSOCKET_RECEIVE_TIMEOUT = float(os.getenv("WEBSOCKET_RECEIVE_TIMEOUT", "5.0"))
    # WebSocket连接超时 (秒)
    WEBSOCKET_CONNECT_TIMEOUT = float(os.getenv("WEBSOCKET_CONNECT_TIMEOUT", "10.0"))
    # WebSocket关闭超时 (秒)
    WEBSOCKET_CLOSE_TIMEOUT = float(os.getenv("WEBSOCKET_CLOSE_TIMEOUT", "5.0"))
    # WebSocket ping超时 (秒)
    WEBSOCKET_PING_TIMEOUT = float(os.getenv("WEBSOCKET_PING_TIMEOUT", "10.0"))
    # 最大重试次数
    MAX_CONNECTION_ATTEMPTS = int(os.getenv("MAX_CONNECTION_ATTEMPTS", "5"))
    
    # ============================================
    # 🎯 实时语音配置
    # ============================================
    # 实时语音连接超时 (秒)
    REALTIME_CONNECTION_TIMEOUT = int(os.getenv("REALTIME_CONNECTION_TIMEOUT", "30"))
    # 实时语音重连次数
    REALTIME_RECONNECT_ATTEMPTS = int(os.getenv("REALTIME_RECONNECT_ATTEMPTS", "3"))
    # 实时语音空闲超时 (毫秒)
    REALTIME_IDLE_TIMEOUT_MS = int(os.getenv("REALTIME_IDLE_TIMEOUT_MS", "30000"))
    # 实时语音阈值
    REALTIME_VOICE_THRESHOLD = float(os.getenv("REALTIME_VOICE_THRESHOLD", "0.2"))
    
    # ============================================
    # 📊 测试和调试配置
    # ============================================
    # 测试超时时间 (秒)
    TEST_TIMEOUT = int(os.getenv("TEST_TIMEOUT", "30"))
    # 测试重试次数
    TEST_MAX_ATTEMPTS = int(os.getenv("TEST_MAX_ATTEMPTS", "5"))
    # 调试模式
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    # 详细日志
    VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"
    
# 创建配置实例
def get_config():
    return Config()