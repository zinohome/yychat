#!/usr/bin/env python3
"""
测试SSE流式响应是否正常
验证前端是否能正确接收到流式文本
"""

import asyncio
import aiohttp
import json
import time

async def test_sse_streaming():
    """测试SSE流式响应"""
    url = 'http://localhost:9800/v1/chat/completions'
    headers = {
        'Authorization': 'Bearer yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': 'gpt-4.1',
        'messages': [
            {'role': 'user', 'content': '请简单介绍一下北京的天气'}
        ],
        'stream': True,
        'use_tools': True,
        'personality_id': 'health_assistant',
        'conversation_id': 'test-sse-streaming',
        'enable_voice': False,  # 先测试不启用语音
        'message_id': 'test-message-1',
        'client_id': 'test-client-1'
    }
    
    print("开始测试SSE流式响应...")
    print(f"请求URL: {url}")
    print(f"请求载荷: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                print(f"响应状态码: {response.status}")
                
                if response.status != 200:
                    print(f"请求失败: {response.status}")
                    text = await response.text()
                    print(f"错误内容: {text}")
                    return
                
                print("\n开始接收SSE流式响应:")
                print("-" * 50)
                
                chunk_count = 0
                content_parts = []
                
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 移除 'data: ' 前缀
                        
                        if data_str == '[DONE]':
                            print("\n" + "=" * 50)
                            print("SSE流式响应结束")
                            break
                        
                        try:
                            data = json.loads(data_str)
                            chunk_count += 1
                            
                            # 检查是否是元事件
                            if data.get('type') == 'stream_start':
                                print(f"[元事件] stream_start: {data}")
                            elif data.get('type') == 'stream_end':
                                print(f"[元事件] stream_end: {data}")
                            else:
                                # 检查是否是标准SSE格式
                                if 'choices' in data and len(data['choices']) > 0:
                                    choice = data['choices'][0]
                                    if 'delta' in choice and 'content' in choice['delta']:
                                        content = choice['delta']['content']
                                        if content:
                                            content_parts.append(content)
                                            print(f"[chunk {chunk_count}] {content}", end='', flush=True)
                                    
                                    # 检查是否有finish_reason
                                    if 'finish_reason' in choice and choice['finish_reason']:
                                        print(f"\n[完成] finish_reason: {choice['finish_reason']}")
                                else:
                                    print(f"[其他数据] {data}")
                        
                        except json.JSONDecodeError as e:
                            print(f"[JSON解析错误] {line_str}: {e}")
                        except Exception as e:
                            print(f"[处理错误] {line_str}: {e}")
                
                print(f"\n总共接收到 {chunk_count} 个chunk")
                full_content = ''.join(content_parts)
                print(f"完整内容长度: {len(full_content)} 字符")
                print(f"完整内容预览: {full_content[:100]}...")
                
    except Exception as e:
        print(f"测试失败: {e}")

async def test_sse_with_voice():
    """测试启用语音的SSE流式响应"""
    url = 'http://localhost:9800/v1/chat/completions'
    headers = {
        'Authorization': 'Bearer yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': 'gpt-4.1',
        'messages': [
            {'role': 'user', 'content': '请简单介绍一下北京的天气'}
        ],
        'stream': True,
        'use_tools': True,
        'personality_id': 'health_assistant',
        'conversation_id': 'test-sse-voice',
        'enable_voice': True,  # 启用语音
        'message_id': 'test-message-2',
        'client_id': 'test-client-2'
    }
    
    print("\n" + "=" * 60)
    print("开始测试启用语音的SSE流式响应...")
    print(f"请求载荷: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                print(f"响应状态码: {response.status}")
                
                if response.status != 200:
                    print(f"请求失败: {response.status}")
                    text = await response.text()
                    print(f"错误内容: {text}")
                    return
                
                print("\n开始接收SSE流式响应:")
                print("-" * 50)
                
                chunk_count = 0
                content_parts = []
                
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        
                        if data_str == '[DONE]':
                            print("\n" + "=" * 50)
                            print("SSE流式响应结束")
                            break
                        
                        try:
                            data = json.loads(data_str)
                            chunk_count += 1
                            
                            # 检查是否是元事件
                            if data.get('type') == 'stream_start':
                                print(f"[元事件] stream_start: {data}")
                            elif data.get('type') == 'stream_end':
                                print(f"[元事件] stream_end: {data}")
                            else:
                                # 检查是否是标准SSE格式
                                if 'choices' in data and len(data['choices']) > 0:
                                    choice = data['choices'][0]
                                    if 'delta' in choice and 'content' in choice['delta']:
                                        content = choice['delta']['content']
                                        if content:
                                            content_parts.append(content)
                                            print(f"[chunk {chunk_count}] {content}", end='', flush=True)
                                    
                                    # 检查是否有finish_reason
                                    if 'finish_reason' in choice and choice['finish_reason']:
                                        print(f"\n[完成] finish_reason: {choice['finish_reason']}")
                                else:
                                    print(f"[其他数据] {data}")
                        
                        except json.JSONDecodeError as e:
                            print(f"[JSON解析错误] {line_str}: {e}")
                        except Exception as e:
                            print(f"[处理错误] {line_str}: {e}")
                
                print(f"\n总共接收到 {chunk_count} 个chunk")
                full_content = ''.join(content_parts)
                print(f"完整内容长度: {len(full_content)} 字符")
                print(f"完整内容预览: {full_content[:100]}...")
                
    except Exception as e:
        print(f"测试失败: {e}")

async def main():
    """运行所有测试"""
    print("SSE流式响应测试")
    print("=" * 60)
    
    # 测试1: 不启用语音的SSE
    await test_sse_streaming()
    
    # 等待一下
    await asyncio.sleep(2)
    
    # 测试2: 启用语音的SSE
    await test_sse_with_voice()

if __name__ == "__main__":
    asyncio.run(main())
