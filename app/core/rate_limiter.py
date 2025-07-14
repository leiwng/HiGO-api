from fastapi import HTTPException, status
from app.services.storage.redis_service import RedisService
from app.core.config import settings
import time

class LoginRateLimiter:
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service
        # 使用配置中的值
        self.max_attempts = settings.LOGIN_MAX_ATTEMPTS
        self.window_seconds = 300  # 5分钟窗口
        self.lockout_seconds = settings.LOGIN_LOCKOUT_MINUTES * 60  # 转换为秒

    async def check_rate_limit(self, identifier: str) -> bool:
        """检查是否超过速率限制"""
        key = f"login_attempts:{identifier}"
        current_time = int(time.time())

        # 获取当前尝试次数
        attempts = await self.redis.get(key)
        if attempts is None:
            attempts = 0
        else:
            attempts = int(attempts)

        if attempts >= self.max_attempts:
            # 检查是否还在锁定期内
            lockout_key = f"login_lockout:{identifier}"
            lockout_time = await self.redis.get(lockout_key)
            if lockout_time and current_time < int(lockout_time):
                return False

        return True

    async def record_failed_attempt(self, identifier: str):
        """记录失败尝试"""
        key = f"login_attempts:{identifier}"
        current_time = int(time.time())

        # 增加尝试次数
        attempts = await self.redis.incr(key)
        await self.redis.expire(key, self.window_seconds)

        # 如果达到最大尝试次数，设置锁定
        if attempts >= self.max_attempts:
            lockout_key = f"login_lockout:{identifier}"
            lockout_until = current_time + self.lockout_seconds
            await self.redis.set(lockout_key, str(lockout_until), ex=self.lockout_seconds)

    async def clear_attempts(self, identifier: str):
        """清除尝试记录（登录成功时调用）"""
        key = f"login_attempts:{identifier}"
        lockout_key = f"login_lockout:{identifier}"
        await self.redis.delete(key)
        await self.redis.delete(lockout_key)

    async def get_lockout_info(self, identifier: str) -> dict:
        """获取锁定信息"""
        lockout_key = f"login_lockout:{identifier}"
        attempts_key = f"login_attempts:{identifier}"

        lockout_time = await self.redis.get(lockout_key)
        attempts = await self.redis.get(attempts_key)

        if lockout_time:
            remaining_time = int(lockout_time) - int(time.time())
            return {
                "is_locked": remaining_time > 0,
                "remaining_seconds": max(0, remaining_time),
                "attempts": int(attempts) if attempts else 0
            }

        return {
            "is_locked": False,
            "remaining_seconds": 0,
            "attempts": int(attempts) if attempts else 0
        }