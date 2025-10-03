#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mem0 Proxy使用示例

这个示例展示了如何使用项目中新增的Mem0ProxyManager类，
这是一种更接近Mem0官方示例的整合方式，性能更好。

使用场景：
- 对启动速度和响应时间要求较高的场景
- 希望更直接使用Mem0官方API的场景
- 需要快速集成记忆功能而不需要复杂处理的场景
"""

import asyncio
from typing import List, Dict
from core import get_mem0_proxy
from utils.log import log



async def simple_chat_demo():
    """简单聊天演示，展示Mem0 Proxy的基本用法"""
    print("=== Mem0 Proxy 简单聊天演示 ===")
    
    # 获取Mem0 Proxy管理器实例
    mem0_proxy = get_mem0_proxy()
    
    # 用户ID，用于区分不同用户的记忆
    user_id = "demo_user"
    
    try:
        # 第一次交互：存储用户偏好
        print("\n第一次交互 - 设置用户偏好：")
        messages1 = [
            {
                "role": "user",
                "content": "我喜欢印度菜，但不能吃奶酪。"
            }
        ]
        
        # 使用Mem0 Proxy生成响应
        response1 = await mem0_proxy.generate_response(
            messages=messages1,
            user_id=user_id,
            stream=False  # 非流式响应
        )
        
        # 输出响应内容
        if hasattr(response1, 'choices') and response1.choices:
            print(f"助手回复: {response1.choices[0].message.content}")
        else:
            print(f"助手回复: {response1}")
        
        # 等待一会儿，确保记忆已保存
        await asyncio.sleep(1)
        
        # 第二次交互：利用存储的记忆
        print("\n第二次交互 - 使用保存的记忆：")
        messages2 = [
            {
                "role": "user",
                "content": "推荐旧金山好吃的餐厅"
            }
        ]
        
        # 使用Mem0 Proxy生成响应
        response2 = await mem0_proxy.generate_response(
            messages=messages2,
            user_id=user_id,
            stream=False  # 非流式响应
        )
        
        # 输出响应内容
        if hasattr(response2, 'choices') and response2.choices:
            print(f"助手回复: {response2.choices[0].message.content}")
        else:
            print(f"助手回复: {response2}")
            
        print("\n演示完成！请注意观察第二次回复是否考虑了用户不能吃奶酪的偏好。")
            
    except Exception as e:
        log.error(f"演示过程中出错: {e}")
        print(f"演示过程中出错: {str(e)}")

async def streaming_chat_demo():
    """流式聊天演示，展示Mem0 Proxy的流式响应能力"""
    print("\n=== Mem0 Proxy 流式聊天演示 ===")
    
    # 获取Mem0 Proxy管理器实例
    mem0_proxy = get_mem0_proxy()
    
    # 用户ID，使用与上面不同的ID以展示独立的记忆
    user_id = "streaming_demo_user"
    
    try:
        # 设置用户偏好
        print("\n设置用户偏好：")
        messages1 = [
            {
                "role": "user",
                "content": "我是一名素食者，不食用任何肉类和海鲜。"
            }
        ]
        
        await mem0_proxy.generate_response(
            messages=messages1,
            user_id=user_id,
            stream=False
        )
        
        await asyncio.sleep(1)
        
        # 使用流式响应查询
        print("\n使用流式响应查询餐厅推荐：")
        messages2 = [
            {
                "role": "user",
                "content": "请推荐一些适合素食者的健康食谱"
            }
        ]
        
        # 流式响应
        stream_response = await mem0_proxy.generate_response(
            messages=messages2,
            user_id=user_id,
            stream=True  # 启用流式响应
        )
        
        # 处理流式响应
        print("助手回复: ", end="", flush=True)
        if hasattr(stream_response, '__aiter__'):
            # 异步迭代器模式
            async for chunk in stream_response:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        print(delta.content, end="", flush=True)
        else:
            # 非异步迭代器模式（可能是降级后的响应）
            print(stream_response)
        
        print("\n\n流式演示完成！")
            
    except Exception as e:
        log.error(f"流式演示过程中出错: {e}")
        print(f"流式演示过程中出错: {str(e)}")

async def compare_performance_demo():
    """性能对比演示，简单比较两种实现方式的响应时间"""
    print("\n=== 性能对比演示 ===")
    print("注意：这只是一个简单的性能测试，实际性能可能因环境而异")
    
    from core import ChatEngine
    import time
    
    # 初始化两种实现
    mem0_proxy = get_mem0_proxy()
    chat_engine = ChatEngine()
    
    # 测试消息
    messages = [
        {"role": "user", "content": "什么是人工智能？简单解释一下。"}
    ]
    user_id = "performance_test_user"
    
    try:
        # 测试Mem0 Proxy
        print("\n测试Mem0 Proxy响应时间：")
        start_time = time.time()
        await mem0_proxy.generate_response(messages=messages, user_id=user_id, stream=False)
        proxy_time = time.time() - start_time
        print(f"Mem0 Proxy响应时间: {proxy_time:.3f}秒")
        
        # 测试ChatEngine
        print("\n测试ChatEngine响应时间：")
        start_time = time.time()
        await chat_engine.generate_response(messages=messages, conversation_id=user_id, stream=False)
        engine_time = time.time() - start_time
        print(f"ChatEngine响应时间: {engine_time:.3f}秒")
        
        # 计算差异
        diff = engine_time - proxy_time
        percentage = (diff / proxy_time) * 100 if proxy_time > 0 else 0
        print(f"\n性能差异: ChatEngine比Mem0 Proxy慢{diff:.3f}秒 ({percentage:.1f}%)")
        print("\n注意：实际差异可能因网络条件、系统负载和记忆库大小而异")
        
    except Exception as e:
        log.error(f"性能测试过程中出错: {e}")
        print(f"性能测试过程中出错: {str(e)}")

async def main():
    """运行所有演示"""
    try:
        # 运行简单聊天演示
        await simple_chat_demo()
        
        # 运行流式聊天演示
        await streaming_chat_demo()
        
        # 运行性能对比演示
        await compare_performance_demo()
        
    except KeyboardInterrupt:
        print("\n演示被用户中断")
    finally:
        print("\n所有演示已完成")

if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())