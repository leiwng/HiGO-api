#!/usr/bin/env python3
"""
API 客户端测试工具
用于测试生成的 API Key
"""
import requests
import json
import time
from typing import dict, Any
import os

class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            })

    def set_api_key(self, api_key: str):
        """设置API Key"""
        self.api_key = api_key
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}"
        })

    def test_health(self) -> dict[str, Any]:
        """测试健康检查端点"""
        print("🏥 测试健康检查...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            result = {
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "success": response.status_code == 200
            }
            print(f"   状态码: {result['status_code']}")
            print(f"   响应: {result['response']}")
            return result
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            return {"success": False, "error": str(e)}

    def test_chat_completions(self, messages: list = None) -> dict[str, Any]:
        """测试聊天完成API (OpenAI兼容格式)"""
        print("💬 测试聊天完成API...")

        if not self.api_key:
            print("   ❌ 需要API Key")
            return {"success": False, "error": "API Key required"}

        if not messages:
            messages = [
                {"role": "user", "content": "我的狗狗最近食欲不振，可能是什么原因？"}
            ]

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        }

        try:
            print(f"   发送请求: {json.dumps(payload, ensure_ascii=False, indent=2)}")

            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/completions",
                json=payload
            )
            end_time = time.time()

            result = {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200
            }

            if response.headers.get('content-type', '').startswith('application/json'):
                result["response"] = response.json()

                if result["success"]:
                    usage = result["response"].get("usage", {})
                    choice = result["response"].get("choices", [{}])[0]
                    message = choice.get("message", {})

                    print(f"   ✅ 请求成功 ({result['response_time']:.2f}s)")
                    print(f"   Token使用: {usage}")
                    print(f"   AI回复: {message.get('content', 'No content')}")
                else:
                    print(f"   ❌ 请求失败: {result['response']}")
            else:
                result["response"] = response.text
                print(f"   ❌ 非JSON响应: {result['response']}")

            return result

        except Exception as e:
            print(f"   ❌ 错误: {e}")
            return {"success": False, "error": str(e)}

    def test_chat_legacy(self, question: str = None) -> dict[str, Any]:
        """测试传统聊天API"""
        print("💬 测试传统聊天API...")

        if not self.api_key:
            print("   ❌ 需要API Key")
            return {"success": False, "error": "API Key required"}

        if not question:
            question = "我的猫咪一直在咳嗽，需要注意什么？"

        payload = {
            "question": question,
            "conversation_id": f"test_{int(time.time())}"
        }

        try:
            print(f"   发送问题: {question}")

            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/",
                json=payload
            )
            end_time = time.time()

            result = {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200
            }

            if response.headers.get('content-type', '').startswith('application/json'):
                result["response"] = response.json()

                if result["success"]:
                    print(f"   ✅ 请求成功 ({result['response_time']:.2f}s)")
                    print(f"   AI回复: {result['response'].get('response', 'No response')}")
                else:
                    print(f"   ❌ 请求失败: {result['response']}")
            else:
                result["response"] = response.text
                print(f"   ❌ 非JSON响应: {result['response']}")

            return result

        except Exception as e:
            print(f"   ❌ 错误: {e}")
            return {"success": False, "error": str(e)}

    def test_rate_limiting(self, requests_count: int = 5) -> dict[str, Any]:
        """测试速率限制"""
        print(f"⏱️  测试速率限制 (发送{requests_count}个请求)...")

        if not self.api_key:
            print("   ❌ 需要API Key")
            return {"success": False, "error": "API Key required"}

        results = []

        for i in range(requests_count):
            print(f"   发送第 {i+1} 个请求...")

            result = self.test_chat_completions([
                {"role": "user", "content": f"测试请求 #{i+1}: 简单回答'收到'"}
            ])

            results.append({
                "request_number": i + 1,
                "status_code": result.get("status_code"),
                "success": result.get("success"),
                "response_time": result.get("response_time", 0)
            })

            if result.get("status_code") == 429:
                print(f"   🚫 触发速率限制")
                break

            # 短暂延迟
            time.sleep(0.5)

        success_count = sum(1 for r in results if r["success"])
        print(f"   总结: {success_count}/{len(results)} 请求成功")

        return {
            "success": True,
            "results": results,
            "success_rate": success_count / len(results) if results else 0
        }

    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🧪 开始综合测试")
        print("=" * 50)

        # 1. 健康检查
        health_result = self.test_health()

        if not health_result.get("success"):
            print("❌ 服务不可用，停止测试")
            return

        print()

        # 2. 测试聊天API (如果有API Key)
        if self.api_key:
            print("🔑 使用API Key进行认证测试")

            # OpenAI兼容API
            self.test_chat_completions()
            print()

            # 传统API
            self.test_chat_legacy()
            print()

            # 速率限制测试
            self.test_rate_limiting(3)
            print()
        else:
            print("⚠️  未提供API Key，跳过认证测试")

        print("🎉 测试完成")

def load_api_key_from_file() -> str:
    """从文件加载API Key"""
    try:
        with open("tools/generated_api_key.txt", "r") as f:
            for line in f:
                if line.startswith("API Key:"):
                    return line.split(":", 1)[1].strip()
    except FileNotFoundError:
        pass
    return None

def main():
    """主函数"""
    print("🧪 API 客户端测试工具")
    print("=" * 50)

    # 配置
    base_url = input("请输入API基础URL (默认: http://localhost:8000): ").strip() or "http://localhost:8000"

    # 尝试从文件加载API Key
    saved_api_key = load_api_key_from_file()
    if saved_api_key:
        print(f"发现保存的API Key: {saved_api_key[:20]}...")
        use_saved = input("使用保存的API Key? (y/n, 默认: y): ").strip().lower()
        if use_saved != 'n':
            api_key = saved_api_key
        else:
            api_key = input("请输入API Key (可选): ").strip() or None
    else:
        api_key = input("请输入API Key (可选): ").strip() or None

    # 创建客户端
    client = APIClient(base_url=base_url, api_key=api_key)

    print(f"\n配置:")
    print(f"  基础URL: {base_url}")
    print(f"  API Key: {'已设置' if api_key else '未设置'}")
    print()

    # 运行测试
    client.run_comprehensive_test()

if __name__ == "__main__":
    main()