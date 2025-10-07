"""
配置验证工具
用于验证和检查配置的正确性
"""
import os
from typing import Dict, List, Tuple
from config.config import get_config
from utils.log import log


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.config = get_config()
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> Tuple[bool, Dict]:
        """验证所有配置"""
        self.errors.clear()
        self.warnings.clear()
        
        # 验证必需的配置
        self._validate_required_configs()
        
        # 验证OpenAI配置
        self._validate_openai_config()
        
        # 验证Memory配置
        self._validate_memory_config()
        
        # 验证性能配置
        self._validate_performance_config()
        
        # 验证文件路径
        self._validate_paths()
        
        # 返回结果
        is_valid = len(self.errors) == 0
        return is_valid, {
            "valid": is_valid,
            "errors": self.errors,
            "warnings": self.warnings
        }
    
    def _validate_required_configs(self):
        """验证必需的配置项"""
        required = {
            "OPENAI_API_KEY": "OpenAI API密钥",
            "YYCHAT_API_KEY": "YYChat API密钥",
        }
        
        for key, name in required.items():
            value = getattr(self.config, key, None)
            if not value or value == "your-api-key-here" or value == "your-openai-api-key-here":
                self.errors.append(f"❌ {name} ({key}) 未配置或使用默认值")
    
    def _validate_openai_config(self):
        """验证OpenAI配置"""
        # 检查API Key格式
        api_key = self.config.OPENAI_API_KEY
        if api_key and not api_key.startswith(("sk-", "your-")):
            self.warnings.append(f"⚠️  OpenAI API Key格式可能不正确")
        
        # 检查模型名称
        model = self.config.OPENAI_MODEL
        known_models = ["gpt-4", "gpt-4-turbo", "gpt-4-turbo-preview", "gpt-3.5-turbo", "gpt-4.1"]
        if not any(model.startswith(m) for m in known_models):
            self.warnings.append(f"⚠️  OpenAI模型 '{model}' 可能不是标准模型名称")
        
        # 检查温度范围
        temp = self.config.OPENAI_TEMPERATURE
        if temp < 0 or temp > 2:
            self.errors.append(f"❌ OpenAI温度参数 {temp} 超出范围 [0, 2]")
        
        # 检查超时配置
        if self.config.OPENAI_API_TIMEOUT < 5:
            self.warnings.append(f"⚠️  OpenAI API超时设置过短 ({self.config.OPENAI_API_TIMEOUT}s)，可能导致请求失败")
    
    def _validate_memory_config(self):
        """验证Memory配置"""
        # 检查Memory模式
        if self.config.MEMO_USE_LOCAL:
            # 本地模式检查
            if not os.path.exists(self.config.CHROMA_PERSIST_DIRECTORY):
                self.warnings.append(f"⚠️  ChromaDB持久化目录不存在: {self.config.CHROMA_PERSIST_DIRECTORY}")
        else:
            # API模式检查
            if not self.config.MEM0_API_KEY or self.config.MEM0_API_KEY == "your-mem0-api-key-here":
                self.errors.append(f"❌ Memory API模式需要配置 MEM0_API_KEY")
        
        # 检查Memory检索超时
        timeout = self.config.MEMORY_RETRIEVAL_TIMEOUT
        if timeout > 2.0:
            self.warnings.append(f"⚠️  Memory检索超时设置过长 ({timeout}s)，建议设置为0.5-1.0秒")
        elif timeout < 0.1:
            self.warnings.append(f"⚠️  Memory检索超时设置过短 ({timeout}s)，可能导致检索失败")
        
        # 检查Memory检索限制
        if self.config.MEMORY_RETRIEVAL_LIMIT > 20:
            self.warnings.append(f"⚠️  Memory检索数量过多 ({self.config.MEMORY_RETRIEVAL_LIMIT})，可能影响性能")
    
    def _validate_performance_config(self):
        """验证性能配置"""
        # 检查连接池配置
        if self.config.MAX_CONNECTIONS < 10:
            self.warnings.append(f"⚠️  最大连接数设置过小 ({self.config.MAX_CONNECTIONS})，可能影响并发性能")
        
        if self.config.MAX_KEEPALIVE_CONNECTIONS > self.config.MAX_CONNECTIONS:
            self.errors.append(f"❌ Keep-Alive连接数 ({self.config.MAX_KEEPALIVE_CONNECTIONS}) 不能大于最大连接数 ({self.config.MAX_CONNECTIONS})")
        
        # 检查重试次数
        if self.config.OPENAI_API_RETRIES > 5:
            self.warnings.append(f"⚠️  API重试次数过多 ({self.config.OPENAI_API_RETRIES})，可能导致响应变慢")
    
    def _validate_paths(self):
        """验证文件路径"""
        # 检查personalities目录
        personalities_dir = "./personalities"
        if not os.path.exists(personalities_dir):
            self.warnings.append(f"⚠️  Personalities目录不存在: {personalities_dir}")
        
        # 检查日志目录
        log_dir = "./logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            self.warnings.append(f"⚠️  日志目录不存在，已自动创建: {log_dir}")
    
    def print_report(self):
        """打印验证报告"""
        print("\n" + "="*60)
        print("YYChat 配置验证报告")
        print("="*60 + "\n")
        
        if self.errors:
            print("❌ 错误 (必须修复):")
            for error in self.errors:
                print(f"   {error}")
            print()
        
        if self.warnings:
            print("⚠️  警告 (建议修复):")
            for warning in self.warnings:
                print(f"   {warning}")
            print()
        
        if not self.errors and not self.warnings:
            print("✅ 所有配置检查通过！")
            print()
        
        # 显示关键配置
        print("📊 关键配置:")
        print(f"   OpenAI模型: {self.config.OPENAI_MODEL}")
        print(f"   Memory模式: {'本地 (ChromaDB)' if self.config.MEMO_USE_LOCAL else 'API'}")
        print(f"   Memory检索超时: {self.config.MEMORY_RETRIEVAL_TIMEOUT}s")
        print(f"   Memory检索限制: {self.config.MEMORY_RETRIEVAL_LIMIT}条")
        print(f"   Memory检索开关: {'启用' if self.config.ENABLE_MEMORY_RETRIEVAL else '禁用'}")
        print(f"   默认引擎: {self.config.CHAT_ENGINE}")
        print(f"   服务地址: {self.config.SERVER_HOST}:{self.config.SERVER_PORT}")
        print()
        
        print("="*60 + "\n")
        
        return len(self.errors) == 0


def validate_config():
    """验证配置并返回结果"""
    validator = ConfigValidator()
    is_valid, result = validator.validate_all()
    return is_valid, result


if __name__ == "__main__":
    # 命令行运行时打印报告
    validator = ConfigValidator()
    validator.validate_all()
    is_valid = validator.print_report()
    
    if not is_valid:
        exit(1)

