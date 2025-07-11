import asyncio
import json
import logging
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError
from app.core.config import settings
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class RedisService:
    """Redis异步服务类，提供缓存、会话管理、速率限制等功能"""

    def __init__(self):
        self._pool: ConnectionPool | None = None
        self._redis: Redis | None = None

    async def connect(self):
        """连接到Redis"""
        try:
            # 支持 REDIS_URL 或分离的配置项
            if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
                # 解析 Redis URL
                parsed = urlparse(settings.REDIS_URL)
                host = parsed.hostname or 'localhost'
                port = parsed.port or 6379
                password = parsed.password
                db = int(parsed.path[1:]) if parsed.path and len(parsed.path) > 1 else 0
            else:
                host = settings.REDIS_HOST
                port = settings.REDIS_PORT
                password = settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None
                db = settings.REDIS_DB

            self._pool = ConnectionPool(
                host=host,
                port=port,
                password=password,
                db=db,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            self._redis = Redis(connection_pool=self._pool)

            # 测试连接
            await self._redis.ping()
            logger.info("Redis连接成功")

        except ConnectionError as e:
            logger.error(f"Redis连接失败: {e}")
            raise
        except Exception as e:
            logger.error(f"Redis初始化错误: {e}")
            raise

    async def disconnect(self):
        """断开Redis连接"""
        if self._redis:
            await self._redis.close()
        if self._pool:
            await self._pool.disconnect()
        logger.info("Redis连接已断开")

    async def ping(self) -> bool:
        """检查Redis连接状态"""
        try:
            await self._redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping失败: {e}")
            return False

    # ==================== 基础操作 ====================

    async def get(self, key: str) -> str | None:
        """获取字符串值"""
        try:
            result = await self._redis.get(key)
            return result.decode('utf-8') if result else None
        except RedisError as e:
            logger.error(f"Redis GET错误 {key}: {e}")
            return None

    async def set(self, key: str, value: str, ex: int | None = None,
                  nx: bool = False) -> bool:
        """设置字符串值"""
        try:
            result = await self._redis.set(key, value, ex=ex, nx=nx)
            return result is True
        except RedisError as e:
            logger.error(f"Redis SET错误 {key}: {e}")
            return False

    async def delete(self, *keys: str) -> int:
        """删除键"""
        try:
            return await self._redis.delete(*keys)
        except RedisError as e:
            logger.error(f"Redis DELETE错误 {keys}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return await self._redis.exists(key) > 0
        except RedisError as e:
            logger.error(f"Redis EXISTS错误 {key}: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """设置键过期时间"""
        try:
            return await self._redis.expire(key, seconds)
        except RedisError as e:
            logger.error(f"Redis EXPIRE错误 {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """获取键的剩余生存时间"""
        try:
            return await self._redis.ttl(key)
        except RedisError as e:
            logger.error(f"Redis TTL错误 {key}: {e}")
            return -1

    # ==================== 计数器操作 ====================

    async def incr(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        try:
            return await self._redis.incr(key, amount)
        except RedisError as e:
            logger.error(f"Redis INCR错误 {key}: {e}")
            return 0

    async def decr(self, key: str, amount: int = 1) -> int:
        """递减计数器"""
        try:
            return await self._redis.decr(key, amount)
        except RedisError as e:
            logger.error(f"Redis DECR错误 {key}: {e}")
            return 0

    # ==================== 列表操作 ====================

    async def lpush(self, key: str, *values: str) -> int:
        """从左侧推入列表"""
        try:
            return await self._redis.lpush(key, *values)
        except RedisError as e:
            logger.error(f"Redis LPUSH错误 {key}: {e}")
            return 0

    async def rpush(self, key: str, *values: str) -> int:
        """从右侧推入列表"""
        try:
            return await self._redis.rpush(key, *values)
        except RedisError as e:
            logger.error(f"Redis RPUSH错误 {key}: {e}")
            return 0

    async def lpop(self, key: str) -> str | None:
        """从左侧弹出列表元素"""
        try:
            result = await self._redis.lpop(key)
            return result.decode('utf-8') if result else None
        except RedisError as e:
            logger.error(f"Redis LPOP错误 {key}: {e}")
            return None

    async def rpop(self, key: str) -> str | None:
        """从右侧弹出列表元素"""
        try:
            result = await self._redis.rpop(key)
            return result.decode('utf-8') if result else None
        except RedisError as e:
            logger.error(f"Redis RPOP错误 {key}: {e}")
            return None

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        """获取列表范围内的元素"""
        try:
            result = await self._redis.lrange(key, start, end)
            return [item.decode('utf-8') for item in result]
        except RedisError as e:
            logger.error(f"Redis LRANGE错误 {key}: {e}")
            return []

    async def ltrim(self, key: str, start: int, end: int) -> bool:
        """修剪列表"""
        try:
            await self._redis.ltrim(key, start, end)
            return True
        except RedisError as e:
            logger.error(f"Redis LTRIM错误 {key}: {e}")
            return False

    async def llen(self, key: str) -> int:
        """获取列表长度"""
        try:
            return await self._redis.llen(key)
        except RedisError as e:
            logger.error(f"Redis LLEN错误 {key}: {e}")
            return 0

    # ==================== 集合操作 ====================

    async def sadd(self, key: str, *members: str) -> int:
        """添加集合成员"""
        try:
            return await self._redis.sadd(key, *members)
        except RedisError as e:
            logger.error(f"Redis SADD错误 {key}: {e}")
            return 0

    async def srem(self, key: str, *members: str) -> int:
        """移除集合成员"""
        try:
            return await self._redis.srem(key, *members)
        except RedisError as e:
            logger.error(f"Redis SREM错误 {key}: {e}")
            return 0

    async def sismember(self, key: str, member: str) -> bool:
        """检查是否为集合成员"""
        try:
            return await self._redis.sismember(key, member)
        except RedisError as e:
            logger.error(f"Redis SISMEMBER错误 {key}: {e}")
            return False

    async def smembers(self, key: str) -> set:
        """获取集合所有成员"""
        try:
            result = await self._redis.smembers(key)
            return {item.decode('utf-8') for item in result}
        except RedisError as e:
            logger.error(f"Redis SMEMBERS错误 {key}: {e}")
            return set()

    async def scard(self, key: str) -> int:
        """获取集合成员数量"""
        try:
            return await self._redis.scard(key)
        except RedisError as e:
            logger.error(f"Redis SCARD错误 {key}: {e}")
            return 0

    # ==================== 哈希操作 ====================

    async def hset(self, key: str, field: str, value: str) -> int:
        """设置哈希字段"""
        try:
            return await self._redis.hset(key, field, value)
        except RedisError as e:
            logger.error(f"Redis HSET错误 {key}.{field}: {e}")
            return 0

    async def hget(self, key: str, field: str) -> str | None:
        """获取哈希字段值"""
        try:
            result = await self._redis.hget(key, field)
            return result.decode('utf-8') if result else None
        except RedisError as e:
            logger.error(f"Redis HGET错误 {key}.{field}: {e}")
            return None

    async def hmset(self, key: str, mapping: dict[str, str]) -> bool:
        """设置多个哈希字段"""
        try:
            await self._redis.hmset(key, mapping)
            return True
        except RedisError as e:
            logger.error(f"Redis HMSET错误 {key}: {e}")
            return False

    async def hgetall(self, key: str) -> dict[str, str]:
        """获取哈希所有字段"""
        try:
            result = await self._redis.hgetall(key)
            return {k.decode('utf-8'): v.decode('utf-8') for k, v in result.items()}
        except RedisError as e:
            logger.error(f"Redis HGETALL错误 {key}: {e}")
            return {}

    async def hdel(self, key: str, *fields: str) -> int:
        """删除哈希字段"""
        try:
            return await self._redis.hdel(key, *fields)
        except RedisError as e:
            logger.error(f"Redis HDEL错误 {key}: {e}")
            return 0

    # ==================== JSON操作辅助方法 ====================

    async def get_json(self, key: str) -> dict | None:
        """获取JSON数据"""
        try:
            data = await self.get(key)
            return json.loads(data) if data else None
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误 {key}: {e}")
            return None

    async def set_json(self, key: str, value: dict, ex: int | None = None) -> bool:
        """设置JSON数据"""
        try:
            json_str = json.dumps(value, ensure_ascii=False)
            return await self.set(key, json_str, ex=ex)
        except (TypeError, ValueError) as e:
            logger.error(f"JSON序列化错误 {key}: {e}")
            return False

    # ==================== 分布式锁 ====================

    async def acquire_lock(self, lock_key: str, timeout: int = 30,
                          identifier: str | None = None) -> str | None:
        """获取分布式锁"""
        if not identifier:
            identifier = f"{asyncio.current_task().get_name()}_{id(asyncio.current_task())}"

        try:
            if await self.set(lock_key, identifier, ex=timeout, nx=True):
                return identifier
            return None
        except RedisError as e:
            logger.error(f"获取锁失败 {lock_key}: {e}")
            return None

    async def release_lock(self, lock_key: str, identifier: str) -> bool:
        """释放分布式锁"""
        try:
            # 使用Lua脚本确保原子操作
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            result = await self._redis.eval(lua_script, 1, lock_key, identifier)
            return result == 1
        except RedisError as e:
            logger.error(f"释放锁失败 {lock_key}: {e}")
            return False

    # ==================== 缓存操作 ====================

    async def cache_user_info(self, user_id: str, user_data: dict,
                             expire_seconds: int = 3600) -> bool:
        """缓存用户信息"""
        cache_key = f"user_cache:{user_id}"
        return await self.set_json(cache_key, user_data, ex=expire_seconds)

    async def get_cached_user_info(self, user_id: str) -> dict | None:
        """获取缓存的用户信息"""
        cache_key = f"user_cache:{user_id}"
        return await self.get_json(cache_key)

    async def cache_conversation_history(self, conversation_id: str,
                                       messages: list[dict],
                                       max_messages: int = 100,
                                       expire_seconds: int = 3600) -> bool:
        """缓存对话历史"""
        cache_key = f"chat_history:{conversation_id}"
        try:
            # 将消息序列化并推入列表
            for message in messages:
                message_json = json.dumps(message, ensure_ascii=False)
                await self.lpush(cache_key, message_json)

            # 保持最新的消息数量
            await self.ltrim(cache_key, 0, max_messages - 1)
            await self.expire(cache_key, expire_seconds)
            return True
        except Exception as e:
            logger.error(f"缓存对话历史失败 {conversation_id}: {e}")
            return False

    async def get_cached_conversation_history(self, conversation_id: str,
                                            limit: int = 50) -> list[dict]:
        """获取缓存的对话历史"""
        cache_key = f"chat_history:{conversation_id}"
        try:
            messages_json = await self.lrange(cache_key, 0, limit - 1)
            messages = []
            for msg_json in messages_json:
                try:
                    messages.append(json.loads(msg_json))
                except json.JSONDecodeError:
                    continue
            return messages
        except Exception as e:
            logger.error(f"获取缓存对话历史失败 {conversation_id}: {e}")
            return []

    # ==================== 统计功能 ====================

    async def record_api_call(self, endpoint: str, user_id: str | None = None) -> bool:
        """记录API调用统计"""
        try:
            import datetime
            today = datetime.date.today().strftime("%Y-%m-%d")

            # 全局统计
            global_key = f"api_stats:global:{today}:{endpoint}"
            await self.incr(global_key)
            await self.expire(global_key, 86400 * 7)  # 保留7天

            # 用户统计
            if user_id:
                user_key = f"api_stats:user:{user_id}:{today}:{endpoint}"
                await self.incr(user_key)
                await self.expire(user_key, 86400 * 7)  # 保留7天

            return True
        except Exception as e:
            logger.error(f"记录API调用统计失败: {e}")
            return False

    async def get_api_stats(self, endpoint: str, date: str | None = None) -> dict:
        """获取API调用统计"""
        if not date:
            import datetime
            date = datetime.date.today().strftime("%Y-%m-%d")

        try:
            global_key = f"api_stats:global:{date}:{endpoint}"
            global_count = await self.get(global_key)

            return {
                "endpoint": endpoint,
                "date": date,
                "total_calls": int(global_count) if global_count else 0
            }
        except Exception as e:
            logger.error(f"获取API统计失败: {e}")
            return {"endpoint": endpoint, "date": date, "total_calls": 0}

    # ==================== 在线用户管理 ====================

    async def add_online_user(self, user_id: str, expire_seconds: int = 300) -> bool:
        """添加在线用户"""
        try:
            await self.sadd("online_users", user_id)
            user_activity_key = f"user_activity:{user_id}"
            await self.set(user_activity_key, "active", ex=expire_seconds)
            return True
        except Exception as e:
            logger.error(f"添加在线用户失败 {user_id}: {e}")
            return False

    async def remove_online_user(self, user_id: str) -> bool:
        """移除在线用户"""
        try:
            await self.srem("online_users", user_id)
            await self.delete(f"user_activity:{user_id}")
            return True
        except Exception as e:
            logger.error(f"移除在线用户失败 {user_id}: {e}")
            return False

    async def get_online_users_count(self) -> int:
        """获取在线用户数量"""
        return await self.scard("online_users")

    async def cleanup_offline_users(self) -> int:
        """清理离线用户"""
        try:
            online_users = await self.smembers("online_users")
            offline_users = []

            for user_id in online_users:
                activity_key = f"user_activity:{user_id}"
                if not await self.exists(activity_key):
                    offline_users.append(user_id)

            if offline_users:
                await self.srem("online_users", *offline_users)

            return len(offline_users)
        except Exception as e:
            logger.error(f"清理离线用户失败: {e}")
            return 0

# 全局Redis服务实例
redis_service = RedisService()

# 生命周期管理
async def init_redis():
    """初始化Redis连接"""
    await redis_service.connect()

async def close_redis():
    """关闭Redis连接"""
    await redis_service.disconnect()