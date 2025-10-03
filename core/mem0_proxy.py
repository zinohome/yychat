import time
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI
from mem0.proxy.main import Mem0
from config.config import get_config
from config.log_config import get_logger

logger = get_logger(__name__)
config = get_config()

class Mem0ProxyManager:
    """
    基于Mem0官方Proxy接口的轻量级记忆管理器
    特点：更接近官方示例的实现方式，性能更好，但功能相对简单
    """
    def __init__(self):
        # 初始化Mem0客户端
        self._init_mem0_client()
        # 缓存已初始化的客户端，避免重复创建
        self.clients_cache = {}
        
    def _init_mem0_client(self):
        """初始化基础Mem0客户端"""
        try:
            # 本地配置初始化函数，避免代码重复
            def init_local_config():        
                mem_config = {
                    "vector_store": {
                        "provider": "chroma",
                        "config": {
                            "collection_name": config.CHROMA_COLLECTION_NAME,
                            "path": config.CHROMA_PERSIST_DIRECTORY
                        }
                    },
                    "llm": {
                        "provider": config.MEM0_LLM_PROVIDER,
                        "config": {
                            "model": config.MEM0_LLM_CONFIG_MODEL,
                            "max_tokens": config.MEM0_LLM_CONFIG_MAX_TOKENS
                        }
                    }
                }
                self.base_client = Mem0(config=mem_config)
                return "本地配置"

            # 判断逻辑简化：
            # 1. 如果MEMO_USE_LOCAL为True，强制使用本地配置
            # 2. 否则，如果有API密钥，使用API密钥方式
            # 3. 否则，使用本地配置作为后备方案
            if config.MEMO_USE_LOCAL:
                config_type = init_local_config()
                logger.info(f"强制使用{config_type}初始化Mem0客户端")
            elif config.MEM0_API_KEY:
                self.base_client = Mem0(api_key=config.MEM0_API_KEY)
                logger.info("使用Mem0 API密钥初始化客户端")
            else:
                config_type = init_local_config()
                logger.info(f"使用{config_type}初始化Mem0客户端")
        except Exception as e:
            logger.error(f"初始化Mem0客户端失败: {e}")
            # 创建一个模拟客户端用于降级处理
            self.base_client = self._create_mock_client()
    
    def _create_mock_client(self):
        """创建一个模拟客户端用于降级处理"""
        class MockMem0Client:
            def chat(self):
                class MockChat:
                    def completions(self):
                        class MockCompletions:
                            def create(self, **kwargs):
                                # 直接调用OpenAI API作为降级方案
                                client = OpenAI(
                                    api_key=config.OPENAI_API_KEY,
                                    base_url=config.OPENAI_BASE_URL
                                )
                                return client.chat.completions.create(**kwargs)
                        return MockCompletions()
                return MockChat()
        return MockMem0Client()
    
    def get_client(self, user_id: str = "default"):
        """获取或创建特定用户的Mem0客户端"""
        if user_id not in self.clients_cache:
            # 注意：这里可以根据需要为不同用户创建不同配置的客户端
            # 目前简单实现为所有用户共享同一个基础客户端
            self.clients_cache[user_id] = self.base_client
        return self.clients_cache[user_id]
    
    async def generate_response(self, messages: List[Dict[str, str]], user_id: str = "default",
                               model: Optional[str] = None, stream: Optional[bool] = None,
                               temperature: Optional[float] = None) -> Any:
        """
        使用Mem0 Proxy接口生成响应
        这个方法更接近官方示例，性能更好，但功能相对简单
        """
        start_time = time.time()
        try:
            # 使用默认值
            if model is None:
                model = config.OPENAI_MODEL
            if stream is None:
                stream = config.STREAM_DEFAULT
            if temperature is None:
                temperature = float(config.OPENAI_TEMPERATURE)
            
            # 获取客户端
            client = self.get_client(user_id)
            
            # 调用Mem0的chat.completions.create方法
            # 这是与官方示例最接近的调用方式，性能更好
            response = client.chat.completions.create(
                messages=messages,
                model=model,
                user_id=user_id,
                stream=stream,
                temperature=temperature,
                # 可以添加Mem0特有的参数
                limit=config.MEMORY_RETRIEVAL_LIMIT
            )
            
            logger.debug(f"Mem0代理响应生成耗时: {time.time() - start_time:.3f}秒")
            return response
        except Exception as e:
            logger.error(f"使用Mem0代理生成响应失败: {e}")
            # 降级到直接调用OpenAI API
            try:
                openai_client = OpenAI(
                    api_key=config.OPENAI_API_KEY,
                    base_url=config.OPENAI_BASE_URL
                )
                response = openai_client.chat.completions.create(
                    messages=messages,
                    model=model or config.OPENAI_MODEL,
                    stream=stream or config.STREAM_DEFAULT,
                    temperature=temperature or float(config.OPENAI_TEMPERATURE)
                )
                return response
            except Exception as fallback_error:
                logger.error(f"降级到OpenAI API也失败: {fallback_error}")
                # 返回错误响应
                if stream:
                    # 对于流式响应，返回一个异步生成器
                    async def error_generator():
                        yield {"role": "assistant", "content": f"发生错误: {str(fallback_error)}"}
                    return error_generator()
                else:
                    return {"choices": [{"message": {"content": f"发生错误: {str(fallback_error)}"}}]}

# 创建全局实例
def get_mem0_proxy():
    """获取全局的Mem0ProxyManager实例"""
    global _mem0_proxy
    try:
        return _mem0_proxy
    except NameError:
        _mem0_proxy = Mem0ProxyManager()
        return _mem0_proxy

# 性能比较说明
"""
项目当前实现 vs Mem0官方Proxy实现的性能比较：

1. 项目当前实现（ChatEngine + ChatMemory）：
   - 优点：功能更丰富，错误处理更完善，与系统集成更紧密
   - 缺点：处理链更长，可能导致额外的几秒钟延迟
   - 主要耗时点：记忆检索、token估算、消息预处理、格式转换等

2. 本文件中的Mem0 Proxy实现：
   - 优点：更接近官方示例，性能更好，启动速度更快
   - 缺点：功能相对简单，与项目其他组件（如人格系统）集成度较低
   - 优化点：减少了中间处理步骤，直接使用Mem0的代理接口

选择建议：
- 如果更看重性能和启动速度，可以考虑使用本文件中的实现
- 如果需要更丰富的功能和更好的系统集成，建议保持当前实现
- 也可以考虑混合使用：对于新会话使用Proxy实现快速启动，后续交互使用完整实现
"""