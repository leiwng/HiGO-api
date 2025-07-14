import hashlib
import secrets
from datetime import datetime, timezone
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.api_key import APIKey, APIKeyStatus
from app.core.logging import get_logger

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)

class APIKeyAuth:
    def __init__(self):
        # 延迟导入避免循环依赖
        self.api_key_service = None
        self.rate_limit_service = None

    def _get_api_key_service(self):
        """延迟初始化 API Key 服务"""
        if self.api_key_service is None:
            from app.services.api_key_service import APIKeyService
            self.api_key_service = APIKeyService()
        return self.api_key_service

    def _get_rate_limit_service(self):
        """延迟初始化速率限制服务"""
        if self.rate_limit_service is None:
            from app.services.rate_limit_service import RateLimitService
            self.rate_limit_service = RateLimitService()
        return self.rate_limit_service

    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """生成API Key和对应的哈希值"""
        prefix = "sk-higo"
        random_part = secrets.token_urlsafe(32)
        api_key = f"{prefix}-{random_part}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return api_key, key_hash

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """对API Key进行哈希"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    async def verify_api_key(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> APIKey:
        """验证API Key"""
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API key",
                headers={"WWW-Authenticate": "Bearer"}
            )

        api_key = credentials.credentials

        if not api_key.startswith("sk-"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format",
                headers={"WWW-Authenticate": "Bearer"}
            )

        key_hash = self.hash_api_key(api_key)
        api_key_service = self._get_api_key_service()
        api_key_obj = await api_key_service.get_by_hash(key_hash)

        if not api_key_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"}
            )

        if api_key_obj.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"API key is {api_key_obj.status}",
                headers={"WWW-Authenticate": "Bearer"}
            )

        if api_key_obj.expires_at and datetime.now(timezone.utc) > api_key_obj.expires_at:
            await api_key_service.update_status(api_key_obj.id, APIKeyStatus.EXPIRED)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return api_key_obj

# 延迟初始化全局实例
_api_key_auth = None

def get_api_key_auth() -> APIKeyAuth:
    """获取API Key认证实例"""
    global _api_key_auth
    if _api_key_auth is None:
        _api_key_auth = APIKeyAuth()
    return _api_key_auth

# 依赖函数
async def get_current_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> APIKey:
    auth = get_api_key_auth()
    return await auth.verify_api_key(credentials)