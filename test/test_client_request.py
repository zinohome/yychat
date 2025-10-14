#!/usr/bin/env python3
"""
测试客户端请求
模拟yyAsistant的请求来诊断问题
"""

import requests
import json
import time

def test_client_request():
    """测试客户端请求"""
    print("🧪 测试客户端请求...")
    
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
    
    try:
        # 发送流式请求
        response = requests.post(
            url,
            headers=headers,
            json=data,
            stream=True,
            timeout=30
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        print(f"📥 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ 请求成功，开始接收流式响应...")
            
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    print(f"📥 Chunk {chunk_count}: {line.decode('utf-8')}")
                    
                    # 只显示前几个chunk，避免输出太多
                    if chunk_count >= 5:
                        print("... (省略后续chunks)")
                        break
                        
            print(f"✅ 成功接收 {chunk_count} 个chunks")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"❌ 响应内容: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 客户端请求测试")
    print("=" * 50)
    
    result = test_client_request()
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 客户端请求测试成功")
    else:
        print("❌ 客户端请求测试失败")
    
    return result

if __name__ == "__main__":
    try:
        result = main()
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 测试被中断")
        exit(1)
