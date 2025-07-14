from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"

class APIKeyType(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    ENTERPRISE = "enterprise"

class APIKey(BaseModel):
    id: str
    key_id: str  # API Key的前缀，如 "sk-higo-xxx"
    key_hash: str  # API Key的哈希值
    user_id: str
    name: str  # Key的名称，用户自定义
    type: APIKeyType = APIKeyType.DEVELOPMENT
    status: APIKeyStatus = APIKeyStatus.ACTIVE

    # 配额管理
    monthly_quota: int | None = None  # 每月Token配额
    daily_quota: int | None = None    # 每日Token配额
    rate_limit_rpm: int = 60          # 每分钟请求数限制
    rate_limit_tpm: int = 10000       # 每分钟Token数限制

    # 使用统计
    total_tokens_used: int = 0
    monthly_tokens_used: int = 0
    daily_tokens_used: int = 0
    last_used_at: datetime | None = None

    # 时间戳
    created_at: datetime
    expires_at: datetime | None = None
    updated_at: datetime

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: APIKeyType = APIKeyType.DEVELOPMENT
    monthly_quota: int | None = Field(None, gt=0)
    daily_quota: int | None = Field(None, gt=0)
    rate_limit_rpm: int = Field(60, gt=0, le=1000)
    rate_limit_tpm: int = Field(10000, gt=0, le=100000)
    expires_days: int | None = Field(None, gt=0, le=365)

class APIKeyResponse(BaseModel):
    id: str
    key_id: str
    key: str | None = None  # 只在创建时返回完整key
    name: str
    type: APIKeyType
    status: APIKeyStatus
    monthly_quota: int | None
    daily_quota: int | None
    rate_limit_rpm: int
    rate_limit_tpm: int
    total_tokens_used: int
    monthly_tokens_used: int
    daily_tokens_used: int
    created_at: datetime
    expires_at: datetime | None