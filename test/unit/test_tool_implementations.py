"""
工具实现测试
测试Calculator、TimeTool和TavilySearch工具
"""
import pytest
import math
from unittest.mock import Mock, patch, AsyncMock
from services.tools.implementations.calculator import CalculatorTool
from services.tools.implementations.time_tool import TimeTool
from services.tools.implementations.tavily_search import TavilySearchTool

@pytest.mark.asyncio
class TestCalculatorTool:
    """Calculator工具测试"""
    
    def test_calculator_tool_properties(self):
        """测试Calculator工具属性"""
        calc = CalculatorTool()
        
        assert calc.name == "calculator"
        assert "数学计算" in calc.description
        assert "operation" in calc.parameters
        assert "a" in calc.parameters
        print("✅ Calculator工具属性正确")
    
    async def test_calculator_add(self):
        """测试加法"""
        calc = CalculatorTool()
        result = await calc.execute({
            "operation": "add",
            "a": 5,
            "b": 3
        })
        
        assert result["result"] == 8
        assert result["operation"] == "add"
        print("✅ 加法计算正确")
    
    async def test_calculator_subtract(self):
        """测试减法"""
        calc = CalculatorTool()
        result = await calc.execute({
            "operation": "subtract",
            "a": 10,
            "b": 4
        })
        
        assert result["result"] == 6
        print("✅ 减法计算正确")
    
    async def test_calculator_multiply(self):
        """测试乘法"""
        calc = CalculatorTool()
        result = await calc.execute({
            "operation": "multiply",
            "a": 6,
            "b": 7
        })
        
        assert result["result"] == 42
        print("✅ 乘法计算正确")
    
    async def test_calculator_divide(self):
        """测试除法"""
        calc = CalculatorTool()
        result = await calc.execute({
            "operation": "divide",
            "a": 20,
            "b": 4
        })
        
        assert result["result"] == 5.0
        print("✅ 除法计算正确")
    
    async def test_calculator_divide_by_zero(self):
        """测试除以零"""
        calc = CalculatorTool()
        
        with pytest.raises(ValueError, match="除数不能为零"):
            await calc.execute({
                "operation": "divide",
                "a": 10,
                "b": 0
            })
        
        print("✅ 除以零错误处理正确")
    
    async def test_calculator_pow(self):
        """测试幂运算"""
        calc = CalculatorTool()
        result = await calc.execute({
            "operation": "pow",
            "a": 2,
            "b": 3
        })
        
        assert result["result"] == 8.0
        print("✅ 幂运算计算正确")
    
    async def test_calculator_sqrt(self):
        """测试平方根"""
        calc = CalculatorTool()
        result = await calc.execute({
            "operation": "sqrt",
            "a": 16
        })
        
        assert result["result"] == 4.0
        print("✅ 平方根计算正确")
    
    async def test_calculator_sqrt_negative(self):
        """测试负数平方根"""
        calc = CalculatorTool()
        
        with pytest.raises(ValueError, match="不能计算负数的平方根"):
            await calc.execute({
                "operation": "sqrt",
                "a": -16
            })
        
        print("✅ 负数平方根错误处理正确")
    
    async def test_calculator_invalid_operation(self):
        """测试无效操作"""
        calc = CalculatorTool()
        
        with pytest.raises(ValueError, match="不支持的操作"):
            await calc.execute({
                "operation": "invalid",
                "a": 10,
                "b": 5
            })
        
        print("✅ 无效操作错误处理正确")
    
    async def test_calculator_result_format(self):
        """测试结果格式"""
        calc = CalculatorTool()
        result = await calc.execute({
            "operation": "add",
            "a": 1,
            "b": 2
        })
        
        assert "result" in result
        assert "operation" in result
        assert "input" in result
        print("✅ 结果格式正确")


@pytest.mark.asyncio
class TestTimeTool:
    """TimeTool工具测试"""
    
    def test_time_tool_properties(self):
        """测试TimeTool工具属性"""
        time_tool = TimeTool()
        
        assert time_tool.name == "gettime"
        assert "上海时区" in time_tool.description
        assert "properties" in time_tool.parameters
        print("✅ TimeTool工具属性正确")
    
    async def test_time_tool_execute(self):
        """测试获取时间"""
        time_tool = TimeTool()
        result = await time_tool.execute({})
        
        assert "current_time" in result
        assert "timezone" in result
        assert "timestamp" in result
        assert "Asia/Shanghai" in result["timezone"]
        print(f"✅ 获取时间成功：{result['current_time']}")
    
    async def test_time_tool_format(self):
        """测试时间格式"""
        time_tool = TimeTool()
        result = await time_tool.execute({})
        
        # 检查时间格式 YYYY-MM-DD HH:MM:SS
        time_str = result["current_time"]
        assert len(time_str) == 19
        assert time_str[4] == '-'
        assert time_str[7] == '-'
        assert time_str[10] == ' '
        assert time_str[13] == ':'
        assert time_str[16] == ':'
        print("✅ 时间格式正确")
    
    async def test_time_tool_timestamp(self):
        """测试时间戳"""
        time_tool = TimeTool()
        result = await time_tool.execute({})
        
        timestamp = result["timestamp"]
        assert isinstance(timestamp, float)
        assert timestamp > 0
        print(f"✅ 时间戳正确：{timestamp}")


@pytest.mark.asyncio
class TestTavilySearchTool:
    """TavilySearch工具测试"""
    
    def test_tavily_tool_properties(self):
        """测试TavilySearch工具属性"""
        tavily = TavilySearchTool()
        
        assert tavily.name == "tavily_search"
        assert "搜索" in tavily.description
        assert "query" in tavily.parameters
        assert "search_depth" in tavily.parameters
        print("✅ TavilySearch工具属性正确")
    
    async def test_tavily_search_mock_success(self):
        """测试Tavily搜索（mock成功）"""
        tavily = TavilySearchTool()
        
        mock_response = {
            "query": "test query",
            "answer": "Test answer",
            "images": [],
            "results": [
                {
                    "title": "Test Result",
                    "url": "http://test.com",
                    "content": "Test content",
                    "score": 0.9
                }
            ],
            "response_time": 0.5,
            "request_id": "test123"
        }
        
        with patch('services.tools.implementations.tavily_search.TavilyClient') as mock_client:
            mock_instance = Mock()
            mock_instance.search.return_value = mock_response
            mock_client.return_value = mock_instance
            
            result = await tavily.execute({
                "query": "test query",
                "search_depth": "basic"
            })
            
            assert result["query"] == "test query"
            assert result["answer"] == "Test answer"
            assert len(result["results"]) == 1
            print("✅ Tavily搜索（mock）成功")
    
    async def test_tavily_search_empty_query(self):
        """测试空查询"""
        tavily = TavilySearchTool()
        
        with pytest.raises(ValueError, match="搜索查询不能为空"):
            await tavily.execute({})
        
        print("✅ 空查询错误处理正确")
    
    async def test_tavily_search_no_api_key(self):
        """测试缺少API密钥"""
        tavily = TavilySearchTool()
        
        with patch('services.tools.implementations.tavily_search.config') as mock_config:
            mock_config.TAVILY_API_KEY = None
            
            with pytest.raises(ValueError, match="未配置Tavily API密钥"):
                await tavily.execute({"query": "test"})
            
            print("✅ 缺少API密钥错误处理正确")
    
    async def test_tavily_search_default_depth(self):
        """测试默认搜索深度"""
        tavily = TavilySearchTool()
        
        mock_response = {
            "query": "test",
            "answer": "answer",
            "results": []
        }
        
        with patch('services.tools.implementations.tavily_search.TavilyClient') as mock_client:
            mock_instance = Mock()
            mock_instance.search.return_value = mock_response
            mock_client.return_value = mock_instance
            
            # 不提供search_depth，应该使用默认值
            await tavily.execute({"query": "test"})
            
            # 验证search调用使用了默认depth
            mock_instance.search.assert_called_once()
            call_args = mock_instance.search.call_args
            assert call_args[1]["search_depth"] == "basic"
            
            print("✅ 默认搜索深度正确")
    
    async def test_tavily_search_result_format(self):
        """测试搜索结果格式"""
        tavily = TavilySearchTool()
        
        mock_response = {
            "query": "test",
            "answer": "answer",
            "images": ["img1", "img2"],
            "results": [
                {"title": "T1", "url": "u1", "content": "c1", "score": 0.9}
            ],
            "response_time": 1.0,
            "request_id": "req123"
        }
        
        with patch('services.tools.implementations.tavily_search.TavilyClient') as mock_client:
            mock_instance = Mock()
            mock_instance.search.return_value = mock_response
            mock_client.return_value = mock_instance
            
            result = await tavily.execute({"query": "test"})
            
            assert "query" in result
            assert "answer" in result
            assert "images" in result
            assert "results" in result
            assert "response_time" in result
            assert len(result["images"]) == 2
            
            print("✅ 搜索结果格式正确")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
