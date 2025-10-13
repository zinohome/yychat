"""
WebSocket功能测试脚本
用于测试阶段1实现的WebSocket基础功能
"""

import asyncio
import json
import websockets
import time
from typing import Dict, Any


class WebSocketTestClient:
    """WebSocket测试客户端"""
    
    def __init__(self, uri: str = "ws://localhost:9800/ws/chat"):
        self.uri = uri
        self.websocket = None
        self.client_id = None
    
    async def connect(self) -> bool:
        """连接到WebSocket服务器"""
        try:
            self.websocket = await websockets.connect(self.uri)
            print(f"✅ 已连接到WebSocket服务器: {self.uri}")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开WebSocket连接"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 WebSocket连接已断开")
    
    async def send_message(self, message: Dict[str, Any]):
        """发送消息"""
        if not self.websocket:
            print("❌ WebSocket未连接")
            return
        
        try:
            message_str = json.dumps(message)
            await self.websocket.send(message_str)
            print(f"📤 已发送消息: {message.get('type', 'unknown')}")
        except Exception as e:
            print(f"❌ 发送消息失败: {e}")
    
    async def receive_message(self) -> Dict[str, Any]:
        """接收消息"""
        if not self.websocket:
            print("❌ WebSocket未连接")
            return {}
        
        try:
            message_str = await self.websocket.recv()
            message = json.loads(message_str)
            print(f"📥 收到消息: {message.get('type', 'unknown')}")
            return message
        except Exception as e:
            print(f"❌ 接收消息失败: {e}")
            return {}
    
    async def test_heartbeat(self):
        """测试心跳功能"""
        print("\n🔄 测试心跳功能...")
        
        # 发送心跳
        await self.send_message({
            "type": "heartbeat",
            "timestamp": time.time()
        })
        
        # 接收消息直到找到心跳响应
        max_attempts = 5
        for _ in range(max_attempts):
            response = await self.receive_message()
            if response.get("type") == "heartbeat_response":
                print("✅ 心跳测试通过")
                return
            elif response.get("type") == "connection_established":
                print("📡 收到连接确认消息")
                continue
        
        print("❌ 心跳测试失败")
    
    async def test_ping(self):
        """测试ping功能"""
        print("\n🏓 测试ping功能...")
        
        # 发送ping
        await self.send_message({
            "type": "ping",
            "timestamp": time.time()
        })
        
        # 接收消息直到找到pong响应
        max_attempts = 5
        for _ in range(max_attempts):
            response = await self.receive_message()
            if response.get("type") == "pong":
                print("✅ ping测试通过")
                return
            elif response.get("type") == "connection_established":
                print("📡 收到连接确认消息")
                continue
        
        print("❌ ping测试失败")
    
    async def test_status(self):
        """测试状态查询功能"""
        print("\n📊 测试状态查询功能...")
        
        # 发送状态查询
        await self.send_message({
            "type": "get_status",
            "timestamp": time.time()
        })
        
        # 接收消息直到找到状态响应
        max_attempts = 5
        for _ in range(max_attempts):
            response = await self.receive_message()
            if response.get("type") == "status_response":
                data = response.get("data", {})
                print(f"✅ 状态查询测试通过 - 连接数: {data.get('total_connections', 0)}")
                return
            elif response.get("type") == "connection_established":
                print("📡 收到连接确认消息")
                continue
        
        print("❌ 状态查询测试失败")
    
    async def test_text_message(self):
        """测试文本消息功能"""
        print("\n💬 测试文本消息功能...")
        
        # 发送文本消息
        await self.send_message({
            "type": "text_message",
            "content": "Hello, this is a test message!",
            "conversation_id": "test_conversation",
            "stream": True,
            "timestamp": time.time()
        })
        
        # 接收处理开始消息
        response = await self.receive_message()
        if response.get("type") == "processing_start":
            print("✅ 文本消息处理开始")
        else:
            print("❌ 文本消息处理开始失败")
            return
        
        # 接收流式响应
        stream_start = await self.receive_message()
        if stream_start.get("type") == "stream_start":
            print("✅ 流式响应开始")
        else:
            print("❌ 流式响应开始失败")
            return
        
        # 接收内容块
        content_received = False
        while True:
            response = await self.receive_message()
            if response.get("type") == "stream_chunk":
                content_received = True
                print(f"📝 收到内容块: {response.get('content', '')[:50]}...")
            elif response.get("type") == "stream_end":
                print("✅ 流式响应结束")
                break
            elif response.get("type") == "error":
                print(f"❌ 文本消息处理错误: {response.get('error', {}).get('message', 'Unknown error')}")
                return
        
        if content_received:
            print("✅ 文本消息测试通过")
        else:
            print("❌ 文本消息测试失败")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始WebSocket功能测试...")
        
        # 连接
        if not await self.connect():
            return
        
        try:
            # 等待连接建立
            await asyncio.sleep(1)
            
            # 运行测试
            await self.test_heartbeat()
            await asyncio.sleep(0.5)
            
            await self.test_ping()
            await asyncio.sleep(0.5)
            
            await self.test_status()
            await asyncio.sleep(0.5)
            
            await self.test_text_message()
            
        finally:
            await self.disconnect()
        
        print("\n🎉 测试完成!")


async def main():
    """主函数"""
    client = WebSocketTestClient()
    await client.run_all_tests()


if __name__ == "__main__":
    print("WebSocket功能测试脚本")
    print("请确保yychat服务器正在运行 (python app.py)")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
