#!/usr/bin/env python3
"""
测试WebSocket连接管理改进
验证死循环问题是否已解决
"""

import asyncio
import websockets
import json
import time
import signal
import sys

class WebSocketConnectionTester:
    def __init__(self, uri='ws://localhost:9800/ws/chat'):
        self.uri = uri
        self.connections = []
        self.running = True
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        print(f"\n收到信号 {signum}，正在关闭...")
        self.running = False
    
    async def create_connection(self, connection_id):
        """创建一个WebSocket连接"""
        try:
            websocket = await websockets.connect(self.uri)
            self.connections.append(websocket)
            print(f"连接 {connection_id} 已建立")
            
            # 发送连接确认消息
            await websocket.send(json.dumps({
                "type": "heartbeat",
                "timestamp": time.time()
            }))
            
            # 等待响应
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"连接 {connection_id} 收到响应: {json.loads(response).get('type', 'unknown')}")
            
            return websocket
            
        except Exception as e:
            print(f"连接 {connection_id} 失败: {e}")
            return None
    
    async def close_connection(self, websocket, connection_id):
        """关闭一个WebSocket连接"""
        try:
            if websocket:
                await websocket.close()
                print(f"连接 {connection_id} 已关闭")
        except Exception as e:
            print(f"关闭连接 {connection_id} 时出错: {e}")
    
    async def test_rapid_connect_disconnect(self):
        """测试快速连接和断开"""
        print("开始测试快速连接和断开...")
        
        for i in range(5):
            if not self.running:
                break
                
            print(f"\n--- 测试轮次 {i+1} ---")
            
            # 创建多个连接
            connections = []
            for j in range(3):
                websocket = await self.create_connection(f"{i+1}-{j+1}")
                if websocket:
                    connections.append(websocket)
            
            # 等待一段时间
            await asyncio.sleep(1)
            
            # 关闭所有连接
            for j, websocket in enumerate(connections):
                await self.close_connection(websocket, f"{i+1}-{j+1}")
            
            # 等待清理
            await asyncio.sleep(0.5)
    
    async def test_abnormal_disconnect(self):
        """测试异常断开连接"""
        print("\n开始测试异常断开连接...")
        
        for i in range(3):
            if not self.running:
                break
                
            print(f"\n--- 异常断开测试 {i+1} ---")
            
            try:
                websocket = await self.create_connection(f"abnormal-{i+1}")
                if websocket:
                    # 模拟异常断开（不调用close）
                    print(f"连接 abnormal-{i+1} 异常断开")
                    # 不调用 websocket.close()，让连接自然超时
                    
            except Exception as e:
                print(f"异常断开测试 {i+1} 出错: {e}")
            
            await asyncio.sleep(1)
    
    async def test_concurrent_connections(self):
        """测试并发连接"""
        print("\n开始测试并发连接...")
        
        tasks = []
        for i in range(10):
            if not self.running:
                break
            task = asyncio.create_task(self.create_connection(f"concurrent-{i+1}"))
            tasks.append(task)
        
        # 等待所有连接建立
        connections = await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"建立了 {len([c for c in connections if c is not None and not isinstance(c, Exception)])} 个连接")
        
        # 等待一段时间
        await asyncio.sleep(2)
        
        # 关闭所有连接
        for i, websocket in enumerate(connections):
            if websocket and not isinstance(websocket, Exception):
                await self.close_connection(websocket, f"concurrent-{i+1}")
    
    async def run_tests(self):
        """运行所有测试"""
        print("WebSocket连接管理测试开始...")
        print("按 Ctrl+C 停止测试")
        
        try:
            # 测试1: 快速连接和断开
            await self.test_rapid_connect_disconnect()
            
            # 测试2: 异常断开
            await self.test_abnormal_disconnect()
            
            # 测试3: 并发连接
            await self.test_concurrent_connections()
            
        except KeyboardInterrupt:
            print("\n测试被用户中断")
        except Exception as e:
            print(f"测试过程中出错: {e}")
        finally:
            # 清理所有连接
            print("\n清理所有连接...")
            for websocket in self.connections:
                if websocket:
                    try:
                        await websocket.close()
                    except:
                        pass
            
            print("测试完成")

async def main():
    tester = WebSocketConnectionTester()
    await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main())
