from app.core.logging import get_logger
from datetime import datetime, timedelta, timezone
from app.models.api_key import APIKey, APIKeyCreate, APIKeyStatus
from app.models.account import Account, UsageRecord, BillingRate
from app.services.storage.mongo_service import MongoService
from app.services.storage.redis_service import RedisService
from app.core.api_key_auth import APIKeyAuth

logger = get_logger(__name__)

class APIKeyService:
    def __init__(self):
        self.mongo = MongoService()
        self.redis = RedisService()
        self.api_keys_collection = "api_keys"
        self.accounts_collection = "accounts"
        self.usage_records_collection = "usage_records"

    async def create_api_key(self, user_id: str, key_data: APIKeyCreate) -> tuple[APIKey, str]:
        """创建新的API Key"""
        # 生成API Key
        api_key_str, key_hash = APIKeyAuth.generate_api_key()
        key_id = api_key_str[:20] + "..."  # 显示用的key_id

        # 计算过期时间
        expires_at = None
        if key_data.expires_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=key_data.expires_days)

        # 创建API Key对象
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_id,
            name=key_data.name,
            type=key_data.type,
            status=APIKeyStatus.ACTIVE,
            monthly_quota=key_data.monthly_quota,
            daily_quota=key_data.daily_quota,
            rate_limit_rpm=key_data.rate_limit_rpm,
            rate_limit_tpm=key_data.rate_limit_tpm,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            updated_at=datetime.now(timezone.utc)
        )

        # 保存到数据库
        key_id = await self.mongo.insert_one(self.api_keys_collection, api_key.model_dump())
        api_key.id = key_id

        # 缓存到Redis
        await self.redis.set_json(f"api_key:{key_hash}", api_key.model_dump(), ex=3600)

        return api_key, api_key_str

    async def get_by_hash(self, key_hash: str) -> APIKey | None:
        """根据哈希值获取API Key"""
        # 先从缓存获取
        cached = await self.redis.get_json(f"api_key:{key_hash}")
        if cached:
            return APIKey(**cached)

        # 从数据库获取
        key_doc = await self.mongo.find_one(self.api_keys_collection, {"key_hash": key_hash})
        if not key_doc:
            return None

        api_key = APIKey(**key_doc)

        # 更新缓存
        await self.redis.set_json(f"api_key:{key_hash}", api_key.model_dump(), ex=3600)

        return api_key

    async def update_status(self, api_key_id: str, status: APIKeyStatus):
        """更新API Key状态"""
        await self.mongo.update_one(
            self.api_keys_collection,
            {"_id": api_key_id},
            {"status": status, "updated_at": datetime.now(timezone.utc)}
        )

    async def record_usage(self, api_key: APIKey, usage_data: dict) -> UsageRecord:
        """记录使用量"""
        # 计算费用
        billing_rates = BillingRate.get_default_rates()
        model = usage_data.get("model", "gpt-3.5-turbo")
        rate = billing_rates.get(model, billing_rates["gpt-3.5-turbo"])

        prompt_tokens = usage_data.get("prompt_tokens", 0)
        completion_tokens = usage_data.get("completion_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens

        # 计算费用(美分)
        cost_cents = (
            (prompt_tokens / 1000) * rate.prompt_token_price_per_1k +
            (completion_tokens / 1000) * rate.completion_token_price_per_1k
        )
        cost_cents = int(cost_cents)

        # 创建使用记录
        usage_record = UsageRecord(
            api_key_id=api_key.id,
            user_id=api_key.user_id,
            endpoint=usage_data.get("endpoint", "/chat/completions"),
            method=usage_data.get("method", "POST"),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_cents=cost_cents,
            model=model,
            timestamp=datetime.now(timezone.utc)
        )

        # 保存使用记录
        record_id = await self.mongo.insert_one(
            self.usage_records_collection,
            usage_record.model_dump()
        )
        usage_record.id = record_id

        # 更新API Key使用量
        await self.update_token_usage(api_key.id, total_tokens)

        # 扣费
        await self.charge_account(api_key.user_id, cost_cents)

        return usage_record

    async def update_token_usage(self, api_key_id: str, tokens_used: int):
        """更新Token使用量"""
        update_data = {
            "$inc": {
                "total_tokens_used": tokens_used,
                "monthly_tokens_used": tokens_used,
                "daily_tokens_used": tokens_used
            },
            "$set": {
                "last_used_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        }

        await self.mongo.update_one(
            self.api_keys_collection,
            {"_id": api_key_id},
            update_data
        )

    async def charge_account(self, user_id: str, cost_cents: int):
        """账户扣费"""
        # 优先使用赠送额度，再使用余额
        account = await self.get_account_by_user_id(user_id)
        if not account:
            return

        if account.credit_cents >= cost_cents:
            # 使用赠送额度
            await self.mongo.update_one(
                self.accounts_collection,
                {"user_id": user_id},
                {
                    "$inc": {
                        "credit_cents": -cost_cents,
                        "total_spent_cents": cost_cents,
                        "monthly_spent_cents": cost_cents,
                        "daily_spent_cents": cost_cents
                    },
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )
        else:
            # 使用余额
            remaining_cost = cost_cents - account.credit_cents
            await self.mongo.update_one(
                self.accounts_collection,
                {"user_id": user_id},
                {
                    "$set": {
                        "credit_cents": 0,
                        "updated_at": datetime.now(timezone.utc)
                    },
                    "$inc": {
                        "balance_cents": -remaining_cost,
                        "total_spent_cents": cost_cents,
                        "monthly_spent_cents": cost_cents,
                        "daily_spent_cents": cost_cents
                    }
                }
            )

    async def get_account_by_user_id(self, user_id: str) -> Account | None:
        """获取用户账户信息"""
        account_doc = await self.mongo.find_one(self.accounts_collection, {"user_id": user_id})
        if not account_doc:
            return None
        return Account(**account_doc)

    async def create_account(self, user_id: str, account_type: str = "trial") -> Account:
        """创建用户账户"""
        account = Account(
            user_id=user_id,
            account_type=account_type,
            balance_cents=0,
            credit_cents=500,  # 新用户赠送$5
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        account_id = await self.mongo.insert_one(self.accounts_collection, account.model_dump())
        account.id = account_id

        return account

    async def get_user_api_keys(self, user_id: str) -> list[APIKey]:
        """获取用户的所有API Key"""
        keys_docs = await self.mongo.find_many(
            self.api_keys_collection,
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )

        return [APIKey(**doc) for doc in keys_docs]

    async def revoke_api_key(self, api_key_id: str, user_id: str) -> bool:
        """撤销API Key"""
        result = await self.mongo.update_one(
            self.api_keys_collection,
            {"_id": api_key_id, "user_id": user_id},
            {
                "status": APIKeyStatus.REVOKED,
                "updated_at": datetime.now(timezone.utc)
            }
        )

        if result:
            # 清除缓存
            key_doc = await self.mongo.find_one(self.api_keys_collection, {"_id": api_key_id})
            if key_doc:
                await self.redis.delete(f"api_key:{key_doc['key_hash']}")

        return result