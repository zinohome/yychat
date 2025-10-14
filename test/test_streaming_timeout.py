#!/usr/bin/env python3
"""
流式响应超时测试
用于诊断流式响应卡住的问题
"""

import asyncio
import sys
import os
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

async def test_openai_streaming():
    """测试OpenAI流式响应"""
    print("🧪 测试OpenAI流式响应...")
    
    try:
        from core.chat_engine import ChatEngine
        from core.engine_manager import get_engine_manager
        from config.config import get_config
        
        # 获取配置
        config = get_config()
        
        # 获取引擎管理器并初始化引擎
        engine_manager = get_engine_manager()
        
        # 根据配置初始化引擎
        if config.CHAT_ENGINE == "mem0_proxy":
            from core.mem0_proxy import get_mem0_proxy
            mem0_engine = get_mem0_proxy()
            engine_manager.register_engine("mem0_proxy", mem0_engine)
            engine_manager.current_engine_name = "mem0_proxy"
            chat_engine = mem0_engine
        else:
            chat_engine_instance = ChatEngine()
            engine_manager.register_engine("chat_engine", chat_engine_instance)
            engine_manager.current_engine_name = "chat_engine"
            chat_engine = chat_engine_instance
        
        # 再次获取聊天引擎
        chat_engine = engine_manager.get_current_engine()
        
        if not chat_engine:
            print("❌ 聊天引擎未初始化")
            return
        
        print("✅ 聊天引擎已获取")
        
        # 构建测试请求
        request_params = {
            "model": "gpt-4.1",
            "messages": [
                {"role": "user", "content": "你好，请简单回复"}
            ],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        print("📤 开始流式请求...")
        start_time = time.time()
        
        # 设置超时
        try:
            async with asyncio.timeout(30):  # 30秒超时
                chunk_count = 0
                async for chunk in chat_engine.client.create_chat_stream(request_params):
                    chunk_count += 1
                    elapsed = time.time() - start_time
                    print(f"📥 [{elapsed:.1f}s] 收到chunk #{chunk_count}")
                    
                    if chunk.choices and len(chunk.choices) > 0:
                        choice = chunk.choices[0]
                        if hasattr(choice.delta, 'content') and choice.delta.content:
                            print(f"📝 内容: {choice.delta.content}")
                    
                    # 限制测试长度
                    if chunk_count > 10:
                        print("🛑 测试完成，收到10个chunk")
                        break
                
                print(f"✅ 流式响应完成，总耗时: {time.time() - start_time:.2f}秒")
                
        except asyncio.TimeoutError:
            print(f"⏰ 流式响应超时 ({time.time() - start_time:.2f}秒)")
        except Exception as e:
            print(f"❌ 流式响应错误: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_simple_streaming():
    """测试简单的流式响应"""
    print("\n🧪 测试简单流式响应...")
    
    try:
        from core.chat_engine import ChatEngine
        from core.engine_manager import get_engine_manager
        from config.config import get_config
        
        # 获取配置
        config = get_config()
        
        # 获取引擎管理器并初始化引擎
        engine_manager = get_engine_manager()
        
        # 根据配置初始化引擎
        if config.CHAT_ENGINE == "mem0_proxy":
            from core.mem0_proxy import get_mem0_proxy
            mem0_engine = get_mem0_proxy()
            engine_manager.register_engine("mem0_proxy", mem0_engine)
            engine_manager.current_engine_name = "mem0_proxy"
            chat_engine = mem0_engine
        else:
            chat_engine_instance = ChatEngine()
            engine_manager.register_engine("chat_engine", chat_engine_instance)
            engine_manager.current_engine_name = "chat_engine"
            chat_engine = chat_engine_instance
        
        # 再次获取聊天引擎
        chat_engine = engine_manager.get_current_engine()
        
        if not chat_engine:
            print("❌ 聊天引擎未初始化")
            return
        
        # 构建测试请求
        request_params = {
            "model": "gpt-4.1",
            "messages": [
                {"role": "user", "content": "Hi"}
            ],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 50
        }
        
        print("📤 开始简单流式请求...")
        start_time = time.time()
        
        # 设置超时
        try:
            async with asyncio.timeout(20):  # 20秒超时
                chunk_count = 0
                async for chunk in chat_engine.client.create_chat_stream(request_params):
                    chunk_count += 1
                    elapsed = time.time() - start_time
                    print(f"📥 [{elapsed:.1f}s] 收到chunk #{chunk_count}")
                    
                    if chunk.choices and len(chunk.choices) > 0:
                        choice = chunk.choices[0]
                        if hasattr(choice.delta, 'content') and choice.delta.content:
                            print(f"📝 内容: {choice.delta.content}")
                
                print(f"✅ 简单流式响应完成，总耗时: {time.time() - start_time:.2f}秒")
                
        except asyncio.TimeoutError:
            print(f"⏰ 简单流式响应超时 ({time.time() - start_time:.2f}秒)")
        except Exception as e:
            print(f"❌ 简单流式响应错误: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ 简单测试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主测试函数"""
    print("🚀 开始流式响应超时测试")
    print("=" * 50)
    
    await test_simple_streaming()
    await asyncio.sleep(2)
    await test_openai_streaming()
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")

if __name__ == "__main__":
    asyncio.run(main())
