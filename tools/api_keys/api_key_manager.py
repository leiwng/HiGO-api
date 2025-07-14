#!/usr/bin/env python3
"""
API Key 管理工具
用于管理测试环境中的 API Key
"""
import asyncio
import sys
import os
from datetime import datetime, timezone

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.storage.mongo_service import MongoService
from app.models.api_key import APIKey, APIKeyStatus

class APIKeyManager:
    def __init__(self):
        self.mongo = MongoService()

    async def list_all_api_keys(self):
        """列出所有API Key"""
        keys = await self.mongo.find_many(
            "api_keys",
            {},
            sort=[("created_at", -1)]
        )

        if not keys:
            print("❌ 没有找到任何API Key")
            return

        print(f"📋 共找到 {len(keys)} 个API Key")
        print("=" * 80)

        for i, key_doc in enumerate(keys, 1):
            api_key = APIKey(**key_doc)
            status_emoji = {
                "active": "✅",
                "suspended": "⏸️",
                "expired": "⏰",
                "revoked": "❌"
            }.get(api_key.status, "❓")

            print(f"{i}. {status_emoji} {api_key.name}")
            print(f"   Key ID: {api_key.key_id}")
            print(f"   用户ID: {api_key.user_id}")
            print(f"   类型: {api_key.type}")
            print(f"   状态: {api_key.status}")
            print(f"   Token使用: {api_key.total_tokens_used:,}")
            print(f"   创建时间: {api_key.created_at}")
            if api_key.expires_at:
                print(f"   过期时间: {api_key.expires_at}")
            print()

    async def revoke_api_key(self, key_id: str):
        """撤销API Key"""
        result = await self.mongo.update_one(
            "api_keys",
            {"_id": key_id},
            {
                "status": APIKeyStatus.REVOKED,
                "updated_at": datetime.now(timezone.utc)
            }
        )

        if result:
            print(f"✅ API Key {key_id} 已撤销")
        else:
            print(f"❌ API Key {key_id} 撤销失败")

        return result

    async def activate_api_key(self, key_id: str):
        """激活API Key"""
        result = await self.mongo.update_one(
            "api_keys",
            {"_id": key_id},
            {
                "status": APIKeyStatus.ACTIVE,
                "updated_at": datetime.now(timezone.utc)
            }
        )

        if result:
            print(f"✅ API Key {key_id} 已激活")
        else:
            print(f"❌ API Key {key_id} 激活失败")

        return result

    async def delete_api_key(self, key_id: str):
        """删除API Key"""
        result = await self.mongo.delete_one("api_keys", {"_id": key_id})

        if result:
            print(f"✅ API Key {key_id} 已删除")
        else:
            print(f"❌ API Key {key_id} 删除失败")

        return result

    async def reset_usage_stats(self, key_id: str):
        """重置使用统计"""
        result = await self.mongo.update_one(
            "api_keys",
            {"_id": key_id},
            {
                "total_tokens_used": 0,
                "monthly_tokens_used": 0,
                "daily_tokens_used": 0,
                "updated_at": datetime.now(timezone.utc)
            }
        )

        if result:
            print(f"✅ API Key {key_id} 使用统计已重置")
        else:
            print(f"❌ API Key {key_id} 使用统计重置失败")

        return result

    async def cleanup_revoked_keys(self):
        """清理已撤销的API Key"""
        # 删除所有已撤销的key
        deleted_count = 0
        revoked_keys = await self.mongo.find_many(
            "api_keys",
            {"status": APIKeyStatus.REVOKED}
        )

        for key_doc in revoked_keys:
            await self.mongo.delete_one("api_keys", {"_id": key_doc["_id"]})
            deleted_count += 1

        print(f"✅ 已清理 {deleted_count} 个已撤销的API Key")
        return deleted_count

async def main():
    """主函数"""
    manager = APIKeyManager()

    while True:
        print("\n🔧 API Key 管理工具")
        print("=" * 30)
        print("1. 列出所有API Key")
        print("2. 撤销API Key")
        print("3. 激活API Key")
        print("4. 删除API Key")
        print("5. 重置使用统计")
        print("6. 清理已撤销的Key")
        print("0. 退出")

        choice = input("\n请选择操作 (0-6): ").strip()

        if choice == "0":
            print("👋 再见！")
            break

        elif choice == "1":
            await manager.list_all_api_keys()

        elif choice in ["2", "3", "4", "5"]:
            key_id = input("请输入API Key ID: ").strip()
            if not key_id:
                print("❌ API Key ID 不能为空")
                continue

            if choice == "2":
                await manager.revoke_api_key(key_id)
            elif choice == "3":
                await manager.activate_api_key(key_id)
            elif choice == "4":
                confirm = input(f"确认删除 API Key {key_id}? (y/N): ").strip().lower()
                if confirm == 'y':
                    await manager.delete_api_key(key_id)
                else:
                    print("❌ 操作已取消")
            elif choice == "5":
                await manager.reset_usage_stats(key_id)

        elif choice == "6":
            confirm = input("确认清理所有已撤销的API Key? (y/N): ").strip().lower()
            if confirm == 'y':
                await manager.cleanup_revoked_keys()
            else:
                print("❌ 操作已取消")

        else:
            print("❌ 无效选择")

if __name__ == "__main__":
    asyncio.run(main())