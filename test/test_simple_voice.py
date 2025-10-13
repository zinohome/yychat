"""
简单的语音命令测试
"""

import asyncio
import json
import websockets
import time

async def test_voice_command():
    """测试语音命令"""
    uri = "ws://localhost:9800/ws/chat"
    
    try:
        websocket = await websockets.connect(uri)
        print("✅ 已连接到WebSocket服务器")
        
        # 发送语音命令
        message = {
            "type": "voice_command",
            "command": "start_recording",
            "timestamp": time.time()
        }
        
        await websocket.send(json.dumps(message))
        print("📤 已发送语音命令")
        
        # 接收响应
        response = await websocket.recv()
        response_data = json.loads(response)
        print(f"📥 收到响应: {response_data}")
        
        await websocket.close()
        print("🔌 连接已关闭")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_voice_command())
