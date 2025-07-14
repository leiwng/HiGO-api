from app.core.logging import get_logger
from app.services.storage.redis_service import RedisService

logger = get_logger(__name__)

class RateLimitService:
    def __init__(self, redis_service: RedisService | None = None):
        self.redis = redis_service or RedisService()

    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        """检查速率限制"""
        try:
            # 使用Redis的滑动窗口算法
            current_count = await self.redis.incr(key)

            if current_count == 1:
                # 第一次访问，设置过期时间
                await self.redis.expire(key, window_seconds)

            return current_count <= limit

        except Exception as e:
            logger.error(f"Rate limit check failed for key {key}: {e}")
            # 出错时允许请求通过
            return True

    async def get_remaining_limit(self, key: str, limit: int) -> int:
        """获取剩余限制次数"""
        try:
            current_count = await self.redis.get(key)
            if current_count is None:
                return limit
            return max(0, limit - int(current_count))
        except Exception as e:
            logger.error(f"Get remaining limit failed for key {key}: {e}")
            return limit

    async def reset_limit(self, key: str) -> bool:
        """重置限制计数"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Reset limit failed for key {key}: {e}")
            return False