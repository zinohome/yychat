"""
调试语音命令测试
"""

import asyncio
import json
import websockets
import time

async def test_voice_command_debug():
    """调试语音命令"""
    uri = "ws://localhost:9800/ws/chat"
    
    try:
        websocket = await websockets.connect(uri)
        print("✅ 已连接到WebSocket服务器")
        
        # 等待连接确认
        response = await websocket.recv()
        response_data = json.loads(response)
        print(f"📥 连接确认: {response_data}")
        
        # 发送语音命令
        message = {
            "type": "voice_command",
            "command": "start_recording",
            "timestamp": time.time()
        }
        
        await websocket.send(json.dumps(message))
        print("📤 已发送语音命令")
        
        # 等待响应
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            print(f"📥 收到响应: {response_data}")
        except asyncio.TimeoutError:
            print("⏰ 响应超时")
        
        await websocket.close()
        print("🔌 连接已关闭")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_voice_command_debug())
