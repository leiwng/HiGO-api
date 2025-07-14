from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class AccountType(str, Enum):
    TRIAL = "trial"
    DEVELOPER = "developer"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class Account(BaseModel):
    id: str | None = None
    user_id: str
    account_type: AccountType = AccountType.TRIAL

    # 余额管理 (以美分为单位，避免浮点数精度问题)
    balance_cents: int = 0  # 账户余额(美分)
    credit_cents: int = 0   # 赠送额度(美分)

    # 配额限制
    monthly_spending_limit_cents: int | None = None
    daily_spending_limit_cents: int | None = None

    # 统计信息
    total_spent_cents: int = 0
    monthly_spent_cents: int = 0
    daily_spent_cents: int = 0

    # 时间戳
    created_at: datetime
    updated_at: datetime

class UsageRecord(BaseModel):
    id: str | None = None
    api_key_id: str
    user_id: str

    # 请求信息
    endpoint: str
    method: str

    # Token使用量
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # 计费信息
    cost_cents: int = 0  # 本次请求费用(美分)
    model: str | None = None

    # 时间戳
    timestamp: datetime

class BillingRate(BaseModel):
    """计费费率配置"""
    model: str
    prompt_token_price_per_1k: int  # 每1000个prompt token的价格(美分)
    completion_token_price_per_1k: int  # 每1000个completion token的价格(美分)

    @staticmethod
    def get_default_rates() -> dict[str, "BillingRate"]:
        return {
            "gpt-3.5-turbo": BillingRate(
                model="gpt-3.5-turbo",
                prompt_token_price_per_1k=50,  # $0.0005 per 1K tokens
                completion_token_price_per_1k=150  # $0.0015 per 1K tokens
            ),
            "gpt-4": BillingRate(
                model="gpt-4",
                prompt_token_price_per_1k=3000,  # $0.03 per 1K tokens
                completion_token_price_per_1k=6000  # $0.06 per 1K tokens
            ),
            "claude-3-sonnet": BillingRate(
                model="claude-3-sonnet",
                prompt_token_price_per_1k=300,  # $0.003 per 1K tokens
                completion_token_price_per_1k=1500  # $0.015 per 1K tokens
            )
        }