#!/usr/bin/env python3
"""
API Key 生成工具
用于生成测试用的 API Key
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.config import settings
from app.services.storage.mongo_service import MongoService
from app.models.api_key import APIKey, APIKeyType, APIKeyStatus
from app.models.account import Account, AccountType

class APIKeyGenerator:
    def __init__(self):
        self.mongo = MongoService()

    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """生成API Key和对应的哈希值"""
        prefix = "sk-higo"
        random_part = secrets.token_urlsafe(32)
        api_key = f"{prefix}-{random_part}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return api_key, key_hash

    async def create_test_user(self, username: str = "test_user") -> str:
        """创建测试用户"""
        user_id = str(uuid.uuid4())
        user_doc = {
            "_id": user_id,
            "username": username,
            "email": f"{username}@example.com",
            "password_hash": "test_hash",
            "salt": "test_salt",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        # 检查用户是否已存在
        existing_user = await self.mongo.find_one("users", {"username": username})
        if existing_user:
            print(f"用户 {username} 已存在，使用现有用户ID: {existing_user['_id']}")
            return str(existing_user["_id"])

        await self.mongo.insert_one("users", user_doc)
        print(f"创建测试用户: {username}, ID: {user_id}")
        return user_id

    async def create_test_account(self, user_id: str) -> Account:
        """创建测试账户"""
        account = Account(
            user_id=user_id,
            account_type=AccountType.DEVELOPER,
            balance_cents=10000,  # $100
            credit_cents=500,     # $5 免费额度
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # 检查账户是否已存在
        existing_account = await self.mongo.find_one("accounts", {"user_id": user_id})
        if existing_account:
            print(f"用户 {user_id} 的账户已存在")
            return Account(**existing_account)

        account_id = await self.mongo.insert_one("accounts", account.model_dump())
        account.id = account_id
        print(f"创建测试账户: {account_id}, 余额: ${account.balance_cents/100:.2f}")
        return account

    async def generate_test_api_key(
        self,
        user_id: str,
        name: str = "Test API Key",
        key_type: APIKeyType = APIKeyType.DEVELOPMENT,
        expires_days: int | None = None
    ) -> tuple[APIKey, str]:
        """生成测试API Key"""
        # 生成API Key
        api_key_str, key_hash = self.generate_api_key()
        key_id = api_key_str[:20] + "..."

        # 计算过期时间
        expires_at = None
        if expires_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

        # 创建API Key对象
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_id,
            name=name,
            type=key_type,
            status=APIKeyStatus.ACTIVE,
            monthly_quota=100000,  # 10万Token
            daily_quota=10000,     # 1万Token
            rate_limit_rpm=60,
            rate_limit_tpm=10000,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            updated_at=datetime.now(timezone.utc)
        )

        # 保存到数据库
        key_doc_id = await self.mongo.insert_one("api_keys", api_key.model_dump())
        api_key.id = key_doc_id

        print(f"生成API Key: {name}")
        print(f"Key ID: {key_id}")
        print(f"完整Key: {api_key_str}")
        print(f"配额: 每月{api_key.monthly_quota:,}, 每日{api_key.daily_quota:,}")

        return api_key, api_key_str

    async def list_api_keys(self, user_id: str):
        """列出用户的所有API Key"""
        keys = await self.mongo.find_many(
            "api_keys",
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )

        if not keys:
            print("没有找到API Key")
            return

        print(f"\n用户 {user_id} 的API Key列表:")
        print("-" * 80)
        for key in keys:
            api_key = APIKey(**key)
            status_emoji = "✅" if api_key.status == "active" else "❌"
            print(f"{status_emoji} {api_key.name}")
            print(f"   Key ID: {api_key.key_id}")
            print(f"   类型: {api_key.type}")
            print(f"   状态: {api_key.status}")
            print(f"   已用Token: {api_key.total_tokens_used:,}")
            print(f"   创建时间: {api_key.created_at}")
            if api_key.expires_at:
                print(f"   过期时间: {api_key.expires_at}")
            print()

async def main():
    """主函数"""
    generator = APIKeyGenerator()

    print("🔑 API Key 生成工具")
    print("=" * 50)

    # 创建测试用户
    username = input("请输入用户名 (默认: test_user): ").strip() or "test_user"
    user_id = await generator.create_test_user(username)

    # 创建测试账户
    account = await generator.create_test_account(user_id)

    # 生成API Key
    key_name = input("请输入API Key名称 (默认: Test API Key): ").strip() or "Test API Key"

    # 选择类型
    print("\n选择API Key类型:")
    print("1. Development (开发)")
    print("2. Production (生产)")
    print("3. Enterprise (企业)")

    type_choice = input("请选择 (1-3, 默认: 1): ").strip() or "1"
    key_types = {
        "1": APIKeyType.DEVELOPMENT,
        "2": APIKeyType.PRODUCTION,
        "3": APIKeyType.ENTERPRISE
    }
    key_type = key_types.get(type_choice, APIKeyType.DEVELOPMENT)

    # 设置过期天数
    expires_input = input("过期天数 (默认: 无限期): ").strip()
    expires_days = int(expires_input) if expires_input.isdigit() else None

    print("\n生成中...")
    api_key, api_key_str = await generator.generate_test_api_key(
        user_id=user_id,
        name=key_name,
        key_type=key_type,
        expires_days=expires_days
    )

    print("\n" + "=" * 50)
    print("✅ API Key 生成成功!")
    print("=" * 50)
    print(f"完整API Key: {api_key_str}")
    print(f"Key ID: {api_key.key_id}")
    print(f"用户ID: {user_id}")
    print(f"账户余额: ${account.balance_cents/100:.2f}")
    print(f"免费额度: ${account.credit_cents/100:.2f}")

    # 保存到文件
    with open("tools/generated_api_key.txt", "w") as f:
        f.write(f"API Key: {api_key_str}\n")
        f.write(f"Key ID: {api_key.key_id}\n")
        f.write(f"User ID: {user_id}\n")
        f.write(f"Generated at: {datetime.now()}\n")

    print(f"\nAPI Key 已保存到: tools/generated_api_key.txt")

    # 显示所有API Key
    await generator.list_api_keys(user_id)

if __name__ == "__main__":
    asyncio.run(main())