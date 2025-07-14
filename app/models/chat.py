from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from app.models.pet import PetInfo


class ImageType(str, Enum):
    EMOTION = "emotion-recognition"
    FECES = "feces-recognition"
    SKIN = "skin-recognition"
    URINE = "urine-recognition"
    VOMITUS = "vomitus-recognition"
    EAR_CANAL = "ear_canal"


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
    images: list[str] = Field(..., description="Base64编码的图片数组，最多5张")


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: dict[str, str | int | float] | None = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    conversation_id: str | None = None
    context: dict[str, str | int | float] | None = None


class ChatResponse(BaseModel):
    success: bool
    response: str | None = None
    conversation_id: str | None = None
    error: str | None = None
    metadata: dict[str, str | int | float] | None = None


class StreamChunk(BaseModel):
    conversation_id: str
    text_chunk: str
    is_final: bool
    timestamp: str


class ConversationHistory(BaseModel):
    conversation_id: str
    messages: list[ChatMessage]
    created_at: datetime
    updated_at: datetime


class ImageAnalysisRequest(BaseModel):
    image_base64: str
    image_type: ImageType
    pet_info: PetInfo

    class Config:
        json_schema_extra = {
            "example": {
                "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
                "image_type": "skin",
                "pet_info": {
                    "name": "小白",
                    "species": "dog",
                    "breed": "金毛",
                    "age": 3.5,
                    "gender": "male",
                    "is_neutered": False
                }
            }
        }
