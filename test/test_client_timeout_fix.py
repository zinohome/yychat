#!/usr/bin/env python3
"""
测试客户端超时修复
验证客户端是否能正确处理第一次请求的延迟
"""

import sys
import os

# 添加yyAsistant项目根目录到Python路径
yyasistant_root = "/Users/zhangjun/PycharmProjects/yyAsistant"
sys.path.insert(0, yyasistant_root)

def test_client_timeout_fix():
    """测试客户端超时修复"""
    print("🧪 测试客户端超时修复...")
    
    try:
        from utils.yychat_client import YYChatClient
        
        # 创建客户端
        client = YYChatClient()
        
        print("✅ YYChatClient创建成功")
        
        # 测试流式请求
        print("📤 测试流式请求...")
        try:
            response_generator = client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model="gpt-4.1",
                personality_id="health_assistant",
                conversation_id="conv-admin-1760323520182",
                use_tools=True,
                stream=True
            )
            
            print("✅ 流式请求发送成功")
            
            # 接收前几个响应
            chunk_count = 0
            for chunk in response_generator:
                chunk_count += 1
                print(f"📥 接收到chunk {chunk_count}: {str(chunk)[:100]}...")
                
                if chunk_count >= 3:
                    print("... (省略后续chunks)")
                    break
            
            print(f"✅ 成功接收 {chunk_count} 个chunks")
            return True
            
        except Exception as e:
            print(f"❌ 流式请求失败: {e}")
            return False
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 客户端超时修复测试")
    print("=" * 50)
    
    result = test_client_timeout_fix()
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 客户端超时修复测试成功")
        print("✅ 客户端现在可以正确处理第一次请求的延迟")
    else:
        print("❌ 客户端超时修复测试失败")
    
    return result

if __name__ == "__main__":
    try:
        result = main()
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 测试被中断")
        exit(1)
