"""
实时语音对话测试脚本
测试阶段3实现的实时消息处理功能
"""

import asyncio
import json
import base64
import websockets
import time
from typing import Dict, Any


class RealtimeVoiceTestClient:
    """实时语音测试客户端"""
    
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
    
    async def test_text_with_voice(self):
        """测试带语音的文本消息"""
        print("\n💬 测试带语音的文本消息...")
        
        # 发送带语音的文本消息
        await self.send_message({
            "type": "text_message",
            "content": "Hello, please respond with voice!",
            "conversation_id": "test_conversation",
            "personality_id": "health_assistant",
            "stream": True,
            "enable_voice": True,
            "timestamp": time.time()
        })
        
        # 接收消息直到完成
        max_attempts = 20
        for _ in range(max_attempts):
            response = await self.receive_message()
            if response.get("type") == "connection_established":
                print("📡 收到连接确认消息")
                continue
            elif response.get("type") == "processing_start":
                print("✅ 文本处理开始")
            elif response.get("type") == "stream_start":
                print("✅ 流式响应开始")
            elif response.get("type") == "stream_chunk":
                content = response.get("content", "")
                print(f"📝 收到内容块: {content[:50]}...")
            elif response.get("type") == "stream_end":
                print("✅ 流式响应结束")
            elif response.get("type") == "voice_generation_start":
                voice = response.get("voice", "unknown")
                print(f"🎤 语音生成开始，使用语音: {voice}")
            elif response.get("type") == "voice_response":
                audio_size = len(response.get("audio_data", ""))
                print(f"🔊 收到语音响应，音频大小: {audio_size} bytes")
                break
            elif response.get("type") == "error":
                print(f"❌ 错误: {response.get('error', {}).get('message', 'Unknown error')}")
                break
    
    async def test_voice_command(self):
        """测试语音命令"""
        print("\n🎤 测试语音命令...")
        
        # 测试开始录音命令
        await self.send_message({
            "type": "voice_command",
            "command": "start_recording",
            "timestamp": time.time()
        })
        
        response = await self.receive_message()
        if response.get("type") == "recording_started":
            print("✅ 开始录音命令成功")
        else:
            print("❌ 开始录音命令失败")
        
        # 测试改变语音命令
        await self.send_message({
            "type": "voice_command",
            "command": "change_voice",
            "voice": "nova",
            "personality_id": "health_assistant",
            "timestamp": time.time()
        })
        
        response = await self.receive_message()
        if response.get("type") == "voice_changed":
            print("✅ 改变语音命令成功")
        else:
            print("❌ 改变语音命令失败")
    
    async def test_status_query(self):
        """测试状态查询"""
        print("\n📊 测试状态查询...")
        
        # 查询连接状态
        await self.send_message({
            "type": "status_query",
            "query_type": "connection",
            "timestamp": time.time()
        })
        
        response = await self.receive_message()
        if response.get("type") == "status_response":
            data = response.get("data", {})
            print(f"✅ 连接状态查询成功 - 连接数: {data.get('total_connections', 0)}")
        else:
            print("❌ 连接状态查询失败")
        
        # 查询音频缓存状态
        await self.send_message({
            "type": "status_query",
            "query_type": "audio_cache",
            "timestamp": time.time()
        })
        
        response = await self.receive_message()
        if response.get("type") == "audio_cache_stats":
            data = response.get("data", {})
            print(f"✅ 音频缓存查询成功 - 缓存大小: {data.get('cache_size', 0)}")
        else:
            print("❌ 音频缓存查询失败")
    
    async def test_audio_input(self):
        """测试音频输入（模拟）"""
        print("\n🎵 测试音频输入...")
        
        # 创建一个模拟的音频数据（Base64编码的简单音频）
        # 这里使用一个简单的测试数据
        test_audio_data = base64.b64encode(b"fake_audio_data_for_testing").decode('utf-8')
        
        await self.send_message({
            "type": "audio_input",
            "audio_data": test_audio_data,
            "conversation_id": "test_conversation",
            "personality_id": "health_assistant",
            "auto_reply": True,
            "enable_voice": True,
            "timestamp": time.time()
        })
        
        # 接收消息直到完成
        max_attempts = 15
        for _ in range(max_attempts):
            response = await self.receive_message()
            if response.get("type") == "audio_processing_start":
                print("✅ 音频处理开始")
            elif response.get("type") == "transcription_result":
                text = response.get("text", "")
                print(f"📝 转录结果: {text}")
            elif response.get("type") == "processing_start":
                print("✅ 文本处理开始")
            elif response.get("type") == "stream_start":
                print("✅ 流式响应开始")
            elif response.get("type") == "stream_chunk":
                content = response.get("content", "")
                print(f"📝 收到内容块: {content[:30]}...")
            elif response.get("type") == "stream_end":
                print("✅ 流式响应结束")
            elif response.get("type") == "voice_response":
                print("🔊 收到语音响应")
                break
            elif response.get("type") == "error":
                print(f"❌ 错误: {response.get('error', {}).get('message', 'Unknown error')}")
                break
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始实时语音对话功能测试...")
        
        # 连接
        if not await self.connect():
            return
        
        try:
            # 等待连接建立
            await asyncio.sleep(1)
            
            # 运行测试
            await self.test_text_with_voice()
            await asyncio.sleep(1)
            
            await self.test_voice_command()
            await asyncio.sleep(1)
            
            await self.test_status_query()
            await asyncio.sleep(1)
            
            await self.test_audio_input()
            
        finally:
            await self.disconnect()
        
        print("\n🎉 测试完成!")


async def main():
    """主函数"""
    client = RealtimeVoiceTestClient()
    await client.run_all_tests()


if __name__ == "__main__":
    print("实时语音对话功能测试脚本")
    print("请确保yychat服务器正在运行 (python app.py)")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
