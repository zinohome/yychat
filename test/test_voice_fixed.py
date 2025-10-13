#!/usr/bin/env python3
"""
修复后的语音功能测试脚本
使用真实的音频文件进行测试
"""

import asyncio
import websockets
import json
import time
import base64
import os
from pathlib import Path


class VoiceTestClient:
    """语音测试客户端"""
    
    def __init__(self):
        self.websocket = None
        self.client_id = None
    
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.websocket = await websockets.connect("ws://localhost:9800/ws/chat")
            print("✅ 已连接到WebSocket服务器")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    async def send_message(self, message: dict):
        """发送消息"""
        if self.websocket:
            await self.websocket.send(json.dumps(message))
            print(f"📤 已发送消息: {message.get('type', 'unknown')}")
    
    async def receive_message(self, timeout: float = 5.0):
        """接收消息"""
        if self.websocket:
            try:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
                return json.loads(message)
            except asyncio.TimeoutError:
                return None
            except Exception as e:
                print(f"❌ 接收消息失败: {e}")
                return None
        return None
    
    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 连接已关闭")
    
    async def test_voice_command_fixed(self):
        """测试修复后的语音命令"""
        print("\n🎤 测试修复后的语音命令...")
        
        # 测试开始录音命令
        await self.send_message({
            "type": "voice_command",
            "command": "start_recording",
            "timestamp": time.time()
        })
        
        response = await self.receive_message()
        if response and response.get("type") == "recording_started":
            print("✅ 开始录音命令成功")
        else:
            print("❌ 开始录音命令失败")
            if response:
                print(f"   收到响应: {response}")
        
        # 测试改变语音命令
        await self.send_message({
            "type": "voice_command",
            "command": "change_voice",
            "voice": "nova",
            "personality_id": "health_assistant",
            "timestamp": time.time()
        })
        
        response = await self.receive_message()
        if response and response.get("type") == "voice_changed":
            print("✅ 改变语音命令成功")
        else:
            print("❌ 改变语音命令失败")
            if response:
                print(f"   收到响应: {response}")
    
    async def test_status_query_fixed(self):
        """测试修复后的状态查询"""
        print("\n📊 测试修复后的状态查询...")
        
        # 查询连接状态
        await self.send_message({
            "type": "status_query",
            "query_type": "connection",
            "timestamp": time.time()
        })
        
        response = await self.receive_message()
        if response and response.get("type") == "status_response":
            data = response.get("data", {})
            print(f"✅ 连接状态查询成功 - 连接数: {data.get('total_connections', 0)}")
        else:
            print("❌ 连接状态查询失败")
            if response:
                print(f"   收到响应: {response}")
        
        # 查询音频缓存状态
        await self.send_message({
            "type": "status_query",
            "query_type": "audio_cache",
            "timestamp": time.time()
        })
        
        response = await self.receive_message()
        if response and response.get("type") == "audio_cache_stats":
            data = response.get("data", {})
            print(f"✅ 音频缓存查询成功 - 缓存大小: {data.get('cache_size', 0)}")
        else:
            print("❌ 音频缓存查询失败")
            if response:
                print(f"   收到响应: {response}")
    
    async def test_text_with_voice(self):
        """测试带语音的文本消息"""
        print("\n💬 测试带语音的文本消息...")
        
        await self.send_message({
            "type": "text_message",
            "content": "Hello, please respond with voice!",
            "conversation_id": "test_conversation",
            "personality_id": "health_assistant",
            "use_tools": True,
            "stream": True,
            "enable_voice": True,
            "timestamp": time.time()
        })
        
        # 接收消息直到完成
        max_attempts = 20
        for _ in range(max_attempts):
            response = await self.receive_message()
            if not response:
                break
                
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


async def main():
    """主函数"""
    print("修复后的语音功能测试脚本")
    print("请确保yychat服务器正在运行 (python app.py)")
    print("=" * 50)
    
    client = VoiceTestClient()
    
    try:
        # 连接
        if not await client.connect():
            return
        
        # 等待连接确认
        response = await client.receive_message()
        if response and response.get("type") == "connection_established":
            print(f"📥 连接确认: {response}")
            client.client_id = response.get("client_id")
        
        # 运行测试
        await client.test_voice_command_fixed()
        await client.test_status_query_fixed()
        await client.test_text_with_voice()
        
        print("\n🎉 测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
