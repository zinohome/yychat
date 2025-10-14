#!/usr/bin/env python3
"""
测试第一次请求的延迟
模拟第一次请求需要初始化Memory的情况
"""

import requests
import json
import time

def test_first_request_delay():
    """测试第一次请求的延迟"""
    print("🧪 测试第一次请求的延迟...")
    
    url = "http://localhost:9800/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4"
    }
    
    # 模拟客户端的请求数据
    data = {
        "model": "gpt-4.1",
        "messages": [{"role": "user", "content": "Hello"}],
        "personality_id": "health_assistant",
        "conversation_id": "conv-admin-1760323520182",
        "use_tools": True,
        "stream": True
    }
    
    print(f"📤 发送请求到: {url}")
    print(f"📤 请求数据: {json.dumps(data, indent=2)}")
    
    start_time = time.time()
    
    try:
        # 发送流式请求，设置较长的超时时间
        response = requests.post(
            url,
            headers=headers,
            json=data,
            stream=True,
            timeout=60  # 60秒超时
        )
        
        end_time = time.time()
        request_time = end_time - start_time
        
        print(f"📥 响应状态码: {response.status_code}")
        print(f"⏱️ 请求耗时: {request_time:.2f}秒")
        print(f"📥 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ 请求成功，开始接收流式响应...")
            
            chunk_count = 0
            first_chunk_time = None
            
            for line in response.iter_lines():
                if line:
                    if first_chunk_time is None:
                        first_chunk_time = time.time()
                        first_chunk_delay = first_chunk_time - start_time
                        print(f"⏱️ 首字节时间: {first_chunk_delay:.2f}秒")
                    
                    chunk_count += 1
                    print(f"📥 Chunk {chunk_count}: {line.decode('utf-8')[:100]}...")
                    
                    # 只显示前几个chunk，避免输出太多
                    if chunk_count >= 3:
                        print("... (省略后续chunks)")
                        break
                        
            print(f"✅ 成功接收 {chunk_count} 个chunks")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"❌ 响应内容: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时 (60秒)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 第一次请求延迟测试")
    print("=" * 50)
    
    result = test_first_request_delay()
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 第一次请求延迟测试成功")
    else:
        print("❌ 第一次请求延迟测试失败")
    
    return result

if __name__ == "__main__":
    try:
        result = main()
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 测试被中断")
        exit(1)
