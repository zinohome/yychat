"""环境验证测试"""

def test_environment():
    """验证测试环境正常"""
    assert True

def test_imports():
    """验证关键模块可导入"""
    from core.chat_engine import chat_engine
    assert chat_engine is not None
