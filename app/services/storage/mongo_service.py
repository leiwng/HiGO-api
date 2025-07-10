# /app/services/storage/mongo_service.py
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from loguru import logger
from typing import List, Dict

from app.core.config import Settings, get_settings

class MongoService:
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.client = AsyncIOMotorClient(settings.MONGO_CONNECTION_STRING)
        self.db = self.client[settings.MONGO_DB_NAME]
        self.conversations = self.db["conversations"]
        logger.info("MongoDB connection established.")

    async def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict]:
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

    async def save_message(self, conversation_id: str, role: str, content: str):
        """
        Saves a message to the conversation history.
        """
        from datetime import datetime
        message = {
            "conversation_id": conversation_id,
            "role": role, # "user" or "assistant"
            "content": content,
            "timestamp": datetime.utcnow()
        }
        await self.conversations.insert_one(message)
        logger.info(f"Saved message for conversation_id: {conversation_id}")

    def get_db(self) -> AsyncIOMotorDatabase:
        return self.db

# Dependency to get the database instance
def get_mongo_db(mongo_service: MongoService = Depends()) -> AsyncIOMotorDatabase:
    return mongo_service.get_db()
