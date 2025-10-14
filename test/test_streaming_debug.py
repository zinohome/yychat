#!/usr/bin/env python3
"""
流式响应调试测试
用于诊断流式响应卡住的问题
"""

import asyncio
import json
import websockets
import time
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class StreamingDebugTest:
    def __init__(self):
        self.websocket = None
        self.client_id = None
        
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.websocket = await websockets.connect("ws://localhost:8000/ws/chat")
            print("✅ 已连接到WebSocket服务器")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    async def send_message(self, message):
        """发送消息"""
        try:
            await self.websocket.send(json.dumps(message))
            print(f"📤 已发送消息: {message.get('type', 'unknown')}")
        except Exception as e:
            print(f"❌ 发送消息失败: {e}")
    
    async def receive_messages(self, timeout=30):
        """接收消息，带超时"""
        try:
            print(f"📥 开始接收消息，超时时间: {timeout}秒")
            start_time = time.time()
            
            while True:
                try:
                    # 设置接收超时
                    message = await asyncio.wait_for(
                        self.websocket.recv(), 
                        timeout=5.0  # 5秒超时
                    )
                    
                    elapsed = time.time() - start_time
                    data = json.loads(message)
                    msg_type = data.get("type", "unknown")
                    
                    print(f"📥 [{elapsed:.1f}s] 收到消息: {msg_type}")
                    
                    if msg_type == "connection_established":
                        self.client_id = data.get("client_id")
                        print(f"🆔 客户端ID: {self.client_id}")
                    
                    elif msg_type == "stream_start":
                        print("🚀 流式响应开始")
                    
                    elif msg_type == "stream_chunk":
                        content = data.get("content", "")
                        print(f"📝 内容块: {content[:50]}{'...' if len(content) > 50 else ''}")
                    
                    elif msg_type == "stream_end":
                        full_content = data.get("full_content", "")
                        print(f"🏁 流式响应结束，总长度: {len(full_content)}")
                        break
                    
                    elif msg_type == "error":
                        error_msg = data.get("message", "未知错误")
                        print(f"❌ 错误: {error_msg}")
                        break
                    
                    # 检查总超时
                    if time.time() - start_time > timeout:
                        print(f"⏰ 总超时 ({timeout}秒)，停止接收")
                        break
                        
                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    print(f"⏰ 接收超时 (5秒)，已等待 {elapsed:.1f}秒")
                    if elapsed > timeout:
                        print(f"⏰ 总超时 ({timeout}秒)，停止接收")
                        break
                    continue
                    
        except Exception as e:
            print(f"❌ 接收消息失败: {e}")
    
    async def test_simple_text_message(self):
        """测试简单的文本消息"""
        print("\n🧪 测试简单文本消息...")
        
        message = {
            "type": "text_message",
            "content": "你好，请简单回复一下",
            "conversation_id": "test_conversation",
            "personality_id": "friendly",
            "use_tools": False,
            "stream": True,
            "timestamp": time.time()
        }
        
        await self.send_message(message)
        await self.receive_messages(timeout=20)
    
    async def test_short_message(self):
        """测试很短的文本消息"""
        print("\n🧪 测试短文本消息...")
        
        message = {
            "type": "text_message",
            "content": "Hi",
            "conversation_id": "test_conversation",
            "personality_id": "friendly",
            "use_tools": False,
            "stream": True,
            "timestamp": time.time()
        }
        
        await self.send_message(message)
        await self.receive_messages(timeout=15)
    
    async def test_non_streaming(self):
        """测试非流式响应"""
        print("\n🧪 测试非流式响应...")
        
        message = {
            "type": "text_message",
            "content": "简单回复",
            "conversation_id": "test_conversation",
            "personality_id": "friendly",
            "use_tools": False,
            "stream": False,
            "timestamp": time.time()
        }
        
        await self.send_message(message)
        await self.receive_messages(timeout=15)
    
    async def run_tests(self):
        """运行所有测试"""
        print("🚀 开始流式响应调试测试")
        print("=" * 50)
        
        if not await self.connect():
            return
        
        try:
            # 等待连接确认
            await self.receive_messages(timeout=5)
            
            # 运行测试
            await self.test_short_message()
            await asyncio.sleep(2)
            
            await self.test_non_streaming()
            await asyncio.sleep(2)
            
            await self.test_simple_text_message()
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
        finally:
            if self.websocket:
                await self.websocket.close()
                print("🔌 连接已关闭")

async def main():
    test = StreamingDebugTest()
    await test.run_tests()

if __name__ == "__main__":
    asyncio.run(main())
