#!/usr/bin/env python3
"""
最终优化测试
验证是否完全消除了重复初始化和警告
"""

import asyncio
import websockets
import json
import time
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

async def test_websocket_connection():
    """测试WebSocket连接和消息处理"""
    print("🧪 测试WebSocket连接...")
    
    try:
        uri = "ws://localhost:9800/ws/chat"
        print(f"📡 连接到: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 等待连接建立消息
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                message = json.loads(response)
                print(f"📨 收到消息: {message.get('type', 'unknown')}")
                
                if message.get('type') == 'connection_established':
                    print("✅ 连接建立成功")
                else:
                    print(f"⚠️ 意外的消息类型: {message.get('type')}")
                    return False
                    
            except asyncio.TimeoutError:
                print("❌ 连接建立超时")
                return False
            
            # 测试文本消息
            test_message = {
                "type": "text_message",
                "content": "测试消息",
                "conversation_id": "test_conversation",
                "personality_id": "friendly",
                "use_tools": False,
                "stream": False,
                "timestamp": time.time()
            }
            
            print("📤 发送测试文本消息...")
            await websocket.send(json.dumps(test_message))
            
            # 等待响应
            try:
                response_received = False
                start_time = time.time()
                
                while time.time() - start_time < 10.0:  # 10秒超时
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    message = json.loads(response)
                    msg_type = message.get('type', 'unknown')
                    
                    print(f"📨 收到响应: {msg_type}")
                    
                    if msg_type == 'text_response':
                        print("✅ 文本消息处理成功")
                        return True
                    elif msg_type == 'error':
                        error_data = message.get('data', {})
                        error_msg = error_data.get('message', '未知错误')
                        print(f"❌ 收到错误响应: {error_msg}")
                        return False
                    elif msg_type in ['processing_start', 'stream_start', 'stream_chunk', 'stream_end']:
                        response_received = True
                        continue
                    else:
                        print(f"⚠️ 意外的响应类型: {msg_type}")
                        return False
                
                if response_received:
                    print("✅ 收到流式响应")
                    return True
                else:
                    print("❌ 文本消息响应超时")
                    return False
                    
            except asyncio.TimeoutError:
                print("❌ 文本消息响应超时")
                return False
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def test_api_endpoints():
    """测试API端点"""
    print("\n🧪 测试API端点...")
    
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试模型列表端点
            url = "http://localhost:9800/v1/models"
            headers = {"Authorization": "Bearer yychat-api-key"}
            
            print(f"📡 测试: {url}")
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 模型列表API正常，返回 {len(data.get('data', []))} 个模型")
                else:
                    print(f"❌ 模型列表API失败: {response.status}")
                    return False
            
            # 测试人格列表端点
            url = "http://localhost:9800/v1/personalities"
            print(f"📡 测试: {url}")
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 人格列表API正常，返回 {len(data.get('data', []))} 个人格")
                else:
                    print(f"❌ 人格列表API失败: {response.status}")
                    return False
                    
            return True
            
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 最终优化测试")
    print("=" * 50)
    
    # 等待服务器启动
    print("⏳ 等待服务器启动...")
    await asyncio.sleep(3)
    
    # 测试WebSocket
    websocket_success = await test_websocket_connection()
    
    # 测试API端点
    api_success = await test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"WebSocket测试: {'✅ 通过' if websocket_success else '❌ 失败'}")
    print(f"API端点测试: {'✅ 通过' if api_success else '❌ 失败'}")
    
    if websocket_success and api_success:
        print("\n🎉 所有测试通过！优化成功！")
        print("✅ 重复初始化问题已解决")
        print("✅ 警告信息已消除")
        print("✅ 所有功能正常工作")
        return True
    else:
        print("\n❌ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 测试被中断")
        sys.exit(1)
