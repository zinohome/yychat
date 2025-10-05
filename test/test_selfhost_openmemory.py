#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试本地OpenMemory服务器整合OpenAI功能

这个测试文件验证本地部署的Mem0服务器是否能正确与OpenAI API集成，
参考文档：https://docs.mem0.ai/integrations/openai-agents-sdk
"""

import os
import pytest
import httpx
from unittest.mock import patch, MagicMock
from core.openmem0 import Mem0
from config.config import get_config

# 获取配置
config = get_config()

class TestSelfhostOpenMemory:
    """测试本地OpenMemory服务器整合OpenAI功能"""
    
    def setup_method(self):
        """测试方法设置"""
        # 固定的测试用户ID
        self.user_id = "yyassistant"
        
        # 初始化Mem0客户端，使用本地配置和OPENAI_BASE_URL
        self.mem0_client = Mem0(
            api_key=config.MEM0_API_KEY,
            host=config.MEM0_BASE_URL
        )
    
    def test_mem0_client_initialization(self):
        """测试Mem0客户端初始化是否成功"""
        # 验证客户端是否成功初始化
        assert self.mem0_client is not None
    
    def test_validate_api_key_custom(self):
        """使用自定义方法验证API密钥：访问/api/v1/auth/me，验证返回结果的user_id"""
        try:
            # 创建一个新的HTTP客户端进行自定义验证
            client = httpx.Client(
                base_url=config.MEM0_BASE_URL,
                headers={
                    "Authorization": f"Bearer {config.MEM0_API_KEY}",
                    "Mem0-User-ID": self.user_id
                },
                timeout=30
            )
            
            # 访问自定义验证端点
            response = client.get("/api/v1/auth/me")
            response.raise_for_status()  # 确保请求成功
            
            # 解析响应
            data = response.json()
            
            # 验证返回的user_id是否与测试用户ID相同
            assert "user_id" in data, "响应中未包含user_id字段"
            assert data["user_id"] == self.user_id, f"返回的user_id不匹配: {data['user_id']} != {self.user_id}"
            
        except httpx.HTTPStatusError as e:
            pytest.fail(f"API密钥验证失败，HTTP错误: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            pytest.fail(f"无法连接到本地Mem0服务器或验证失败: {str(e)}")
    
    def test_add_and_search_memory(self):
        """测试添加和搜索记忆功能"""
        try:
            # 添加记忆
            test_content = "我喜欢意大利菜，下个月计划去罗马旅行"
            messages = [{"role": "user", "content": test_content}]
            
            # 第一次交互：存储用户偏好
            chat_completion = self.mem0_client.chat.completions.create(
                messages=messages,
                model=config.OPENAI_MODEL,
                user_id=self.user_id,
                base_url=config.OPENAI_BASE_URL,
                api_key=config.OPENAI_API_KEY
            )
            
            # 验证响应是否成功
            assert chat_completion is not None
            assert hasattr(chat_completion, 'choices') and len(chat_completion.choices) > 0
            
            # 等待一会儿，确保记忆已保存
            import time
            time.sleep(1)  # 短暂延迟以确保记忆已保存
            
            # 第二次交互：利用存储的记忆
            search_messages = [{"role": "user", "content": "我喜欢什么食物？"}]
            search_response = self.mem0_client.chat.completions.create(
                messages=search_messages,
                model=config.OPENAI_MODEL,
                user_id=self.user_id,
                base_url=config.OPENAI_BASE_URL,
                api_key=config.OPENAI_API_KEY
            )
            
            # 验证响应是否成功
            assert search_response is not None
            assert hasattr(search_response, 'choices') and len(search_response.choices) > 0
            assert hasattr(search_response.choices[0], 'message')
            assert hasattr(search_response.choices[0].message, 'content')
            
            # 检查响应是否包含用户的偏好信息
            response_content = search_response.choices[0].message.content
            assert "意大利" in response_content or "Italian" in response_content, f"响应未包含用户偏好信息: {response_content}"
            
        except Exception as e:
            pytest.fail(f"添加和搜索记忆失败: {str(e)}")
    
    @pytest.mark.skipif(not config.OPENAI_API_KEY, reason="OpenAI API密钥未配置")
    def test_integration_with_openai_actual(self):
        """测试与OpenAI的实际集成，使用真实的OpenAI API"""
        try:
            # 第一次交互：存储用户偏好
            messages1 = [
                {
                    "role": "user",
                    "content": "I love Italian food and I'm planning a trip to Rome next month"
                }
            ]
            
            chat_completion1 = self.mem0_client.chat.completions.create(
                messages=messages1,
                model=config.OPENAI_MODEL,
                user_id=self.user_id,
                base_url=config.OPENAI_BASE_URL,
                api_key=config.OPENAI_API_KEY
            )
            
            # 验证响应是否成功
            assert chat_completion1 is not None
            assert hasattr(chat_completion1, 'choices') and len(chat_completion1.choices) > 0
            
            # 等待一会儿，确保记忆已保存
            import time
            time.sleep(1)
            
            # 第二次交互：利用存储的记忆回答问题
            messages2 = [
                {
                    "role": "user",
                    "content": "Give me some recommendations for food"
                }
            ]
            
            chat_completion2 = self.mem0_client.chat.completions.create(
                messages=messages2,
                model=config.OPENAI_MODEL,
                user_id=self.user_id,
                base_url=config.OPENAI_BASE_URL,
                api_key=config.OPENAI_API_KEY
            )
            
            # 验证响应是否成功
            assert chat_completion2 is not None
            assert hasattr(chat_completion2, 'choices') and len(chat_completion2.choices) > 0
            
            # 验证响应是否考虑了用户的偏好（意大利菜）
            response_content = chat_completion2.choices[0].message.content
            assert "Italian" in response_content or "意大利" in response_content, f"响应未考虑用户偏好: {response_content}"
            
        except Exception as e:
            pytest.fail(f"OpenAI集成测试失败: {str(e)}")

if __name__ == "__main__":
    # 如果直接运行此文件，执行简单的测试演示
    print("=== 测试本地OpenMemory服务器整合OpenAI功能 ===")
    
    # 获取配置
    config = get_config()
    
    # 显示配置信息（隐藏API密钥）
    print(f"Mem0服务器地址: {config.MEM0_BASE_URL}")
    print(f"Mem0 API密钥是否已配置: {'是' if config.MEM0_API_KEY else '否'}")
    print(f"OpenAI API密钥是否已配置: {'是' if config.OPENAI_API_KEY else '否'}")
    print(f"OpenAI基础URL: {config.OPENAI_BASE_URL}")
    print(f"测试用户ID: yyassistant")
    
    try:
        # 初始化Mem0客户端
        mem0_client = Mem0(
            api_key=config.MEM0_API_KEY,
            host=config.MEM0_BASE_URL
        )
        
        print("\n✅ Mem0客户端初始化成功")
        
        # 执行自定义API密钥验证
        print("\n执行API密钥验证...")
        client = httpx.Client(
            base_url=config.MEM0_BASE_URL,
            headers={
                "Authorization": f"Bearer {config.MEM0_API_KEY}",
                "Mem0-User-ID": "yyassistant"
            }
        )
        response = client.get("/api/v1/auth/me")
        response.raise_for_status()
        data = response.json()
        print(f"验证成功！返回的user_id: {data.get('user_id')}")
        
        # 简单的添加和搜索演示
        user_id = "yyassistant"
        print("\n=== 运行Mem0 + OpenAI集成演示 ===")
        
        # 第一次交互：存储用户偏好
        messages1 = [
            {
                "role": "user",
                "content": "I love Italian food"
            }
        ]
        
        print(f"用户: I love Italian food")
        chat_completion1 = mem0_client.chat.completions.create(
            messages=messages1,
            model=config.OPENAI_MODEL,
            user_id=user_id,
            base_url=config.OPENAI_BASE_URL,
            api_key=config.OPENAI_API_KEY
        )
        print(f"助手: {chat_completion1.choices[0].message.content}")
        
        print("等待1秒确保记忆已保存...")
        import time
        time.sleep(1)
        
        # 第二次交互：利用存储的记忆
        messages2 = [
            {
                "role": "user",
                "content": "What kind of food do I like?"
            }
        ]
        
        print(f"\n用户: What kind of food do I like?")
        chat_completion2 = mem0_client.chat.completions.create(
            messages=messages2,
            model=config.OPENAI_MODEL,
            user_id=user_id,
            base_url=config.OPENAI_BASE_URL,
            api_key=config.OPENAI_API_KEY
        )
        print(f"助手: {chat_completion2.choices[0].message.content}")
        
        # 检查响应是否包含用户偏好
        response_content = chat_completion2.choices[0].message.content
        if "Italian" in response_content or "意大利" in response_content:
            print("\n✅ 测试成功！助手成功回忆起用户喜欢意大利菜")
        else:
            print("\n⚠️ 注意：助手可能没有正确回忆起用户的偏好")
        
        print("\n=== 演示完成 ===")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {str(e)}")
        print("请检查Mem0服务器是否正常运行以及API密钥是否正确配置")