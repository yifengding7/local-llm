#!/usr/bin/env python3
"""
AI监理系统 - API测试客户端
测试所有API端点功能
"""

import httpx
import asyncio
import json
from datetime import datetime

# API配置
API_BASE = "http://localhost:8000"

# 测试数据
TEST_CODE = '''
def calculate_sum(numbers):
    total = 0
    for i in range(len(numbers)):
        total = total + numbers[i]
    return total

# 测试
result = calculate_sum([1, 2, 3, 4, 5])
print(f"Sum: {result}")
'''

class APITester:
    def __init__(self, base_url=API_BASE):
        self.base_url = base_url
        self.results = []
    
    async def test_health(self):
        """测试健康检查"""
        print("\n🏥 测试健康检查...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                data = response.json()
                
                if response.status_code == 200:
                    print(f"✅ 健康检查通过")
                    print(f"   Ollama状态: {data.get('ollama', 'unknown')}")
                    models = data.get('available_models', [])
                    if models:
                        print(f"   可用模型: {', '.join(models)}")
                    else:
                        print("   ⚠️ 没有可用模型")
                    return True
                else:
                    print(f"❌ 健康检查失败: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    async def test_chat(self):
        """测试聊天功能"""
        print("\n💬 测试聊天功能...")
        
        messages = [
            {"role": "user", "content": "你好，请用一句话介绍自己"}
        ]
        
        try:
            async with httpx.AsyncClient() as client:
                start_time = datetime.now()
                response = await client.post(
                    f"{self.base_url}/chat",
                    json={"messages": messages},
                    timeout=30.0
                )
                elapsed = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 聊天测试通过 (耗时: {elapsed:.2f}秒)")
                    print(f"   回复: {data.get('response', '')[:100]}...")
                    print(f"   模型: {data.get('model', 'unknown')}")
                    return True
                else:
                    print(f"❌ 聊天测试失败: {response.status_code}")
                    print(f"   错误: {response.text}")
                    return False
                    
        except httpx.TimeoutException:
            print("❌ 聊天请求超时（可能是模型太大或系统太慢）")
            return False
        except Exception as e:
            print(f"❌ 聊天测试错误: {e}")
            return False
    
    async def test_code_analysis(self):
        """测试代码分析"""
        print("\n🔍 测试代码分析...")
        
        try:
            async with httpx.AsyncClient() as client:
                start_time = datetime.now()
                response = await client.post(
                    f"{self.base_url}/analyze/code",
                    json={
                        "code": TEST_CODE,
                        "language": "python"
                    },
                    timeout=60.0
                )
                elapsed = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 代码分析通过 (耗时: {elapsed:.2f}秒)")
                    analysis = data.get('analysis', '')
                    print(f"   分析结果预览:")
                    print(f"   {analysis[:200]}...")
                    return True
                else:
                    print(f"❌ 代码分析失败: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ 代码分析错误: {e}")
            return False
    
    async def test_code_generation(self):
        """测试代码生成"""
        print("\n🏗️ 测试代码生成...")
        
        description = "编写一个函数，计算斐波那契数列的第n项"
        
        try:
            async with httpx.AsyncClient() as client:
                start_time = datetime.now()
                response = await client.post(
                    f"{self.base_url}/generate/code",
                    params={
                        "description": description,
                        "language": "python"
                    },
                    timeout=60.0
                )
                elapsed = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 代码生成通过 (耗时: {elapsed:.2f}秒)")
                    code = data.get('code', '')
                    if code:
                        print(f"   生成的代码:")
                        print("   " + "\n   ".join(code.split("\n")[:10]))
                    return True
                else:
                    print(f"❌ 代码生成失败: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ 代码生成错误: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("="*50)
        print("🧪 AI监理系统API测试")
        print("="*50)
        
        # 运行测试
        tests = [
            ("健康检查", self.test_health()),
            ("聊天功能", self.test_chat()),
            ("代码分析", self.test_code_analysis()),
            ("代码生成", self.test_code_generation())
        ]
        
        results = []
        for name, test in tests:
            result = await test
            results.append((name, result))
        
        # 显示总结
        print("\n" + "="*50)
        print("📊 测试总结")
        print("="*50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{name}: {status}")
        
        print(f"\n总计: {passed}/{total} 通过")
        
        if passed == total:
            print("\n🎉 所有测试通过！系统运行正常。")
        elif passed > 0:
            print("\n⚠️ 部分测试失败，请检查相关服务。")
        else:
            print("\n❌ 所有测试失败，请检查:")
            print("1. API服务是否运行: uvicorn app_mini:app")
            print("2. Ollama是否运行: ollama serve")
            print("3. 是否安装了模型: ollama pull llama3.2")

async def interactive_test():
    """交互式测试"""
    print("\n🎮 交互式测试模式")
    print("输入你的问题（输入'exit'退出）:")
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                user_input = input("\n> ")
                if user_input.lower() == 'exit':
                    break
                
                response = await client.post(
                    f"{API_BASE}/chat",
                    json={
                        "messages": [{"role": "user", "content": user_input}]
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"\n🤖 {data.get('response', '')}")
                else:
                    print(f"❌ 错误: {response.status_code}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 错误: {e}")

async def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        await interactive_test()
    else:
        tester = APITester()
        await tester.run_all_tests()
        
        print("\n💡 提示：")
        print("- 运行交互式测试: python test_client.py interactive")
        print("- 查看API文档: http://localhost:8000/docs")

if __name__ == "__main__":
    asyncio.run(main())
