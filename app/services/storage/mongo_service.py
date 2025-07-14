# /app/services/storage/mongo_service.py
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class MongoService:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.conversations = self.db["conversations"]
        self.users = self.db["users"]
        logger.info("MongoDB connection established.")

    async def get_conversation_history(self, conversation_id: str, limit: int = 10) -> list[dict]:
        """
        Retrieves the last `limit` messages for a given conversation_id.
        """
        logger.info(f"Fetching history for conversation_id: {conversation_id}")
        cursor = self.conversations.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", -1).limit(limit)

        history = await cursor.to_list(length=limit)
        history.reverse() # To get chronological order

        # Format to match LangChain's expected message format
        formatted_history = [
            {"role": msg["role"], "content": msg["content"]} for msg in history
        ]
        return formatted_history

    async def save_message(self, conversation_id: str, role: str, content: str) -> str | None:
        """保存聊天消息"""
        try:
            message_doc = {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc),
                "metadata": {}
            }
            result = await self.conversations.insert_one(message_doc)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None

    async def find_one(self, collection_name: str, filter_dict: dict) -> dict | None:
        """查找单个文档"""
        try:
            collection = self.db[collection_name]
            result = await collection.find_one(filter_dict)
            return result
        except Exception as e:
            logger.error(f"MongoDB find_one error in {collection_name}: {e}")
            return None

    async def insert_one(self, collection_name: str, document: dict) -> str | None:
        """插入单个文档"""
        try:
            collection = self.db[collection_name]
            result = await collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"MongoDB insert_one error in {collection_name}: {e}")
            return None

    async def find_many(self, collection_name: str, filter_dict: dict, sort: list[tuple] | None = None, limit: int | None = None) -> list[dict]:
        """查找多个文档"""
        try:
            collection = self.db[collection_name]
            cursor = collection.find(filter_dict)

            if sort:
                cursor = cursor.sort(sort)
            if limit:
                cursor = cursor.limit(limit)

            result = await cursor.to_list(length=limit)
            return result
        except Exception as e:
            logger.error(f"MongoDB find_many error in {collection_name}: {e}")
            return []

    async def update_one(self, collection_name: str, filter_dict: dict, update_dict: dict) -> bool:
        """更新单个文档"""
        try:
            collection = self.db[collection_name]
            # 如果update_dict包含MongoDB操作符，直接使用，否则用$set包装
            if any(key.startswith('$') for key in update_dict.keys()):
                result = await collection.update_one(filter_dict, update_dict)
            else:
                result = await collection.update_one(filter_dict, {"$set": update_dict})
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"MongoDB update_one error in {collection_name}: {e}")
            return False

    async def delete_one(self, collection_name: str, filter_dict: dict) -> bool:
        """删除单个文档"""
        try:
            collection = self.db[collection_name]
            result = await collection.delete_one(filter_dict)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"MongoDB delete_one error in {collection_name}: {e}")
            return False

    def get_current_time(self) -> datetime:
        """获取当前时间"""
        return datetime.now(timezone.utc)

    async def close(self):
        """关闭连接"""
        self.client.close()
        logger.info("MongoDB connection closed.")

# 全局MongoDB服务实例
mongo_service = MongoService()

# 依赖注入函数 - 获取MongoDB服务实例
def get_mongo_service() -> MongoService:
    """获取MongoDB服务实例"""
    return mongo_service

# 依赖注入函数 - 获取数据库实例
def get_mongo_db() -> AsyncIOMotorDatabase:
    """获取数据库实例"""
    return mongo_service.db

# 生命周期管理
async def init_mongo():
    """初始化MongoDB连接"""
    # MongoDB连接在实例化时就建立了
    logger.info("MongoDB service initialized")

async def close_mongo():
    """关闭MongoDB连接"""
    await mongo_service.close()
