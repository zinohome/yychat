"""
音频API测试脚本
测试阶段2实现的音频功能
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:9800"
API_KEY = "yk-1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT1uV2wX3yZ4"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def test_audio_voices():
    """测试获取可用语音类型"""
    print("🎤 测试获取可用语音类型...")
    try:
        response = requests.get(f"{BASE_URL}/v1/audio/voices", headers=HEADERS)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功: {data}")
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")

def test_audio_models():
    """测试获取可用音频模型"""
    print("\n🤖 测试获取可用音频模型...")
    try:
        response = requests.get(f"{BASE_URL}/v1/audio/models", headers=HEADERS)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功: {data}")
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")

def test_personality_voices():
    """测试获取人格语音映射"""
    print("\n👤 测试获取人格语音映射...")
    try:
        response = requests.get(f"{BASE_URL}/v1/audio/personality-voices", headers=HEADERS)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功: {data}")
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")

def test_audio_cache_stats():
    """测试获取音频缓存统计"""
    print("\n📊 测试获取音频缓存统计...")
    try:
        response = requests.get(f"{BASE_URL}/v1/audio/cache/stats", headers=HEADERS)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功: {data}")
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")

def test_tts():
    """测试文本转语音"""
    print("\n🔊 测试文本转语音...")
    try:
        data = {
            "input": "Hello, this is a test message!",
            "voice": "alloy",
            "model": "tts-1",
            "speed": 1.0,
            "response_format": "mp3"
        }
        response = requests.post(f"{BASE_URL}/v1/audio/speech", 
                               headers=HEADERS, 
                               json=data)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ 成功: 音频大小 {len(response.content)} bytes")
            # 保存音频文件
            with open("test_speech.mp3", "wb") as f:
                f.write(response.content)
            print("音频文件已保存为 test_speech.mp3")
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")

def main():
    """主函数"""
    print("🚀 开始音频API功能测试...")
    print("=" * 50)
    
    # 测试各个端点
    test_audio_voices()
    test_audio_models()
    test_personality_voices()
    test_audio_cache_stats()
    test_tts()
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    main()
