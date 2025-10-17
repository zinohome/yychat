"""
警告抑制和优化配置
用于减少开发环境中的警告信息
"""

import warnings
import logging

def suppress_deprecation_warnings():
    """抑制已知的第三方库警告"""
    
    # 抑制 pydub 相关的正则表达式警告
    warnings.filterwarnings(
        "ignore", 
        category=DeprecationWarning, 
        module="pydub.utils"
    )
    
    # 抑制 audioop 模块警告
    warnings.filterwarnings(
        "ignore", 
        category=DeprecationWarning, 
        message=".*audioop.*"
    )
    
    # 抑制 websockets 相关警告（包括 legacy 和 WebSocketServerProtocol）
    warnings.filterwarnings(
        "ignore", 
        category=DeprecationWarning, 
        module="websockets"
    )
    warnings.filterwarnings(
        "ignore", 
        category=DeprecationWarning, 
        message=".*websockets.*"
    )
    warnings.filterwarnings(
        "ignore", 
        category=DeprecationWarning, 
        message=".*WebSocketServerProtocol.*"
    )
    warnings.filterwarnings(
        "ignore", 
        category=DeprecationWarning, 
        message=".*websockets.legacy.*"
    )
    
    # 抑制 webrtcvad 相关警告
    warnings.filterwarnings(
        "ignore", 
        category=DeprecationWarning, 
        module="webrtcvad"
    )
    
    # 抑制 pkg_resources 相关警告
    warnings.filterwarnings(
        "ignore", 
        category=DeprecationWarning, 
        message=".*pkg_resources.*"
    )
    
    # 抑制 setuptools 相关警告
    warnings.filterwarnings(
        "ignore", 
        category=DeprecationWarning, 
        message=".*setuptools.*"
    )

def configure_logging_level():
    """配置日志级别以减少冗余信息"""
    
    # 设置第三方库的日志级别
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("pydub").setLevel(logging.WARNING)
    logging.getLogger("webrtcvad").setLevel(logging.WARNING)
    
    # 设置 asyncio 日志级别
    logging.getLogger("asyncio").setLevel(logging.WARNING)

def suppress_all_known_warnings():
    """抑制所有已知的警告类型"""
    
    # 抑制所有 DeprecationWarning
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    # 抑制所有 FutureWarning
    warnings.filterwarnings("ignore", category=FutureWarning)
    
    # 抑制所有 PendingDeprecationWarning
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
    
    # 抑制所有 UserWarning（可选，根据需要启用）
    # warnings.filterwarnings("ignore", category=UserWarning)

def optimize_imports():
    """优化导入以减少警告"""
    
    # 在应用启动时调用
    suppress_deprecation_warnings()
    configure_logging_level()
    
    # 如果需要完全静默，可以启用下面这行
    # suppress_all_known_warnings()
    
    print("✅ 警告抑制配置已应用")
