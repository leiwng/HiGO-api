# /app/models/chat.py
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ImageType(str, Enum):
    EMOTION = "emotion-recognition"
    FECES = "feces-recognition"
    SKIN = "skin-recognition"
    URINE = "urine-recognition"
    VOMITUS = "vomitus-recognition"
    EAR_CANAL = "ear-canal-recognition"


class TextChatRequest(BaseModel):
    user_id: str = Field(..., description="宠物主人ID")
    conversation_id: str = Field(..., description="本轮对话ID")
    pet_id: str = Field(..., description="宠物ID")
    question: str = Field(..., description="用户咨询文本")


class ImageChatRequest(BaseModel):
    user_id: str = Field(..., description="宠物主人ID")
    conversation_id: str = Field(..., description="本轮对话ID")
    pet_id: str = Field(..., description="宠物ID")
    question: str = Field(..., description="用户咨询文本")
    image_type: ImageType = Field(..., description="图片类型，用于确定调用哪个多模态API")
    images: List[str] = Field(..., description="Base64编码的图片数组，最多5张")


class ChatResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None
    detail: Optional[str] = None


class StreamChunk(BaseModel):
    conversation_id: str
    text_chunk: str
    is_final: bool
    timestamp: str
