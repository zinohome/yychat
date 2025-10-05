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
# 修改导入，使用自定义的OpenMemoryClient
from core.open_mem0_client import OpenMemoryClient
from config.config import get_config

# 获取配置
config = get_config()

class TestSelfhostOpenMemory:
    """测试本地OpenMemory服务器整合OpenAI功能"""
    
    def setup_method(self):
        """测试方法设置"""
        # 固定的测试用户ID
        self.user_id = "yyassistant"
        
        # 初始化OpenMemoryClient客户端，使用本地配置
        self.mem0_client = OpenMemoryClient(
            api_key=config.MEM0_API_KEY,
            host=config.MEM0_BASE_URL
        )
    
    def test_mem0_client_initialization(self):
        """测试OpenMemoryClient客户端初始化是否成功"""
        # 验证客户端是否成功初始化
        assert self.mem0_client is not None
        assert self.mem0_client.api_key == config.MEM0_API_KEY
        assert self.mem0_client.host == config.MEM0_BASE_URL
    
    def test_validate_api_key_custom(self):
        """使用自定义方法验证API密钥：访问/api/v1/auth/me，验证返回结果的user_id"""
        try:
            # 创建一个新的HTTP客户端进行自定义验证
            client = httpx.Client(
                base_url=config.MEM0_BASE_URL,
                headers={
                    "Authorization": f"Token {config.MEM0_API_KEY}",
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
            
            add_response = self.mem0_client.add(messages, user_id=self.user_id)
            
            # 验证添加是否成功
            assert add_response is not None
            assert "id" in add_response  # 假设成功响应包含id字段
            
            # 搜索记忆（添加后可能需要短暂延迟）
            import time
            time.sleep(1)  # 短暂延迟以确保记忆已保存
            
            search_response = self.mem0_client.search("意大利菜", user_id=self.user_id)
            
            # 验证搜索是否成功
            assert search_response is not None
            assert "results" in search_response
            assert len(search_response["results"]) > 0
            
            # 检查搜索结果是否包含我们添加的内容
            found = any(test_content in result.get("memory", "") for result in search_response["results"])
            assert found, "搜索结果中未找到添加的记忆内容"
            
        except Exception as e:
            pytest.fail(f"添加和搜索记忆失败: {str(e)}")
    
    @pytest.mark.skipif(not config.OPENAI_API_KEY, reason="OpenAI API密钥未配置")
    def test_integration_with_openai_actual(self):
        """测试与OpenAI的实际集成，使用真实的OpenAI API"""
        try:
            # 导入OpenAI相关的模块
            from agents import Agent, Runner, function_tool
            
            # 定义记忆工具
            @function_tool
            def search_memory(query: str, user_id: str) -> str:
                """Search through past conversations and memories"""
                memories = self.mem0_client.search(query, user_id=user_id, limit=3)
                if memories and memories.get('results'):
                    return "\n".join([f"- {mem['memory']}" for mem in memories['results']])
                return "No relevant memories found."
        
            @function_tool
            def save_memory(content: str, user_id: str) -> str:
                """Save important information to memory"""
                self.mem0_client.add([{"role": "user", "content": content}], user_id=user_id)
                return "Information saved to memory."
            
            # 创建具有记忆能力的Agent
            agent = Agent(
                name="Personal Assistant",
                instructions="""You are a helpful personal assistant with memory capabilities.
                Use the search_memory tool to recall past conversations and user preferences.
                Use the save_memory tool to store important information about the user.
                Always personalize your responses based on available memory.""",
                tools=[search_memory, save_memory],
                model=config.OPENAI_MODEL
            )
            
            # 定义与Agent交互的函数
            def chat_with_agent(user_input: str, user_id: str) -> str:
                """
                Handle user input with automatic memory integration.
        
                Args:
                    user_input: The user's message
                    user_id: Unique identifier for the user
        
                Returns:
                    The agent's response
                """
                # 运行Agent（它会在需要时自动使用记忆工具）
                result = Runner.run_sync(agent, user_input)
                return result.final_output
            
            # 测试场景1：保存用户偏好
            response_1 = chat_with_agent(
                "I love Italian food and I'm planning a trip to Rome next month",
                user_id=self.user_id
            )
            assert response_1 is not None
            assert isinstance(response_1, str)
            
            # 等待一会儿，确保记忆已保存
            import time
            time.sleep(1)
            
            # 测试场景2：利用存储的记忆回答问题
            response_2 = chat_with_agent(
                "Give me some recommendations for food",
                user_id=self.user_id
            )
            assert response_2 is not None
            assert isinstance(response_2, str)
            
            # 验证响应是否考虑了用户的偏好（意大利菜）
            # 注意：这是一个启发式检查，因为AI的响应可能有所不同
            assert "Italian" in response_2 or "意大利" in response_2,f"响应未考虑用户偏好: {response_2}"
            
        except ImportError:
            pytest.skip("未找到OpenAI Agents SDK，请安装: pip install openai-agents")
        except Exception as e:
            pytest.fail(f"OpenAI集成测试失败: {str(e)}")

if __name__ == "__main__":
    # 如果直接运行此文件，执行简单的测试演示
    import asyncio
    
    print("=== 测试本地OpenMemory服务器整合OpenAI功能 ===")
    
    # 获取配置
    config = get_config()
    
    # 显示配置信息（隐藏API密钥）
    print(f"Mem0服务器地址: {config.MEM0_BASE_URL}")
    print(f"Mem0 API密钥是否已配置: {'是' if config.MEM0_API_KEY else '否'}")
    print(f"OpenAI API密钥是否已配置: {'是' if config.OPENAI_API_KEY else '否'}")
    print(f"测试用户ID: yyassistant")
    
    try:
        # 初始化OpenMemoryClient客户端
        mem0_client = OpenMemoryClient(
            api_key=config.MEM0_API_KEY,
            host=config.MEM0_BASE_URL
        )
        
        print("\n✅ OpenMemoryClient客户端初始化成功")
        
        # 执行自定义API密钥验证
        print("\n执行API密钥验证...")
        client = httpx.Client(
            base_url=config.MEM0_BASE_URL,
            headers={
                "Authorization": f"Token {config.MEM0_API_KEY}",
                "Mem0-User-ID": "yyassistant"
            }
        )
        response = client.get("/api/v1/auth/me")
        response.raise_for_status()
        data = response.json()
        print(f"验证成功！返回的user_id: {data.get('user_id')}")
        
        # 简单的添加和搜索演示
        user_id = "yyassistant"
        test_content = "我喜欢意大利菜，下个月计划去罗马旅行"
        
        print(f"\n添加记忆: {test_content}")
        mem0_client.add([{"role": "user", "content": test_content}], user_id=user_id)
        
        print("等待1秒确保记忆已保存...")
        import time
        time.sleep(1)
        
        print("\n搜索记忆: '意大利菜'")
        search_results = mem0_client.search("意大利菜", user_id=user_id)
        
        if search_results and search_results.get('results'):
            print("找到相关记忆:")
            for i, result in enumerate(search_results['results'], 1):
                print(f"{i}. {result.get('memory', '')}")
        else:
            print("未找到相关记忆")
        
        # 如果配置了OpenAI API密钥，尝试运行集成演示
        if config.OPENAI_API_KEY:
            try:
                from agents import Agent, Runner, function_tool
                print("\n=== 运行OpenAI集成演示 ===")
                
                # 定义记忆工具
                @function_tool
                def search_memory(query: str, user_id: str) -> str:
                    """Search through past conversations and memories"""
                    memories = mem0_client.search(query, user_id=user_id, limit=3)
                    if memories and memories.get('results'):
                        return "\n".join([f"- {mem['memory']}" for mem in memories['results']])
                    return "No relevant memories found."
            
                @function_tool
                def save_memory(content: str, user_id: str) -> str:
                    """Save important information to memory"""
                    mem0_client.add([{"role": "user", "content": content}], user_id=user_id)
                    return "Information saved to memory."
                
                # 创建Agent
                agent = Agent(
                    name="Personal Assistant",
                    instructions="""You are a helpful personal assistant with memory capabilities.""",
                    tools=[search_memory, save_memory],
                    model=config.OPENAI_MODEL
                )
                
                # 交互函数
                def chat_with_agent(user_input: str, user_id: str) -> str:
                    result = Runner.run_sync(agent, user_input)
                    return result.final_output
                
                # 进行交互
                response_1 = chat_with_agent("I love Italian food", user_id)
                print(f"\n用户: I love Italian food")
                print(f"助手: {response_1}")
                
                time.sleep(1)
                
                response_2 = chat_with_agent("What kind of food do I like?", user_id)
                print(f"\n用户: What kind of food do I like?")
                print(f"助手: {response_2}")
                
            except ImportError:
                print("\n❌ 未找到OpenAI Agents SDK，请安装: pip install openai-agents")
            except Exception as e:
                print(f"\n❌ OpenAI集成演示出错: {str(e)}")
        
        print("\n=== 演示完成 ===")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {str(e)}")
        print("请检查Mem0服务器是否正常运行以及API密钥是否正确配置")